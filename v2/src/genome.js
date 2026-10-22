/* ============================================================
   基因组 GENOME —— 形态的唯一真相来源

   一朵花的形态由两组基因决定，这一刀和作品的论点是同一刀：

     先天 innate   由它那张图本身决定。出生即固定，终生不变。
                   这是"它是什么"——图像的颜色、构图、复杂度。

     后天 acquired 由它在展场里被怎么对待决定。活着的时候一直在变。
                   这是"它经历了什么"——被看了多久、长到第几代。

   繁衍时只有先天基因参与交配与变异；后天基因清零重来。
   所以子代继承的是"长相"，不是"际遇"——每一代都得自己重新被看见。

   本模块不碰任何绘图 API，也不依赖 DOM。
   它的输出喂给 grower.js，再由 2D / 3D / STL 三个渲染器消费。
   ============================================================ */

/* ---------- 基因表 ----------
   每一项都必须写明出处。没有出处的参数不配叫基因，那叫美术调参。
   source 为 null 的项是尚未接通的缺口，如实标着。 */

export const INNATE_GENES = {
  // —— 形态骨架 ——
  symmetry:  { min: 3,    max: 13,   int: true,
               source: 'cluster + hsv.dominantHue', desc: '每轮花瓣数' },
  whorls:    { min: 1,    max: 4,    int: true,
               source: 'log(likes + comments)',     desc: '轮生层数' },
  petalLen:  { min: 0.55, max: 1.15,
               source: 'image.aspect',              desc: '花瓣长度' },
  petalWid:  { min: 0.08, max: 0.40,
               source: 'image.aspect (反向)',        desc: '花瓣宽度' },
  curl:      { min: -0.5, max: 0.75,
               source: 'spatial.verticalCentroid',  desc: '花瓣弯曲' },
  serration: { min: 0,    max: 9,    int: true,
               source: 'gray.highFreqEnergy',       desc: '边缘锯齿数' },
  tipSharp:  { min: 0.5,  max: 3.2,
               source: 'gray.highFreqEnergy',       desc: '尖端锐度' },
  twist:     { min: 0,    max: 1,
               source: 'cluster (稳定哈希)',         desc: '层间旋转' },
  discSize:  { min: 0.05, max: 0.30,
               source: 'spatial.centerEdgeContrast', desc: '花心大小' },

  // —— 颜色 ——
  hue:       { min: 0,    max: 360,
               source: 'hsv.dominantHue',           desc: '主色相' },
  sat:       { min: 0.18, max: 0.95,
               source: 'hsv.meanSaturation',        desc: '饱和度' },
  val:       { min: 0.45, max: 1.00,
               source: 'hsv.meanValue',             desc: '明度' },
  hueSpread: { min: 0,    max: 70,
               source: 'hsv.entropy',               desc: '瓣间色相差' },

  // —— 质感 ——
  weave:     { min: 0,    max: 7,    int: true,
               source: 'nearDupeSimilarity',        desc: '编织密度' },
  pixel:     { min: 0,    max: 5,    int: true,
               source: null,  /* 缺口：需要转载/重复次数，当前管线没统计 */
               desc: '像素化程度' }
};

export const ACQUIRED_GENES = {
  gazeSeconds: { min: 0, max: 120, source: 'runtime.gazeAccum',  desc: '累计被注视秒数' },
  generation:  { min: 0, max: 12,  source: 'runtime.lineage',    desc: '第几代' },
  vigor:       { min: 0, max: 1,   source: 'runtime (派生)',      desc: '长势' }
};

/* ---------- 工具 ---------- */

const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
const lerp = (a, b, t) => a + (b - a) * t;

/** 字符串 → [0,1)。确定性，跨平台一致（不用 Math.random，不用 hashCode） */
export function hash01(str) {
  let h = 2166136261 >>> 0;                   // FNV-1a
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h / 4294967296;
}

/** 把 [0,1) 的归一值按基因表映射成真实取值 */
function decode(spec, t) {
  const v = lerp(spec.min, spec.max, clamp01(t));
  return spec.int ? Math.round(v) : v;
}

/** 真实取值反查回 [0,1)——聚类和育种要用 */
function encode(spec, v) {
  return clamp01((v - spec.min) / (spec.max - spec.min || 1));
}

