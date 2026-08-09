#!/usr/bin/env python3
"""
把抓来的原始媒体烘成运行时资源 —— 这一步同时解决「不卡顿」和「物种怎么分」。

一、不卡顿 = 图集（texture atlas）
    1000 张图 = 1000 个请求 + 1000 次解码，一张 1024² 解码后是 4MB RGBA，
    1000 张就是 4GB，浏览器直接跪。
    改成：所有图缩到 128×128 密铺进 2048×2048 大图，一张装 256 块。
    1000 张 → 4 张图集 → 4 个请求、4 次解码、约 64MB。
    运行时 drawImage(atlas, sx,sy,128,128, ...) 取块，GPU 友好。
    视频抽 16 帧拼 4×4 精灵图，不经视频解码器；且只有被注视的那朵才播放。

二、物种怎么分 = 聚类（见 cluster_lib.py）
    不聚类的话"同种花"只能按模型名分组，那是同一个模型、不是相关的图，
    而落籽繁衍与同种成潮流全都依赖"同种 = 真的像"。
    这里用 提示词 TF-IDF + 外观指纹 双通道 k-means，默认 k=8 对上八个物种位。
    图集按簇排序密铺，同簇相邻 —— 图集本身就成了一张分类contact sheet。

依赖：pip install pillow numpy    （视频需要系统里有 ffmpeg）

用法：
    python3 tools/build_assets.py
    python3 tools/build_assets.py --k 8 --tile 128 --atlas 2048 --max 1600
"""
import argparse, json, math, os, shutil, subprocess, sys

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow：pip install pillow numpy")
# Pillow 10 把重采样常量搬进了 Image.Resampling，这里两边都兼容
LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
try:
    import numpy as np
except ImportError:
    sys.exit("需要 numpy：pip install numpy")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cluster_lib as CL

META = "data/meta.jsonl"
MANUAL = "data/raw/manual"
ATLAS_DIR = "assets/atlas"
SHEET_DIR = "assets/sheet"
MANIFEST = "assets/manifest.js"
REPORT = "data/cluster_report.txt"
SHEET_COLS, SHEET_ROWS = 4, 4


def load_meta():
    recs = []
    if os.path.exists(META):
        for line in open(META, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    recs.append(json.loads(line))
                except Exception:
                    pass
    if os.path.isdir(MANUAL):
        for fn in sorted(os.listdir(MANUAL)):
            p = os.path.join(MANUAL, fn)
            ext = os.path.splitext(fn)[1].lower()
            if not os.path.isfile(p) or ext not in (
                    ".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm", ".gif"):
                continue
            recs.append({
                "src": "manual", "id": "man_" + os.path.splitext(fn)[0][:20],
                "url": "", "file": p,
                "type": "video" if ext in (".mp4", ".webm", ".gif") else "image",
                "stratum": 2026, "prompt": "", "model": "手工采集 MANUAL",
                "likes": 0, "comments": 0, "license": "user supplied",
            })
    seen, out = set(), []
    for r in recs:
        k = r.get("id")
        if k and k not in seen and os.path.exists(r.get("file", "")):
            seen.add(k)
            out.append(r)
    return out


def center_crop(im, size):
    im = im.convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
    return im.resize((size, size), LANCZOS)


def video_frames(path, n, size):
    if not shutil.which("ffmpeg"):
        return []
    tmp = "data/.frames"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    try:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path,
             "-vf", f"select='not(mod(n\\,3))',scale={size}:{size}:"
                    f"force_original_aspect_ratio=increase,crop={size}:{size}",
             "-vsync", "vfr", "-frames:v", str(n), f"{tmp}/f%03d.jpg"],
            check=True, timeout=120)
        fs = sorted(os.listdir(tmp))
        return [Image.open(os.path.join(tmp, f)).convert("RGB") for f in fs][:n]
    except Exception:
        return []


def signature(im):
    g = im.convert("L").resize((16, 16), LANCZOS)
    v = np.asarray(g, dtype=np.float32).ravel()
    v -= v.mean()
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v


def spatial_color(im, g=4):
    """4×4 网格的平均 RGB —— 同时编码构图与色彩布局，实测最有区分力。"""
    a = np.asarray(im.resize((g, g), LANCZOS), dtype=np.float32).ravel() / 255.0
    return a / max(np.linalg.norm(a), 1e-6)


