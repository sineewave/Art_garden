#!/usr/bin/env python3
"""
抓取 Civitai 公开 API 的生成图像 / 视频 —— 「2026 地层」

为什么用它：这是目前唯一同时具备 ①现代模型质感 ②完整 prompt 与生成参数
③真实互动计数 的来源，且其 ToS 明确禁止爬虫但允许公开 API。

关键设计：**分层抽样，不是只抓热门。**
只抓 Most Reactions 会丢掉整个长尾，而"无人问津的对象"恰恰是这件作品的一半论点。
本脚本从多组 (sort, period) 拉取并按互动量分桶，保证冷热都有。

用法：
    python3 tools/fetch_civitai.py --target 700
    python3 tools/fetch_civitai.py --target 700 --api-key YOUR_KEY   # 更高速率上限
    python3 tools/fetch_civitai.py --target 200 --video-only         # 补视频

输出：
    data/raw/civitai/<id>.<ext>     媒体文件（已缩到 width=512，省时间）
    data/meta.jsonl                 每行一条元数据（追加，可重复运行）

注：Civitai 社区有 issue 反映 /api/v1/images 的 stats 字段偶尔返回空。
脚本会在结束时打印实际拿到 stats 的比例，跑一次即可知道真相。
"""
import argparse, json, os, random, re, sys, time
import urllib.request, urllib.parse, urllib.error

API = "https://civitai.com/api/v1/images"
RAW = "data/raw/civitai"
META = "data/meta.jsonl"
UA = "AttentionGarden-ArtProject/1.0 (research; contact via project repo)"

# 分层抽样计划：(sort, period, 想要的条数占比)
# Newest 是关键 —— 那一批几乎没有互动，是"被忽略者"的样本
PLAN = [
    ("Most Reactions", "Week",     0.22),
    ("Most Reactions", "Month",    0.18),
    ("Most Comments",  "Month",    0.12),
    ("Newest",         "Day",      0.28),   # 长尾：刚生成、还没人看
    ("Most Reactions", "AllTime",  0.20),
]


def http_json(url, api_key=None, tries=4, verbose=False):
    for i in range(tries):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/json",
        })
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 8 * (i + 1)
                print(f"    429 限流，等 {wait}s", flush=True)
                time.sleep(wait)
                continue
            print(f"    HTTP {e.code} {url[:90]}", flush=True)
            if verbose or i == 0:
                diagnose_http_error(e)
            if e.code in (400, 401, 403, 404):
                return None
        except Exception as e:
            print(f"    {type(e).__name__}: {e}", flush=True)
            if "refused" in str(e).lower() and i == 0:
                px = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
                if px:
                    print(f"      ⇒ 你设了代理 {px}，但那个端口上没有程序在监听。", flush=True)
                    print(f"        要么启动代理软件、把端口改对，要么直接取消代理：", flush=True)
                    print(f"        unset HTTPS_PROXY HTTP_PROXY", flush=True)
                else:
                    print("      ⇒ 连接被拒绝，检查网络是否可达 civitai.com", flush=True)
                return None
        time.sleep(2 * (i + 1))
    return None


def diagnose_http_error(e):
    """把服务端到底说了什么打出来 —— 区分「站点故障」和「防护层拦截」。"""
    try:
        h = dict(e.headers or {})
    except Exception:
        h = {}
    keys = ["server", "cf-ray", "cf-mitigated", "retry-after",
            "content-type", "x-frame-options", "cf-cache-status"]
    shown = {k: v for k, v in h.items() if k.lower() in keys}
    if shown:
        print("      响应头：", flush=True)
        for k, v in shown.items():
            print(f"        {k}: {str(v)[:90]}", flush=True)
    try:
        body = e.read(1200).decode("utf-8", "replace")
    except Exception:
        body = ""
    if body:
        flat = " ".join(body.split())[:400]
        print(f"      正文片段：{flat}", flush=True)
        low = body.lower()
        if "just a moment" in low or "cf-browser-verification" in low \
                or "challenge-platform" in low or "attention required" in low:
            print("      ⇒ 判定：Cloudflare 人机验证拦截（不是站点故障）", flush=True)
            print("        对策：去 civitai.com 账号设置生成 API Key，用 --api-key 带上；", flush=True)
            print("        仍不行说明对方不希望此类访问，应换数据源，不要绕过验证。", flush=True)
        elif "maintenance" in low or "unavailable" in low or "503" in low:
            print("      ⇒ 判定：站点自身不可用，过一阵重试即可", flush=True)


