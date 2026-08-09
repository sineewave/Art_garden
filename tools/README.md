# 素材管线 · 三条命令

时间紧的话按这个顺序跑，1000+ 条素材约 1–2 小时（大头是下载）。

```bash
pip install pillow numpy          # build_assets.py 需要
# 视频抽帧另需系统里有 ffmpeg（没有也能跑，视频退化为静帧）

python3 tools/fetch_civitai.py --probe             # ① 先探针：20 秒验证接口
python3 tools/fetch_civitai.py    --target 700     # ② 2026 地层（含互动数据）
python3 tools/fetch_diffusiondb.py --sample 300    # ③ 2022 地层（对照组）
python3 tools/build_assets.py                      # ④ 烘成图集 + 生成 manifest.js
```

> **第一步别跳过。** 本脚本是对着无法访问的官方文档、按已知 v1 结构写的，
> 字段名可能对不上。`--probe` 只取 3 条并打印真实结构（含 `stats` 到底有没有数据），
> 20 秒就能确认。别拿一小时的下载去赌。

跑完刷新 `index.html` 即可。没跑之前页面用内置程序化纹样，一样能演示。

想先验证渲染管线接通了没有（零依赖、两秒）：

```bash
python3 tools/make_test_assets.py         # 生成合成图集
python3 tools/make_test_assets.py --clear # 清掉，回到内置纹样
```

---

## 为什么是这三条命令

### 1. `fetch_civitai.py` — 2026 地层

Civitai 是目前唯一同时具备**现代模型质感 + 完整 prompt/参数 + 真实互动计数**的来源，
且其 ToS 明确禁止爬虫但**允许公开 API**，所以脚本走的是官方 API，不是爬虫。

关键设计是**分层抽样，不是只抓热门**。脚本从五组 `(sort, period)` 拉取：

| 分层 | 作用 |
|---|---|
| Most Reactions / Week、Month、AllTime | 赢家，形成潮流 |
| Most Comments / Month | 有争议但未必好看的 |
| **Newest / Day** | **长尾：刚生成、还没人看过** |

只抓热门会丢掉整个长尾，而"无人问津的对象"恰恰是这件作品的一半论点。

下载时会把 CDN 路径里的 `/width=NNN/` 改写成 `width=512`，下载量降一个数量级——
1000 张约 100MB 而不是 1–2GB。

**跑完注意看最后一行**：脚本会打印 `stats` 字段的实际可用率。社区有 issue 反映
这个字段偶尔返回空。如果可用率低于 50%，说明拿不到真实互动数据，需要改走单图详情
端点或换源——早知道比爬完才发现好。

参数：

```bash
--target 700          # 目标条数
--api-key KEY         # 或设环境变量 CIVITAI_API_KEY，速率上限更高
--width 512           # 下载宽度，越小越快
--video-only          # 单独补视频
```

脚本可重复运行、断点续传（已下载的自动跳过）。

### 2. `fetch_diffusiondb.py` — 2022 地层

2022 年的生成物**丑但多样**，2026 年的**完美但雷同**。两层并置才能算出那条随年代
下降的多样性曲线——那是这个项目最有可能拿出的原创发现。别把老素材当过时素材丢掉，
它是对照组。

DiffusionDB 是 CC0，无需爬取。脚本下载 1 个 part（1000 张 + 参数 JSON，约 300–500MB），
抽样后默认删掉 zip。

```bash
--sample 300   # 抽多少张
--part 7       # 换一个 part
--keep-zip     # 保留 zip
```

### 3. `build_assets.py` — 解决卡顿

这一步是"不卡顿"的**全部答案**。

问题：1000 张图 = 1000 个 HTTP 请求 + 1000 次解码。一张 1024² 的图解码后在内存里是
4MB RGBA，1000 张就是 4GB，浏览器直接跪。

解法：**图集（texture atlas）**。所有图缩到 128×128 密铺进 2048×2048 的大图，
一张装 256 块。1000 张图 → 4 张图集 → **4 个请求、4 次解码、约 64MB**。
运行时 `drawImage(atlas, sx,sy,128,128, dx,dy,w,h)` 直接取块，GPU 友好。

视频同理：ffmpeg 抽 16 帧拼成 4×4 精灵图（一张 512² JPEG），播放 = 换源矩形，
不经过视频解码器，几十个同时"播放"也不掉帧。而且**只有被注视的那一朵才播放**，
其余显示首帧——这个工程约束正好是概念本身：没有被看的内容，本来就不动。

顺带算一个**多样性指标**（16×16 灰度指纹的平均两两距离），按地层分组输出：

```
2022 年 · n=300   多样性 0.5312
2026 年 · n=700   多样性 0.4188
  → 2026 相对 2022 变化 -21.2%（同质化，符合预期）
```

这是趋势用的近似值，投稿前请换 CLIP 嵌入重算。

参数：`--tile 128 --atlas 2048 --max 1600 --quality 84`

---

## 手工素材

自己下载的视频/图片（比如那些疯传的 AI 猫跳舞）直接丢进：

```
data/raw/manual/
```

`build_assets.py` 会自动收进来，标记为 `model: 手工采集 MANUAL`。

---

## 产物

```
data/meta.jsonl          每行一条完整元数据（分析用，保留全文 prompt）
data/raw/…               原始媒体
assets/atlas/a*.jpg      图集
assets/sheet/<id>.jpg    视频精灵图
assets/manifest.js       运行时清单（页面只读这个）
```

`data/` 不进 git（见 .gitignore）；`assets/` 视体积决定是否入库。

---

## 合规备忘

- Civitai：走官方 API、遵守速率限制；`nsfw=None` 已默认过滤，匿名调用还会被平台
  限制在 public browsing level。每条记录都保留 `url` 与 `license` 字段。
- DiffusionDB：CC0，可自由使用。
- 手工素材：自行确认来源可用于展示。
- 展厅若采集观众注视数据：现场告示、端侧处理、不留原始影像、只存聚合量。