def hsv_hist(im):
    """HSV 直方图（色相 6 × 饱和 3 × 明度 3）—— 比 RGB 更贴近人的分组直觉。"""
    a = np.asarray(im.convert("HSV").resize((32, 32), LANCZOS), dtype=np.float32) / 255.0
    q = np.clip((a * np.array([6, 3, 3], dtype=np.float32)).astype(np.int32),
                0, np.array([5, 2, 2], dtype=np.int32))
    idx = q[..., 0] * 9 + q[..., 1] * 3 + q[..., 2]
    h = np.bincount(idx.ravel(), minlength=54).astype(np.float32)
    return h / max(h.sum(), 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tile", type=int, default=128)
    ap.add_argument("--atlas", type=int, default=2048)
    ap.add_argument("--max", type=int, default=1600)
    ap.add_argument("--quality", type=int, default=84)
    ap.add_argument("--k", type=int, default=8, help="物种数（对应花园里的八个物种位）")
    ap.add_argument("--w-prompt", type=float, default=0.62,
                    help="提示词通道权重（其余给外观）")
    args = ap.parse_args()

    tile, A = args.tile, args.atlas
    cols = A // tile
    per = cols * cols

    recs = load_meta()[: args.max]
    if not recs:
        sys.exit("data/meta.jsonl 为空 —— 先跑 fetch_civitai.py")
    print(f"素材 {len(recs)} 条\n")
    os.makedirs(ATLAS_DIR, exist_ok=True)
    os.makedirs(SHEET_DIR, exist_ok=True)

    # ---------- 第一遍：缩略图 + 特征 ----------
    print("[1/3] 生成缩略图与特征")
    keep, thumbs, sigs, spats, hsvs, prompts, models = [], [], [], [], [], [], []
    skipped = 0
    for i, r in enumerate(recs):
        try:
            if r["type"] == "video":
                fr = video_frames(r["file"], SHEET_COLS * SHEET_ROWS, tile)
                if fr:
                    sheet = Image.new("RGB", (tile * SHEET_COLS, tile * SHEET_ROWS))
                    for j, f in enumerate(fr):
                        sheet.paste(f, ((j % SHEET_COLS) * tile, (j // SHEET_COLS) * tile))
                    sheet.save(os.path.join(SHEET_DIR, f"{r['id']}.jpg"),
                               quality=args.quality, optimize=True)
                    th, r["_frames"] = fr[0], len(fr)
                else:
                    th, r["_frames"] = center_crop(Image.open(r["file"]), tile), 0
            else:
                th, r["_frames"] = center_crop(Image.open(r["file"]), tile), 0
        except Exception:
            skipped += 1
            continue
        keep.append(r); thumbs.append(th)
        sigs.append(signature(th))
        spats.append(spatial_color(th)); hsvs.append(hsv_hist(th))
        prompts.append(r.get("prompt") or "")
        models.append((r.get("model") or r.get("base_model") or "").strip())
        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(recs)}")

    if not keep:
        sys.exit("没有可用素材")

    # ---------- 第二遍：聚类 ----------
    cov = sum(1 for x in prompts if x.strip()) / max(1, len(prompts))
    P, terms = CL.prompt_matrix(prompts)
    a = args.w_prompt
    if cov < 0.15 or not P.shape[1]:
        # Civitai 的 /images 端点不返回 prompt（实测覆盖率 0%），自动退回纯外观
        a = 0.0
        print(f"\n[2/3] 聚类 k={args.k} —— 提示词覆盖率仅 {cov*100:.0f}%，"
              f"自动改用纯外观通道")
    else:
        print(f"\n[2/3] 聚类 k={args.k}（提示词 {a:.2f} + 外观 {1-a:.2f}，"
              f"提示词覆盖率 {cov*100:.0f}%）")
    V = CL.visual_matrix(sigs, spats, hsvs)
    X = np.hstack([P * a, V * (1 - a)]) if (a > 0 and P.shape[1]) else V
    lab, _ = CL.kmeans(X, args.k)
    labels = CL.label_clusters(lab, P, terms, args.k, models)
    mtab = CL.cluster_model_table(lab, models, args.k)

    order = np.argsort(lab, kind="stable")   # 同簇相邻密铺
    div_all = CL.diversity(X)
    dup = CL.near_dupe_rate(sigs)
    strata = {}
    for r, l in zip(keep, lab):
        strata.setdefault(int(r.get("stratum") or 2026), []).append(l)
    div_by_stratum = {}
    for st in strata:
        idxs = [i for i, r in enumerate(keep) if int(r.get("stratum") or 2026) == st]
        if len(idxs) >= 8:
            div_by_stratum[str(st)] = CL.diversity(X[idxs])

    # ---------- 第三遍：密铺图集 ----------
    print("\n[3/3] 密铺图集")
    atlases, items = [], []
    cur = Image.new("RGB", (A, A), (237, 234, 227))
    ci = slot = 0
    for pos, oi in enumerate(order):
        if slot >= per:
            p = os.path.join(ATLAS_DIR, f"a{ci}.jpg")
            cur.save(p, quality=args.quality, optimize=True)
            atlases.append(p); print(f"    写出 {p}")
            ci += 1; slot = 0
            cur = Image.new("RGB", (A, A), (237, 234, 227))
        r, th = keep[oi], thumbs[oi]
        x, y = slot % cols, slot // cols
        cur.paste(th, (x * tile, y * tile))
        items.append([
            ci, x, y,
            1 if r["type"] == "video" else 0,
            int(r.get("stratum") or 2026),
            int(r.get("likes") or 0), int(r.get("comments") or 0),
            int(r.get("_frames") or 0),
            (r.get("model") or "")[:60],
            (r.get("prompt") or "").replace("\n", " ")[:140],
            r.get("url") or "", r.get("id"),
            int(lab[oi]),
        ])
        slot += 1
    p = os.path.join(ATLAS_DIR, f"a{ci}.jpg")
    cur.save(p, quality=args.quality, optimize=True)
    atlases.append(p); print(f"    写出 {p}")

    sizes = {int(j): int((lab == j).sum()) for j in range(args.k)}
    manifest = {
        "tile": tile, "atlasSize": A, "cols": cols,
        "atlases": atlases, "sheetDir": SHEET_DIR + "/",
        "sheetGrid": [SHEET_COLS, SHEET_ROWS],
        "keys": ["atlas", "x", "y", "isVideo", "stratum", "likes",
                 "comments", "frames", "model", "prompt", "url", "id", "cluster"],
        "items": items,
        "clusters": {str(j): {"n": sizes[j], "label": labels.get(j, "")}
                     for j in range(args.k)},
        "diversity": div_by_stratum, "diversityAll": div_all, "nearDupRate": dup,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write("/* 由 tools/build_assets.py 生成，勿手改 */\n")
        f.write("window.ATTENTION_GARDEN_ASSETS=")
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # ---------- 报告 ----------
    lines = [f"素材 {len(keep)} 条（跳过 {skipped}）  图集 {len(atlases)} 张  k={args.k}", ""]
    lines.append("物种（簇）分布：")
    for j in sorted(sizes, key=lambda x: -sizes[x]):
        bar = "█" * max(1, round(sizes[j] / max(sizes.values()) * 34))
        lines.append(f"  #{j}  n={sizes[j]:<5} {bar}  {labels.get(j,'') or '（无提示词）'}")
    lines.append("")
    lines.append("每簇的主导生成模型（视觉聚类 × 模型族的交叉验证）：")
    for j in sorted(sizes, key=lambda x: -sizes[x]):
        tops = mtab.get(j) or []
        txt = "，".join(f"{n} ×{c}" for n, c in tops) or "—"
        lines.append(f"  #{j}  {txt}")
    lines.append("")
    if div_all is not None:
        lines.append(f"整体多样性（平均两两距离，越低越同质）：{div_all:.4f}")
    for k in sorted(div_by_stratum):
        lines.append(f"  {k} 年地层：{div_by_stratum[k]:.4f}")
    if "2022" in div_by_stratum and "2026" in div_by_stratum:
        d = (div_by_stratum["2026"] - div_by_stratum["2022"]) / div_by_stratum["2022"] * 100
        lines.append(f"  → 2026 相对 2022 {d:+.1f}%"
                     + ("（同质化，符合预期）" if d < 0 else "（未见同质化，检查抽样）"))
    if dup is not None:
        lines.append(f"近重复占比（阈值 .92）：{dup*100:.1f}%  ← 这个数字本身就是一个发现")
    lines.append("")
    lines.append("注：这是 TF-IDF + 灰度/色彩指纹的近似，用于看趋势与驱动花园；")
    lines.append("    投稿前请换 CLIP 嵌入重算多样性与聚类。")
    rep = "\n".join(lines)
    os.makedirs("data", exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write(rep + "\n")

    size = sum(os.path.getsize(a) for a in atlases) / 1e6
    print("\n" + rep)
    print(f"\n图集合计 {size:.1f} MB  清单 {os.path.getsize(MANIFEST)/1e3:.0f} KB")
    print(f"报告已存 {REPORT}")


if __name__ == "__main__":
    main()
