#!/usr/bin/env bash
# 把 dist/public_html/ 上传到 HKUST iHost。
#
# 前提：① 已连上 HKUST Secure Remote Access (VPN)，或人在校园网/eduroam
#       ② 本机装了 lftp（推荐）或 sftp
#          macOS:  brew install lftp
#          Ubuntu: sudo apt install lftp
#
#   bash tools/deploy_ihost.sh                     # 用默认账号 aifhack
#   IHOST_USER=你的账号 bash tools/deploy_ihost.sh
#   bash tools/deploy_ihost.sh --dry-run           # 只看会传什么，不真传
#
# 密码不写进脚本、不进 git。运行时输入，或设环境变量 IHOST_PASS。
set -euo pipefail

cd "$(dirname "$0")/.."

HOST="${IHOST_HOST:-webhost8.ust.hk}"
USER="${IHOST_USER:-aifhack}"
REMOTE="${IHOST_REMOTE:-public_html}"
LOCAL="dist/public_html"
DRY=0
[[ "${1:-}" == "--dry-run" ]] && DRY=1

[[ -d "$LOCAL" ]] || { echo "✗ 没有 $LOCAL，先跑：bash tools/build_site.sh" >&2; exit 1; }
[[ -f "$LOCAL/index.html" ]] || { echo "✗ $LOCAL 里没有 index.html —— iHost 会显示 Forbidden" >&2; exit 1; }

echo "目标  sftp://$USER@$HOST/$REMOTE"
echo "本地  $LOCAL  ($(du -sh "$LOCAL" | cut -f1))"

# VPN / 校园网是否真的通了 —— 早失败好过传一半断掉
if ! timeout 10 bash -c "exec 3<>/dev/tcp/$HOST/22" 2>/dev/null; then
  echo "✗ 连不上 $HOST:22。请先启动 Pulse Secure 连 HKUST VPN 并完成手机 2FA，再重试。" >&2
  exit 1
fi
echo "✓ $HOST:22 可达"

if [[ -z "${IHOST_PASS:-}" ]]; then
  read -rsp "密码 ($USER)： " IHOST_PASS; echo
fi

if command -v lftp >/dev/null 2>&1; then
  MIRROR="mirror -R --delete --verbose --parallel=4"
  (( DRY )) && MIRROR="mirror -R --delete --dry-run --verbose"
  LFTP_PASSWORD="$IHOST_PASS" lftp -u "$USER",'' --env-password \
    "sftp://$HOST" <<LFTP
set sftp:auto-confirm yes
set net:max-retries 4
set net:reconnect-interval-base 2
mkdir -p $REMOTE
cd $REMOTE
lcd $LOCAL
$MIRROR . .
bye
LFTP
elif command -v sftp >/dev/null 2>&1; then
  (( DRY )) && { echo "sftp 模式不支持 --dry-run，改用 lftp"; exit 1; }
  echo "→ 没装 lftp，改用 sftp（整目录覆盖上传，不会删除服务器上的旧文件）"
  BATCH=$(mktemp)
  { echo "-mkdir $REMOTE"; echo "cd $REMOTE"; echo "put -r $LOCAL/* ."; echo "bye"; } > "$BATCH"
  sftp -b "$BATCH" "$USER@$HOST"
  rm -f "$BATCH"
else
  echo "✗ 本机既没有 lftp 也没有 sftp。装一个：brew install lftp / sudo apt install lftp" >&2
  echo "  或者直接用 FileZilla 把 $LOCAL 里的内容拖进 public_html（见 DEPLOY.md）" >&2
  exit 1
fi

(( DRY )) && { echo "（dry-run，什么都没改）"; exit 0; }
echo
echo "✓ 上传完成，打开看看： https://${USER}.ust.hk/"
