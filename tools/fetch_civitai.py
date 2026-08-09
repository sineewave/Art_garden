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


def http_json(url, api_key=None, tries=4):
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
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
            if e.code in (400, 404):
                return None
        except Exception as e:
            print(f"    {type(e).__name__}: {e}", flush=True)
        time.sleep(2 * (i + 1))
    return None


def shrink_url(url, width=512):
    """Civitai 的 CDN 路径里带 /width=NNN/，改小它能把下载量降一个数量级。"""
    if "/width=" in url:
        return re.sub(r"/width=\d+", f"/width={width}", url)
    if "image.civitai.com" in url:
        parts = url.rstrip("/").split("/")
        return "/".join(parts[:-1] + [f"width={width}", parts[-1]])
    return url


def download(url, path, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r, open(path, "wb") as f:
                f.write(r.read())
            return os.path.getsize(path) > 512
        except Exception:
            time.sleep(1.5 * (i + 1))
    if os.path.exists(path):
        os.remove(path)
    return False


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
    data = http_json(url, api_key)
    if not data:
        print("✗ 请求失败。检查网络 / 代理 / 是否需要 API key。")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true",
                    help="只取 3 条并打印真实字段结构 —— 正式开爬前先跑这个")
    ap.add_argument("--target", type=int, default=700, help="目标条数")
    ap.add_argument("--api-key", default=os.environ.get("CIVITAI_API_KEY"))
    ap.add_argument("--width", type=int, default=512, help="下载宽度（越小越快）")
    ap.add_argument("--video-only", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.7, help="每页之间的间隔秒")
    args = ap.parse_args()

    if args.probe:
        probe(args.api_key)
        return

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
                is_video = rec["type"] == "video" or rec["media"].lower().endswith((".mp4", ".webm"))
                if args.video_only and not is_video:
                    continue
                ext = ".mp4" if is_video else ".jpg"
                path = os.path.join(RAW, rec["id"] + ext)
                url = rec["media"] if is_video else shrink_url(rec["media"], args.width)
                if not os.path.exists(path):
                    if not download(url, path):
                        continue
                rec["file"] = path
                rec["type"] = "video" if is_video else "image"
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
    print(f"\n完成：新增 {got} 条 → {META}")
    if got:
        print(f"stats 字段可用率：{stats_ok}/{got} = {stats_ok/got*100:.0f}%")
        if stats_ok / got < 0.5:
            print("  ⚠ 互动数据大面积缺失 —— 这是已知 issue。"
                  "若要靠真实互动驱动花园，需改走单个 image 详情端点或换源。")


if __name__ == "__main__":
    main()