TRANSFORM_SEG = re.compile(r"^(original|width|height|anim|quality|fit|optimized)=", re.I)


def shrink_url(url, width=512):
    """Civitai CDN 路径里有一段变换参数，可能是 width=N，也可能是 original=true。
    统一替换成 width=<width> —— 不改的话会按原图下载，体积差一个数量级。"""
    if "image.civitai.com" not in url:
        return url
    parts = url.split("/")
    for i, seg in enumerate(parts):
        if TRANSFORM_SEG.match(seg):
            parts[i] = f"width={width}"
            return "/".join(parts)
    # 没有变换段：插在文件名之前
    if len(parts) > 1:
        return "/".join(parts[:-1] + [f"width={width}", parts[-1]])
    return url


def download(url, path, tries=3, max_bytes=None):
    """流式下载；超过 max_bytes 立即中止并放弃这一条（防止个别大视频吃掉带宽）。"""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r, open(path, "wb") as f:
                got = 0
                while True:
                    chunk = r.read(1 << 18)
                    if not chunk:
                        break
                    got += len(chunk)
                    if max_bytes and got > max_bytes:
                        raise ValueError("oversize")
                    f.write(chunk)
            return os.path.getsize(path) > 512
        except ValueError:
            break                      # 超限：不重试，直接跳过
        except Exception:
            time.sleep(1.5 * (i + 1))
    if os.path.exists(path):
        os.remove(path)
    return False


# 只接受明确安全的分级。不依赖服务端 nsfw 参数的语义 —— 客户端再兜一道。
SAFE_LEVELS = {"none", "1", "safe", "pg", ""}


def is_safe(rec):
    lv = str(rec.get("nsfw_level", "")).strip().lower()
    return lv in SAFE_LEVELS


MODEL_CACHE_PATH = "data/model_cache.json"
MODEL_CACHE = {}


def load_model_cache():
    global MODEL_CACHE
    try:
        MODEL_CACHE = json.load(open(MODEL_CACHE_PATH, encoding="utf-8"))
    except Exception:
        MODEL_CACHE = {}


def save_model_cache():
    try:
        os.makedirs(os.path.dirname(MODEL_CACHE_PATH), exist_ok=True)
        json.dump(MODEL_CACHE, open(MODEL_CACHE_PATH, "w", encoding="utf-8"),
                  ensure_ascii=False)
    except Exception:
        pass


def dedupe_doubled(s2):
    """接口偶尔返回 'Krea 2Krea 2' 这种重复串，切回单份。"""
    s2 = (s2 or "").strip()
    h = len(s2) // 2
    if len(s2) > 3 and len(s2) % 2 == 0 and s2[:h] == s2[h:]:
        return s2[:h]
    return s2


def resolve_model_name(rec, api_key, budget):
    """把 modelVersionIds 换成具体模型名（如 Pony Diffusion V6 XL）。
    baseModel 只到家族级（Pony / Illustrious），具体名字信息量大得多。"""
    ids = rec.get("model_version_ids") or []
    if not ids:
        return ""
    key = str(ids[0])
    if key in MODEL_CACHE:
        return MODEL_CACHE[key]
    if budget["left"] <= 0:
        return ""
    budget["left"] -= 1
    mv = http_json(f"https://civitai.com/api/v1/model-versions/{key}", api_key, tries=2)
    name = ""
    if mv:
        name = (mv.get("model") or {}).get("name") or mv.get("name") or ""
    MODEL_CACHE[key] = dedupe_doubled(name)[:120]
    return MODEL_CACHE[key]


