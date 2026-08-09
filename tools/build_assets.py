#!/usr/bin/env python3
"""
把抓来的原始媒体烘成运行时资源 —— 这一步是「不卡顿」的全部答案。

问题：1000 张图 = 1000 个 HTTP 请求 + 1000 次解码。一张 1024×1024 的图解码后
在内存里是 4MB 的 RGBA，1000 张就是 4GB —— 浏览器直接跪。

解法：**图集（texture atlas）**。
把所有图缩到 128×128 的小块，密铺进 2048×2048 的大图，一张图集装 256 块。
1000 张图 → 4 张图集 → 4 个请求、4 次解码、约 64MB 显存。
运行时用 drawImage(atlas, sx,sy,128,128, dx,dy,w,h) 取块，GPU 友好，零额外开销。

视频同理：抽 16 帧拼成 4×4 精灵图（一张 512×512 的 JPEG），播放 = 换源矩形。
不用视频解码器，几十个同时"播放"也不掉帧。真视频只在被注视时才加载。

依赖：pip install pillow numpy    （视频需要系统里有 ffmpeg）

用法：
    python3 tools/build_assets.py
    python3 tools/build_assets.py --tile 128 --atlas 2048 --max 1200
"""
import argparse, json, math, os, subprocess, sys, shutil

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow：pip install pillow numpy")
try:
    import numpy as np
except ImportError:
    np = None

META = "data/meta.jsonl"
MANUAL = "data/raw/manual"          # 你自己下载的猫跳舞视频丢这里
ATLAS_DIR = "assets/atlas"
SHEET_DIR = "assets/sheet"
MANIFEST = "assets/manifest.js"
SHEET_COLS, SHEET_ROWS = 4, 4       # 每个视频 16 帧


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
    # 手工投放的素材（你自己下的猫视频等）
    if os.path.isdir(MANUAL):
        for fn in sorted(os.listdir(MANUAL)):
            p = os.path.join(MANUAL, fn)
            if not os.path.isfile(p):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm", ".gif"):
                continue
            recs.append({
                "src": "manual", "id": "man_" + os.path.splitext(fn)[0][:20],
                "url": "", "file": p,
                "type": "video" if ext in (".mp4", ".webm", ".gif") else "image",
                "stratum": 2026, "prompt": "", "model": "手工采集 MANUAL",
                "likes": 0, "comments": 0, "license": "user supplied",
            })
    # 去重
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
    return im.resize((size, size), Image.LANCZOS)


def video_frames(path, n, size):
    """用 ffmpeg 均匀抽 n 帧。失败返回 []。"""
    if not shutil.which("ffmpeg"):
        return []
    tmp = "data/.frames"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    try:
        # fps 由时长推算；简单起见直接按帧序均匀取
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path,
             "-vf", f"select='not(mod(n\\,3))',scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size}",
             "-vsync", "vfr", "-frames:v", str(n), f"{tmp}/f%03d.jpg"],
            check=True, timeout=90)
        fs = sorted(os.listdir(tmp))
        return [Image.open(os.path.join(tmp, f)).convert("RGB") for f in fs][:n]
    except Exception:
        return []


def signature(im):
    """16×16 灰度指纹，用于算多样性 —— 不需要 CLIP 也能给出可信的相对趋势。"""
    if np is None:
        return None
    g = im.convert("L").resize((16, 16), Image.LANCZOS)
    v = np.asarray(g, dtype=np.float32).ravel()
    v -= v.mean()
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v


