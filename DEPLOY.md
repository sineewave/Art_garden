# 部署到 HKUST iHost

作品是纯静态的：一个 `index.html` 加一批图集文件，**不需要 PHP、不需要数据库**。
ITSC 给的 MySQL（`aifhack_db`）这件作品用不上，可以先放着。

上传只能在**你自己的电脑**上做——iHost 的 SFTP 只对校园网 / VPN 开放。

---

## 一、打包（任何电脑，不用 VPN）

```bash
bash tools/build_site.sh          # 产出 dist/public_html/
bash tools/build_site.sh --zip    # 顺便打个 zip
```

只会拷贝页面真正会请求的文件：

```
dist/public_html/
├── index.html            ← 作品全部逻辑
├── assets/
│   ├── manifest.js       ← 素材清单
│   ├── atlas/            ← 图集（有素材时才有）
│   ├── sheet/            ← 视频精灵图
│   └── audio/            ← 音频
└── htaccess.optional     ← 可选，见下文
```

`data/`、`tools/`、README 都不上传——服务器只需要成品。

## 二、连 VPN

1. 打开 **Pulse Secure**，连 HKUST Remote VPN
2. 输账号密码，手机上批准 2FA

人在校园网或 eduroam 上可以跳过这步。

## 三、上传，二选一

### A. 命令行（推荐，改一次传一次，几秒钟）

```bash
bash tools/deploy_ihost.sh
```

会先探测 `webhost8.ust.hk:22` 通不通（不通就立刻报错，不会传到一半断掉），
然后问密码，把 `dist/public_html/` 镜像到服务器的 `public_html/`。

需要本机有 `lftp`：`brew install lftp`（macOS）/ `sudo apt install lftp`（Ubuntu）。
没有 lftp 会自动退回系统自带的 `sftp`。

换账号：`IHOST_USER=你的账号 bash tools/deploy_ihost.sh`
先看看会传什么：`bash tools/deploy_ihost.sh --dry-run`

> ⚠️ 脚本用的是 `mirror --delete`：**服务器上多出来的文件会被删掉**，
> 保持和本地一致。如果 `public_html` 里还有别人的东西，先用 `--dry-run` 看一眼。

### B. FileZilla（IT 同事说的那个方式）

| 字段 | 填 |
|---|---|
| 主机 | `sftp://webhost8.ust.hk` |
| 用户名 | `aifhack`（你的 ITSC 账号名） |
| 密码 | 你的账号密码 |
| 端口 | `22` |

连上后右边进 `public_html`，把 `dist/public_html/` 里的**内容**
（`index.html` 和 `assets/`，不是外面那层文件夹）拖进去。

## 四、验收

打开 `https://aifhack.ust.hk/`

- 看到花园 → 成功
- **Forbidden** → `public_html` 根目录下没有 `index.html`（多半是连文件夹一起拖进去了，
  变成了 `public_html/public_html/index.html`）
- 图片不显示 → `assets/atlas/` 没传上去，或 `manifest.js` 还是空的
- 页面白屏 → F12 看 Console；本作品无任何外部依赖，报错通常来自缺文件

调试参数照常可用：`https://aifhack.ust.hk/?skip=1&page=garden`

## 五、`htaccess.optional`

想开 gzip 压缩和图片缓存（图集大的时候加载明显快），把它改名成 `.htaccess`。
**如果网站因此变成 500，删掉这个文件就恢复**——说明 iHost 关掉了 `AllowOverride`。
不确定就别传，不影响作品运行。

---

## 换素材后重新部署

```bash
cp 你的图片/* assets/incoming/
python3 tools/build_assets.py     # 烘图集 + 生成 manifest.js
bash tools/build_site.sh
bash tools/deploy_ihost.sh
```

## 关于密码

`tools/deploy_ihost.sh` 不存密码，运行时才问；`dist/` 已加进 `.gitignore`。
ITSC 发的那个初始密码建议尽快在 phpMyAdmin
（<https://webhost8.ust.hk:9003/phpmyadmin/>）里改掉，别写进任何文件、也别提交到仓库。