def norm(item):
    """把 API 返回压成我们自己的 schema。所有字段都当作可能缺失来处理。"""
    meta = item.get("meta") or {}
    stats = item.get("stats") or {}
    model = meta.get("Model") or meta.get("model") or ""
    if not model:
        for r in (meta.get("resources") or []):
            if r.get("type") == "model" and r.get("name"):
                model = r["name"]
                break
    # meta 为空时的兜底：item 顶层的 baseModel 是真实可用的模型标签
    if not model:
        model = dedupe_doubled(item.get("baseModel") or "")
    likes = sum(int(stats.get(k) or 0) for k in
                ("likeCount", "heartCount", "laughCount", "cryCount"))
    return {
        "src": "civitai",
        "id": str(item.get("id")),
        "url": f"https://civitai.com/images/{item.get('id')}",
        "type": item.get("type") or "image",
        "media": item.get("url") or "",
        "w": item.get("width") or 0,
        "h": item.get("height") or 0,
        "created": item.get("createdAt") or "",
        "stratum": 2026,
        "prompt": (meta.get("prompt") or "")[:600],
        "negative": (meta.get("negativePrompt") or "")[:240],
        "model": model[:120],
        "sampler": meta.get("sampler") or "",
        "steps": meta.get("steps") or meta.get("Steps") or 0,
        "cfg": meta.get("cfgScale") or meta.get("CFG scale") or 0,
        "seed": meta.get("seed") or 0,
        "likes": likes,
        "comments": int(stats.get("commentCount") or 0),
        "base_model": dedupe_doubled(item.get("baseModel") or ""),
        "model_version_ids": item.get("modelVersionIds") or [],
        "post_id": item.get("postId") or 0,
        "username": item.get("username") or "",
        "browsing_level": item.get("browsingLevel", ""),
        "nsfw_level": item.get("nsfwLevel") or item.get("nsfw") or "",
        "license": "Civitai user upload — see source url",
        "has_stats": bool(stats),
        "has_meta": bool(meta),
    }


def probe(api_key):
    """开爬前先验证接口：只取 3 条，打印真实字段结构。

    本脚本是对着无法访问的官方文档、按已知 v1 结构写的。跑这个 20 秒，
    就能确认字段名对不对、stats 到底有没有数据 —— 别拿一小时的下载去赌。
    """
    url = f"{API}?{urllib.parse.urlencode({'limit':3,'sort':'Most Reactions','period':'Week','nsfw':'None'})}"
    print(f"请求 {url}\n")
    data = http_json(url, api_key, tries=2, verbose=True)
    if not data:
        print("\n✗ 请求失败 —— 把上面的响应头与正文片段发我，即可定位原因。")
        return
    print(f"顶层键：{list(data.keys())}")
    md = data.get("metadata") or {}
    print(f"metadata：{md}\n")
    items = data.get("items") or []
    if not items:
        print("✗ items 为空 —— 参数可能不被接受，试试去掉 nsfw 或换 sort 值。")
        return
    it = items[0]
    print(f"单条 item 的键：{sorted(it.keys())}\n")
    for k in ("id", "url", "type", "width", "height", "nsfwLevel", "createdAt", "username"):
        v = it.get(k)
        print(f"  {k:12} = {str(v)[:88]}{'  ← 缺失!' if v is None else ''}")
    st, me = it.get("stats"), it.get("meta")
    print(f"\n  stats  = {json.dumps(st, ensure_ascii=False)[:200] if st else '空 / 缺失  ← 关键问题'}")
    if me:
        print(f"  meta 的键 = {sorted(me.keys())[:14]}")
        for k in ("prompt", "Model", "steps", "sampler", "cfgScale"):
            print(f"    meta.{k:10} = {str(me.get(k))[:70]}")
    else:
        print("  meta   = 空 / 缺失  ← 拿不到 prompt 与参数")

    n_st = sum(1 for x in items if x.get("stats"))
    n_me = sum(1 for x in items if x.get("meta"))
    print(f"\n3 条样本中：有 stats 的 {n_st} 条，有 meta 的 {n_me} 条")
    print("\n归一化后的记录（本脚本实际会存的东西）：")
    print(json.dumps(norm(it), ensure_ascii=False, indent=2)[:900])
    print("\n把以上输出发我，字段对不上我立刻改。没问题就直接开跑正式抓取。")


