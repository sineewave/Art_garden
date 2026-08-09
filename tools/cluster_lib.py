#!/usr/bin/env python3
"""
聚类：把抓来的对象分成"物种"。纯 numpy，不引入 torch / sklearn。

为什么必须聚类：没有它，"同种花"只能按生成模型名分组 —— 那是同一个模型，
不是相关的图。而落籽繁衍、同种成潮流这些机制全都依赖"同种 = 真的像"。

双通道特征：
  · 提示词通道（TF-IDF）—— prompt 是人类欲望的直接记录，
    按它分组，"同一种花"的意思就变成"同一种欲望"
  · 外观通道（16×16 灰度指纹 + 粗色彩直方图）—— 保证同种看着也像

两路各自 L2 归一化后加权拼接，再跑 k-means++。
默认 k=8，正好对上花园里的八个物种位。
"""
import math, re
import numpy as np

STOP = set("""a an the of and or with in on at for to from by is are was were be been being
this that these those it its as into over under very highly ultra super best good great
masterpiece bestquality quality detailed detail intricate realistic photorealistic
hyperrealistic render rendering 8k 4k hd uhd resolution sharp focus professional award
winning trending artstation cgsociety unreal engine octane style art artwork illustration
image picture photo shot view background foreground light lighting shadow color colour
""".split())
TOKEN = re.compile(r"[a-z][a-z0-9\-']+")


def prompt_matrix(prompts, vocab_size=600):
    """手写 TF-IDF。空 prompt 会得到零向量，聚类时自然落到"无提示词"那一类。"""
    docs = []
    for p in prompts:
        toks = [t for t in TOKEN.findall((p or "").lower())
                if t not in STOP and len(t) > 2]
        docs.append(toks)
    df = {}
    for toks in docs:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    n = max(1, len(docs))
    # 只留出现次数够多、又不是人人都用的词
    terms = [t for t, c in df.items() if 2 <= c <= n * 0.6]
    terms.sort(key=lambda t: -df[t])
    terms = terms[:vocab_size]
    idx = {t: i for i, t in enumerate(terms)}
    M = np.zeros((n, len(terms)), dtype=np.float32)
    for r, toks in enumerate(docs):
        if not toks:
            continue
        for t in toks:
            j = idx.get(t)
            if j is not None:
                M[r, j] += 1.0
    if len(terms):
        idf = np.log(n / (1.0 + np.array([df[t] for t in terms], dtype=np.float32))) + 1.0
        M *= idf
    nrm = np.linalg.norm(M, axis=1, keepdims=True)
    M /= np.maximum(nrm, 1e-6)
    return M, terms


def visual_matrix(sigs, hists):
    """外观：灰度结构 + 粗色彩，各自归一化后拼接。"""
    S = np.stack(sigs).astype(np.float32) if len(sigs) else np.zeros((0, 256), np.float32)
    H = np.stack(hists).astype(np.float32) if len(hists) else np.zeros((0, 27), np.float32)
    for M in (S, H):
        nrm = np.linalg.norm(M, axis=1, keepdims=True)
        M /= np.maximum(nrm, 1e-6)
    return np.hstack([S, H * 0.8])


def kmeans(X, k, iters=40, seed=20260808):
    """k-means++ 初始化 + Lloyd 迭代。空簇自动重播种。"""
    rng = np.random.default_rng(seed)
    n = len(X)
    k = max(1, min(k, n))
    # k-means++
    centers = [X[rng.integers(n)]]
    d2 = ((X - centers[0]) ** 2).sum(1)
    for _ in range(k - 1):
        p = d2 / max(d2.sum(), 1e-9)
        centers.append(X[rng.choice(n, p=p)])
        d2 = np.minimum(d2, ((X - centers[-1]) ** 2).sum(1))
    C = np.stack(centers)
    lab = np.zeros(n, dtype=np.int32)
    for _ in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(2) if n * k < 400_000 \
            else np.stack([((X - c) ** 2).sum(1) for c in C], axis=1)
        new = d.argmin(1).astype(np.int32)
        if (new == lab).all():
            lab = new
            break
        lab = new
        for j in range(k):
            m = lab == j
            if m.any():
                C[j] = X[m].mean(0)
            else:                       # 空簇：抢一个离自己最远的点
                C[j] = X[d.min(1).argmax()]
    return lab, C


def label_clusters(lab, prompt_M, terms, k):
    """给每一簇取三个最能代表它的词，作为物种的"学名"。"""
    out = {}
    for j in range(k):
        m = lab == j
        if not m.any() or not len(terms):
            out[j] = ""
            continue
        w = prompt_M[m].mean(0)
        top = np.argsort(-w)[:3]
        out[j] = " ".join(terms[t] for t in top if w[t] > 1e-6)
    return out


def diversity(X, cap=500, seed=7):
    """平均两两余弦距离。越低 = 越同质。"""
    if len(X) < 8:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X), size=min(cap, len(X)), replace=False)
    M = X[idx]
    nrm = np.linalg.norm(M, axis=1, keepdims=True)
    M = M / np.maximum(nrm, 1e-6)
    sim = M @ M.T
    iu = np.triu_indices(len(M), k=1)
    return float(1.0 - sim[iu].mean())


def near_dupe_rate(sigs, thresh=0.92, cap=800, seed=7):
    """近重复占比 —— AI 语料里这个数字通常高得惊人，它本身就是一个发现。"""
    if len(sigs) < 8:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(sigs), size=min(cap, len(sigs)), replace=False)
    M = np.stack([sigs[i] for i in idx]).astype(np.float32)
    nrm = np.linalg.norm(M, axis=1, keepdims=True)
    M /= np.maximum(nrm, 1e-6)
    sim = M @ M.T
    np.fill_diagonal(sim, -1)
    return float((sim.max(1) > thresh).mean())