/* ---------- 从一条素材推出先天基因 ----------

   features 由 build_assets.py 算好写进 manifest：
     hsv      54 维直方图（色相 6 × 饱和 3 × 明度 3）
     spatial  48 维（4×4 网格 × RGB）
     gray     256 维（16×16 灰度，已去均值单位化）

   item 是 manifest.items 里那一条（likes / comments / cluster / id / …）
*/
export function deriveInnate(item, features, stats) {
  const F = features || {};
  const hsv = F.hsv, spatial = F.spatial, gray = F.gray;
  const id = String(item.id || 'unknown');

  // 色相：直方图里最强的那个色相 bin（54 = 6色相 × 3饱和 × 3明度）
  let hueBin = 0, hueMax = -1, satSum = 0, valSum = 0, total = 0, ent = 0;
  if (hsv && hsv.length === 54) {
    const perHue = new Array(6).fill(0);
    for (let h = 0; h < 6; h++)
      for (let s = 0; s < 3; s++)
        for (let v = 0; v < 3; v++) {
          const w = hsv[h * 9 + s * 3 + v];
          perHue[h] += w; total += w;
          satSum += w * (s + 0.5) / 3;
          valSum += w * (v + 0.5) / 3;
        }
    for (let h = 0; h < 6; h++) if (perHue[h] > hueMax) { hueMax = perHue[h]; hueBin = h; }
    for (const w of hsv) if (w > 0) ent -= w * Math.log(w);     // 香农熵 → 杂色程度
    ent /= Math.log(54);                                        // 归一到 [0,1]
  }
  const hueT = total > 0
    ? (hueBin + 0.5) / 6
    : hash01(id + 'hue');                                       // 没特征就退回稳定哈希

  // 灰度高频能量：相邻像素差的均方 → 图像复杂度
  let hf = 0;
  if (gray && gray.length === 256) {
    for (let r = 0; r < 16; r++)
      for (let c = 0; c < 15; c++) {
        const d = gray[r * 16 + c + 1] - gray[r * 16 + c];
        hf += d * d;
      }
    hf = clamp01(Math.sqrt(hf / 240) * 3.2);
  } else hf = hash01(id + 'hf');

  // 空间色块：中心 2×2 与四周的亮度差 → 构图中心性；上下差 → 重心偏移
  let centerEdge = 0.5, vCentroid = 0.5;
  if (spatial && spatial.length === 48) {
    const lum = i => (spatial[i * 3] + spatial[i * 3 + 1] + spatial[i * 3 + 2]) / 3;
    let cen = 0, edge = 0, top = 0, bot = 0;
    for (let r = 0; r < 4; r++)
      for (let c = 0; c < 4; c++) {
        const L = lum(r * 4 + c);
        (r >= 1 && r <= 2 && c >= 1 && c <= 2) ? cen += L / 4 : edge += L / 12;
        r < 2 ? top += L / 8 : bot += L / 8;
      }
    centerEdge = clamp01(0.5 + (cen - edge) * 1.5);
    vCentroid  = clamp01(0.5 + (bot - top) * 1.5);
  }

  // 互动：用百分位而不是原始值 —— 点赞分布是长尾，原始值会把 99% 的花压成一个样
  const pct = (v, arr) => {
    if (!arr || !arr.length) return clamp01(Math.log1p(Math.max(0, v)) / 8);
    let n = 0; for (const x of arr) if (x <= v) n++;
    return n / arr.length;
  };
  const likes = +item.likes || 0, comments = +item.comments || 0;
  const likeT = pct(likes, stats && stats.likes);
  const massT = clamp01(Math.log1p(likes + comments) / Math.log(5000));

  // 长宽比：细长的图 → 细长的花瓣
  const aspect = (item.width && item.height)
    ? clamp01(Math.log(item.width / item.height) / 1.4 + 0.5)
    : hash01(id + 'aspect');      // 缺口：manifest 当前不存 width/height

  const cl = Number.isFinite(item.cluster) ? item.cluster : 0;

  const t = {
    symmetry:  clamp01((cl * 0.137 + hueT * 0.5) % 1),
    whorls:    massT,
    petalLen:  aspect,
    petalWid:  1 - aspect,
    curl:      vCentroid,
    serration: hf,
    tipSharp:  hf,
    twist:     hash01(id + 'twist'),
    discSize:  centerEdge,
    hue:       hueT,
    sat:       total > 0 ? clamp01(satSum / total * 1.3) : hash01(id + 'sat'),
    val:       total > 0 ? clamp01(valSum / total * 1.2) : hash01(id + 'val'),
    hueSpread: ent,
    weave:     clamp01(item.nearDupe != null ? item.nearDupe : hash01(id + 'weave')),
    pixel:     hash01(id + 'pixel')        // 缺口，见基因表
  };

  // openness 不是先天的 —— 它由"被看见"决定，所以归后天。
  // 这是整件作品的规则在基因层面的体现：张开与否，取决于有没有人看。
  const out = { _norm: t, _likeT: likeT };
  for (const k in INNATE_GENES) out[k] = decode(INNATE_GENES[k], t[k]);
  return out;
}