def diversity(sigs, cap=400):
    """平均两两余弦距离。越低 = 越同质。"""
    if np is None or len(sigs) < 8:
        return None
    m = np.stack(sigs[:cap])
    sim = m @ m.T
    iu = np.triu_indices(len(m), k=1)
    return float(1.0 - sim[iu].mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tile", type=int, default=128)
    ap.add_argument("--atlas", type=int, default=2048)
    ap.add_argument("--max", type=int, default=1600)
    ap.add_argument("--quality", type=int, default=84)
    args = ap.parse_args()

    tile, A = args.tile, args.atlas
    cols = A // tile
    per = cols * cols

    recs = load_meta()[: args.max]
    if not recs:
        sys.exit("data/meta.jsonl 为空 —— 先跑 fetch_civitai.py / fetch_diffusiondb.py")
    print(f"素材 {len(recs)} 条 → 每张图集 {cols}×{cols}={per} 块，共 "
          f"{math.ceil(len(recs)/per)} 张图集\n")

    os.makedirs(ATLAS_DIR, exist_ok=True)
    os.makedirs(SHEET_DIR, exist_ok=True)

    atlases, items = [], []
    sigs = {2022: [], 2026: []}
    cur = Image.new("RGB", (A, A), (237, 234, 227))
    ci = 0
    slot = 0
    ok = skipped = 0

    for r in recs:
        path = r["file"]
        thumb = None
        frames = 0
        try:
            if r["type"] == "video":
                fr = video_frames(path, SHEET_COLS * SHEET_ROWS, tile)
                if fr:
                    sheet = Image.new("RGB", (tile * SHEET_COLS, tile * SHEET_ROWS))
                    for i, f in enumerate(fr):
                        sheet.paste(f, ((i % SHEET_COLS) * tile, (i // SHEET_COLS) * tile))
                    sheet.save(os.path.join(SHEET_DIR, f"{r['id']}.jpg"),
                               quality=args.quality, optimize=True)
                    thumb, frames = fr[0], len(fr)
                else:
                    # 没有 ffmpeg：退化成静帧（Pillow 能读 gif 的第一帧）
                    try:
                        thumb = center_crop(Image.open(path), tile)
                    except Exception:
                        skipped += 1
                        continue
            else:
                thumb = center_crop(Image.open(path), tile)
        except Exception:
            skipped += 1
            continue

        if slot >= per:
            p = os.path.join(ATLAS_DIR, f"a{ci}.jpg")
            cur.save(p, quality=args.quality, optimize=True)
            atlases.append(p)
            print(f"  写出 {p}")
            ci += 1
            slot = 0
            cur = Image.new("RGB", (A, A), (237, 234, 227))

        x, y = slot % cols, slot // cols
        cur.paste(thumb, (x * tile, y * tile))

        st = int(r.get("stratum") or 2026)
        s = signature(thumb)
        if s is not None:
            sigs.setdefault(st, []).append(s)

        items.append([
            ci, x, y,
            1 if r["type"] == "video" else 0,
            st,
            int(r.get("likes") or 0),
            int(r.get("comments") or 0),
            frames,
            (r.get("model") or "")[:60],
            (r.get("prompt") or "").replace("\n", " ")[:140],
            r.get("url") or "",
            r.get("id"),
        ])
        slot += 1
        ok += 1
        if ok % 100 == 0:
            print(f"  处理 {ok}/{len(recs)}")

    p = os.path.join(ATLAS_DIR, f"a{ci}.jpg")
    cur.save(p, quality=args.quality, optimize=True)
    atlases.append(p)
    print(f"  写出 {p}")

    div = {str(k): diversity(v) for k, v in sigs.items() if v}
    counts = {str(k): len(v) for k, v in sigs.items() if v}

    manifest = {
        "tile": tile, "atlasSize": A, "cols": cols,
        "atlases": atlases,
        "sheetDir": SHEET_DIR + "/",
        "sheetGrid": [SHEET_COLS, SHEET_ROWS],
        "keys": ["atlas", "x", "y", "isVideo", "stratum", "likes",
                 "comments", "frames", "model", "prompt", "url", "id"],
        "items": items,
        "diversity": div, "strataCount": counts,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write("/* 由 tools/build_assets.py 生成，勿手改 */\n")
        f.write("window.ATTENTION_GARDEN_ASSETS=")
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    size = sum(os.path.getsize(a) for a in atlases) / 1e6
    print(f"\n完成：{ok} 条（跳过 {skipped}）")
    print(f"  图集 {len(atlases)} 张，合计 {size:.1f} MB")
    print(f"  清单 {MANIFEST}（{os.path.getsize(MANIFEST)/1e3:.0f} KB）")
    if div:
        print("\n地层多样性（平均两两距离，越低越同质）：")
        for k in sorted(div):
            print(f"  {k} 年 · n={counts[k]:<5} 多样性 {div[k]:.4f}")
        if "2022" in div and "2026" in div:
            d = (div["2026"] - div["2022"]) / div["2022"] * 100
            print(f"  → 2026 相对 2022 变化 {d:+.1f}%"
                  f"{'（同质化，符合预期）' if d < 0 else '（未见同质化，需检查抽样）'}")
        print("  注：这是 16×16 灰度指纹的近似，用于看趋势；"
              "投稿请换 CLIP 嵌入重算。")


if __name__ == "__main__":
    main()