def probe_meta(api_key):
    """专门追查生成参数：meta 是普遍缺失，还是只是这几条恰好隐藏？
    并测试 API Key 能否解锁、以及模型名有没有别的取法。"""
    print("=" * 60)
    print("A. 大样本统计 meta 覆盖率（100 条，跨三种排序）")
    print("=" * 60)
    total = with_meta = with_prompt = with_stats = with_base = 0
    seen_base = {}
    for sort, period in [("Most Reactions", "Week"), ("Newest", "Day"),
                         ("Most Reactions", "AllTime")]:
        q = {"limit": 100, "sort": sort, "period": period, "nsfw": "None"}
        d = http_json(f"{API}?{urllib.parse.urlencode(q)}", api_key)
        if not d:
            continue
        items = d.get("items") or []
        n = m = pr = st = bm = 0
        for it in items:
            n += 1
            me = it.get("meta") or {}
            if me:
                m += 1
            if me.get("prompt"):
                pr += 1
            if it.get("stats"):
                st += 1
            b = it.get("baseModel")
            if b:
                bm += 1
                seen_base[b] = seen_base.get(b, 0) + 1
        total += n; with_meta += m; with_prompt += pr; with_stats += st; with_base += bm
        print(f"  {sort:>15} / {period:<8}  n={n:<4} meta {m:<4} prompt {pr:<4} "
              f"stats {st:<4} baseModel {bm}")
    if total:
        print(f"\n  合计 n={total}：meta {with_meta/total*100:.0f}%  "
              f"prompt {with_prompt/total*100:.0f}%  "
              f"stats {with_stats/total*100:.0f}%  baseModel {with_base/total*100:.0f}%")
    if seen_base:
        print(f"\n  baseModel 取值分布（可直接当物种维度用）：")
        for k, v in sorted(seen_base.items(), key=lambda x: -x[1])[:12]:
            print(f"    {k:<28} {v}")

    print("\n" + "=" * 60)
    print("B. 单图详情端点是否存在、是否带 meta")
    print("=" * 60)
    d = http_json(f"{API}?limit=1", api_key)
    iid = (d.get("items") or [{}])[0].get("id") if d else None
    if iid:
        one = http_json(f"{API}/{iid}", api_key)
        if one:
            keys = sorted(one.keys()) if isinstance(one, dict) else "非对象"
            print(f"  GET /images/{iid} → 键 {keys}")
            mm = (one or {}).get("meta") or {}
            print(f"  meta：{'有，键=' + str(sorted(mm.keys())[:10]) if mm else '空'}")
        else:
            print(f"  GET /images/{iid} → 不可用（该端点可能不存在）")

    print("\n" + "=" * 60)
    print("C. modelVersionIds 能否换出真实模型名")
    print("=" * 60)
    ids = []
    if d:
        for it in (d.get("items") or []):
            ids += (it.get("modelVersionIds") or [])
    if not ids:
        d2 = http_json(f"{API}?limit=20", api_key)
        for it in ((d2 or {}).get("items") or []):
            ids += (it.get("modelVersionIds") or [])
    if ids:
        mv = http_json(f"https://civitai.com/api/v1/model-versions/{ids[0]}", api_key)
        if mv:
            name = (mv.get("model") or {}).get("name") or mv.get("name")
            print(f"  model-version {ids[0]} → 模型名：{name}")
            print(f"  ⇒ 可用：抓取时按 modelVersionIds 批量换名并缓存")
        else:
            print(f"  model-version {ids[0]} → 不可用")
    else:
        print("  样本里没有 modelVersionIds")

    print("\n" + "=" * 60)
    print("结论建议")
    print("=" * 60)
    if total and with_prompt / total > 0.3:
        print("  prompt 覆盖率尚可 —— 按原方案走，聚类用「提示词+外观」双通道。")
    elif with_base and total and with_base / total > 0.6:
        print("  prompt 大面积缺失，但 baseModel 覆盖良好。")
        print("  ⇒ 聚类改为纯外观通道（--w-prompt 0），物种维度用 baseModel 做交叉验证。")
        print("  ⇒ 档案卡把「提示词」换成「基础模型 + 平台互动」，仍然全是真实字段。")
    else:
        print("  元数据普遍缺失 —— 考虑换源（DiffusionDB 有完整 prompt）。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true",
                    help="只取 3 条并打印真实字段结构 —— 正式开爬前先跑这个")
    ap.add_argument("--probe-meta", action="store_true",
                    help="追查生成参数：meta 覆盖率、单图端点、模型名换取")
    ap.add_argument("--target", type=int, default=700, help="目标条数")
    ap.add_argument("--api-key", default=os.environ.get("CIVITAI_API_KEY"))
    ap.add_argument("--width", type=int, default=512, help="下载宽度（越小越快）")
    ap.add_argument("--video-only", action="store_true")
    ap.add_argument("--max-video-mb", type=float, default=8.0,
                    help="单个视频体积上限，超过直接跳过")
    ap.add_argument("--sleep", type=float, default=0.7, help="每页之间的间隔秒")
    ap.add_argument("--no-resolve-models", action="store_true",
                    help="不去换取具体模型名（只用 baseModel 家族名）")
    ap.add_argument("--model-lookups", type=int, default=400,
                    help="换取模型名的最大请求数（结果会缓存复用）")
    args = ap.parse_args()

    if args.probe:
        probe(args.api_key)
        return
    if args.probe_meta:
        probe_meta(args.api_key)
        return

    load_model_cache()
    mbudget = {"left": args.model_lookups}

    os.makedirs(RAW, exist_ok=True)
    os.makedirs(os.path.dirname(META), exist_ok=True)

    seen = set()
    if os.path.exists(META):
        for line in open(META, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("src") == "civitai":
                    seen.add(d["id"])
            except Exception:
                pass
    print(f"已有 {len(seen)} 条 civitai 记录，继续追加\n")

    out = open(META, "a", encoding="utf-8")
    got = 0
    stats_ok = 0
    nsfw_skipped = 0
    big_skipped = 0
    plan = [(s, p, max(1, int(args.target * w))) for s, p, w in PLAN]
    if args.video_only:
        plan = [("Most Reactions", "Month", args.target),
                ("Newest", "Week", args.target)]

    for sort, period, want in plan:
        if got >= args.target:
            break
        print(f"── {sort} / {period}  目标 {want} 条")
        cursor, page, taken = None, 0, 0
        while taken < want and got < args.target and page < 40:
            q = {"limit": 100, "sort": sort, "period": period, "nsfw": "None"}
            if cursor:
                q["cursor"] = cursor
            data = http_json(f"{API}?{urllib.parse.urlencode(q)}", args.api_key)
            if not data or not data.get("items"):
                break
            page += 1
            for it in data["items"]:
                if got >= args.target or taken >= want:
                    break
                rec = norm(it)
                if rec["id"] in seen or not rec["media"]:
                    continue
                if not is_safe(rec):
                    nsfw_skipped += 1
                    continue
                is_video = rec["type"] == "video" or rec["media"].lower().endswith((".mp4", ".webm"))
                if args.video_only and not is_video:
                    continue
                ext = ".mp4" if is_video else ".jpg"
                path = os.path.join(RAW, rec["id"] + ext)
                url = rec["media"] if is_video else shrink_url(rec["media"], args.width)
                cap = args.max_video_mb * (1 << 20) if is_video else 4 * (1 << 20)
                if not os.path.exists(path):
                    if not download(url, path, max_bytes=cap):
                        big_skipped += 1
                        continue
                rec["file"] = path
                rec["type"] = "video" if is_video else "image"
                if not args.no_resolve_models:
                    mn = resolve_model_name(rec, args.api_key, mbudget)
                    if mn:
                        rec["model"] = mn
                seen.add(rec["id"])
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                got += 1
                taken += 1
                if rec["has_stats"]:
                    stats_ok += 1
                if got % 25 == 0:
                    print(f"    {got}/{args.target}  最新: {rec['model'][:28]}  "
                          f"♥{rec['likes']}", flush=True)
            cursor = (data.get("metadata") or {}).get("nextCursor")
            if not cursor:
                break
            time.sleep(args.sleep)

    out.close()
    save_model_cache()
    print(f"\n完成：新增 {got} 条 → {META}")
    print(f"  跳过：分级不安全 {nsfw_skipped} 条，体积超限 {big_skipped} 条")
    if got:
        print(f"stats 字段可用率：{stats_ok}/{got} = {stats_ok/got*100:.0f}%")
        if stats_ok / got < 0.5:
            print("  ⚠ 互动数据大面积缺失 —— 这是已知 issue。"
                  "若要靠真实互动驱动花园，需改走单个 image 详情端点或换源。")


if __name__ == "__main__":
    main()