/** 后天基因：活着的时候一直在变 */
export function deriveAcquired(runtime) {
  const R = runtime || {};
  const gaze = Math.max(0, +R.gazeSeconds || 0);
  return {
    gazeSeconds: gaze,
    generation:  Math.max(0, Math.round(+R.generation || 0)),
    vigor:       clamp01(Math.log1p(gaze) / Math.log(60)),
    // 开合角度：被看见才张开。初生 0.3，被持续注视逼近 1.0
    openness:    lerp(0.30, 1.0, clamp01(Math.log1p(gaze) / Math.log(45)))
  };
}

/** 合成一个完整基因组 */
export function makeGenome(item, features, runtime, stats) {
  const innate = deriveInnate(item, features, stats);
  const acquired = deriveAcquired(runtime);
  return { innate, acquired, id: String(item.id || ''), srcCluster: item.cluster };
}

/* ---------- 育种 ----------
   同种成丛、落籽繁衍依赖这里。只有先天基因参与。 */

/** 均匀交叉 + 高斯变异。seed 保证同一对父母 + 同一次落籽结果可复现 */
export function breed(a, b, seed, mutation = 0.06) {
  const t = {};
  let i = 0;
  for (const k in INNATE_GENES) {
    const r1 = hash01(seed + '|x|' + k);
    const r2 = hash01(seed + '|m|' + k);
    const r3 = hash01(seed + '|n|' + k);
    // Box-Muller 取一个正态偏移，让变异集中在小幅度、偶尔出大的
    const g = Math.sqrt(-2 * Math.log(r2 + 1e-9)) * Math.cos(2 * Math.PI * r3);
    const base = r1 < 0.5 ? a.innate._norm[k] : b.innate._norm[k];
    t[k] = clamp01(base + g * mutation);
    i++;
  }
  const innate = { _norm: t, _likeT: (a.innate._likeT + b.innate._likeT) / 2 };
  for (const k in INNATE_GENES) innate[k] = decode(INNATE_GENES[k], t[k]);
  return {
    innate,
    acquired: deriveAcquired({
      generation: Math.max(a.acquired.generation, b.acquired.generation) + 1
    }),
    id: 'f1-' + seed,
    parents: [a.id, b.id]
  };
}

/* ---------- 物种 ----------
   物种不再预设。物种 = 先天基因空间里挨得近的那些花。
   这同时修掉 v1 遗留的「聚类 8 簇 vs 物种 14 种」对不齐问题。 */

/** 先天基因 → 归一向量，供聚类/距离计算 */
export function toVector(genome) {
  const out = [];
  for (const k in INNATE_GENES) out.push(genome.innate._norm[k]);
  return out;
}

/** 两朵花的基因距离 [0,1]。同种成丛、能不能杂交都用它判 */
export function distance(a, b) {
  const va = toVector(a), vb = toVector(b);
  let s = 0;
  for (let i = 0; i < va.length; i++) {
    let d = va[i] - vb[i];
    // 色相是环形的，0° 和 359° 其实挨着
    if (i === Object.keys(INNATE_GENES).indexOf('hue') && Math.abs(d) > 0.5)
      d = Math.sign(d) * (1 - Math.abs(d));
    s += d * d;
  }
  return Math.sqrt(s / va.length);
}

/** 这份基因组的可读性自检 —— 防止极端数据长出一团看不懂的浆糊 */
export function legibility(genome) {
  const G = genome.innate, A = genome.acquired;
  const issues = [];
  if (G.petalWid < 0.10 && G.serration > 7) issues.push('瓣太窄+锯齿太密，边缘会糊');
  if (G.whorls >= 3 && A.openness < 0.45)   issues.push('多层+闭合，内层看不见');
  if (G.discSize > 0.26 && G.petalLen < 0.7) issues.push('花心盖住花瓣');
  if (G.weave >= 6 && G.pixel >= 4)         issues.push('编织+像素双重降质，读不出形态');
  if (G.sat < 0.25 && G.val < 0.55)         issues.push('低饱和+低明度，暗场里看不见');
  return { ok: issues.length === 0, issues };
}
