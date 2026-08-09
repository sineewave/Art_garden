#!/usr/bin/env python3
"""
抓取 DiffusionDB 的一个切片 —— 「2022 地层」

为什么需要它：2022 年的生成物**丑但多样**，2026 年的**完美但雷同**。
把两层并置，才能算出那条随年代下降的多样性曲线 —— 那是这件作品最有可能
拿出的原创发现。别把老素材当过时素材丢掉，它是对照组。

DiffusionDB 2M 结构：2000 个 part，每 part 1000 张 512×512 PNG + 一个同名 JSON
（JSON 是 {文件名: [prompt, seed, step, cfg, sampler, width, height, ...]} 的映射）。
本脚本只下 1 个 part（约 300–500MB），并从中抽样 N 张，够用了。

用法：
    python3 tools/fetch_diffusiondb.py --sample 300
    python3 tools/fetch_diffusiondb.py --sample 300 --part 7   # 换一个 part

输出：追加到 data/meta.jsonl，媒体落在 data/raw/diffusiondb/
"""
import argparse, json, io, os, random, sys, time, zipfile
import urllib.request, urllib.error

BASE = "https://huggingface.co/datasets/poloclub/diffusiondb/resolve/main/images"
RAW = "data/raw/diffusiondb"
META = "data/meta.jsonl"
UA = "AttentionGarden-ArtProject/1.0"


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(path, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done / total * 100
                    sys.stdout.write(f"\r  下载 {done/1e6:.0f}/{total/1e6:.0f} MB  {pct:.0f}%")
                else:
                    sys.stdout.write(f"\r  下载 {done/1e6:.0f} MB")
                sys.stdout.flush()
    print()


def parse_params(v):
    """part JSON 的值可能是 list 也可能是 dict，两种都兜住。"""
    if isinstance(v, dict):
        return (v.get("p", "") or v.get("prompt", ""), v.get("se", 0), v.get("st", 0),
                v.get("c", 0), v.get("sa", ""))
    if isinstance(v, (list, tuple)):
        g = lambda i: v[i] if len(v) > i else 0
        return (g(0) or "", g(1), g(2), g(3), g(4))
    return ("", 0, 0, 0, "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--part", type=int, default=1, help="part 编号 1..2000")
    ap.add_argument("--keep-zip", action="store_true", help="保留 zip（默认抽完就删）")
    args = ap.parse_args()

    os.makedirs(RAW, exist_ok=True)
    name = f"part-{args.part:06d}.zip"
    zpath = os.path.join("data", name)

    if not os.path.exists(zpath):
        print(f"下载 {name} …（一个 part = 1000 张，约 300–500MB）")
        try:
            download(f"{BASE}/{name}", zpath)
        except urllib.error.HTTPError as e:
            print(f"\n下载失败 HTTP {e.code}。")
            print("备选：pip install datasets 后用官方子集，体积小很多：")
            print('  from datasets import load_dataset')
            print('  ds = load_dataset("poloclub/diffusiondb", "2m_random_1k")')
            sys.exit(1)
    else:
        print(f"已存在 {zpath}，直接抽样")

    seen = set()
    if os.path.exists(META):
        for line in open(META, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("src") == "diffusiondb":
                    seen.add(d["id"])
            except Exception:
                pass

    out = open(META, "a", encoding="utf-8")
    n = 0
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        jname = next((x for x in names if x.endswith(".json")), None)
        params = json.loads(z.read(jname).decode("utf-8")) if jname else {}
        imgs = [x for x in names if x.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        random.seed(20260808)
        random.shuffle(imgs)
        for fn in imgs:
            if n >= args.sample:
                break
            key = os.path.basename(fn)
            iid = "ddb_" + os.path.splitext(key)[0][:16]
            if iid in seen:
                continue
            prompt, seed, step, cfg, sampler = parse_params(params.get(key, {}))
            dst = os.path.join(RAW, key)
            if not os.path.exists(dst):
                with open(dst, "wb") as f:
                    f.write(z.read(fn))
            out.write(json.dumps({
                "src": "diffusiondb", "id": iid,
                "url": "https://poloclub.github.io/diffusiondb/",
                "type": "image", "file": dst, "w": 512, "h": 512,
                "created": "2022", "stratum": 2022,
                "prompt": str(prompt)[:600], "negative": "",
                "model": "Stable Diffusion 1.x",
                "sampler": str(sampler), "steps": step, "cfg": cfg, "seed": seed,
                "likes": 0, "comments": 0,          # 该数据集没有互动数据 —— 这本身就是重点
                "nsfw_level": "", "license": "CC0 1.0",
                "has_stats": False, "has_meta": bool(prompt),
            }, ensure_ascii=False) + "\n")
            n += 1
            if n % 50 == 0:
                print(f"  抽取 {n}/{args.sample}")
    out.close()

    if not args.keep_zip and os.path.exists(zpath):
        os.remove(zpath)
        print("已删除 zip（--keep-zip 可保留）")
    print(f"\n完成：新增 {n} 条 2022 地层 → {META}")


if __name__ == "__main__":
    main()
