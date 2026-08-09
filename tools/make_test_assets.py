#!/usr/bin/env python3
"""
生成合成图集，用来在真正开爬之前先验证渲染管线 —— 零依赖，两秒跑完。

跑完刷新页面，花心和信息流对象就会换成图集里的测试图块，
档案卡也会显示"生成模型 / 提示词 / 地层 / 平台互动"这些真实字段的位置。
确认无误后再去爬真数据，避免爬完才发现哪里没接上。

    python3 tools/make_test_assets.py      # 生成
    python3 tools/make_test_assets.py --clear   # 清掉，回到内置纹样
"""
import argparse, json, os, random, struct, zlib

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE, A = 64, 512
COLS = A // TILE
PER = COLS * COLS
PALS = [(194,100,63),(110,147,174),(126,148,99),(94,154,146),
        (142,123,166),(196,132,154),(201,151,63),(107,107,96)]
MODELS = ["SDXL 1.0","Flux.2 dev","Kling 2.5","Illustrious XL","SD 1.5"]
PROMPTS = ["a cat dancing on a rooftop, cinematic",
           "portrait of a woman, 8k, hyperrealistic",
           "ancient forest, volumetric light",
           "cyberpunk street food stall at night",
           "ceramic still life, soft daylight"]


def png(path, w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    def ck(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    hdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + ck(b"IHDR", hdr)
                + ck(b"IDAT", zlib.compress(raw, 6)) + ck(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--atlases", type=int, default=2)
    args = ap.parse_args()

    mpath = os.path.join(OUT, "assets", "manifest.js")
    if args.clear:
        with open(mpath, "w", encoding="utf-8") as f:
            f.write("/* 未生成真实素材，页面回退到内置程序化纹样 */\n"
                    "window.ATTENTION_GARDEN_ASSETS = null;\n")
        print("已清空 → 回到内置纹样")
        return

    random.seed(7)
    os.makedirs(os.path.join(OUT, "assets", "atlas"), exist_ok=True)
    items, atlases = [], []
    for ai in range(args.atlases):
        buf = [bytearray(b"\xed\xea\xe3" * A) for _ in range(A)]
        for s in range(PER):
            tx, ty = s % COLS, s // COLS
            idx = ai * PER + s
            c = PALS[idx % len(PALS)]
            c2 = tuple(min(255, int(v * 1.45 + 40)) for v in c)
            kind = idx % 3
            for y in range(TILE):
                row = buf[ty * TILE + y]
                for x in range(TILE):
                    if kind == 0:   on = ((x + y) // 8) % 2 == 0
                    elif kind == 1: on = (x - TILE//2)**2 + (y - TILE//2)**2 < (TILE*0.32)**2
                    else:           on = (x//8 + y//8) % 2 == 0
                    p = (tx * TILE + x) * 3
                    row[p:p+3] = bytes(c if on else c2)
            items.append([ai, tx, ty,
                          1 if idx % 17 == 0 else 0,
                          2022 if idx % 3 == 0 else 2026,
                          random.choice([0, 0, 1, 3, 12, 58, 240, 1900]),
                          random.randint(0, 40),
                          16 if idx % 17 == 0 else 0,
                          MODELS[idx % len(MODELS)],
                          PROMPTS[idx % len(PROMPTS)],
                          f"https://civitai.com/images/{1000+idx}",
                          f"test_{idx:03d}"])
        rel = f"assets/atlas/test_a{ai}.png"
        png(os.path.join(OUT, rel), A, A, buf)
        atlases.append(rel)

    man = {"tile": TILE, "atlasSize": A, "cols": COLS, "atlases": atlases,
           "sheetDir": "assets/sheet/", "sheetGrid": [4, 4],
           "keys": ["atlas","x","y","isVideo","stratum","likes","comments",
                    "frames","model","prompt","url","id"],
           "items": items,
           "diversity": {"2022": 0.5312, "2026": 0.4188},
           "strataCount": {"2022": len(items)//3, "2026": len(items)-len(items)//3}}
    with open(mpath, "w", encoding="utf-8") as f:
        f.write("/* 合成测试素材 —— tools/build_assets.py 会覆盖本文件 */\n")
        f.write("window.ATTENTION_GARDEN_ASSETS=")
        json.dump(man, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"生成 {len(items)} 条测试素材 / {len(atlases)} 张图集 → 刷新页面查看")


if __name__ == "__main__":
    main()
