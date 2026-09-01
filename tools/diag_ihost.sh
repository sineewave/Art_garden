#!/usr/bin/env bash
# iHost 连不上时先跑这个。不需要密码，不会尝试登录，只探测网络可达性。
#
#   bash tools/diag_ihost.sh
#
# 关键在于区分两种失败——它们的原因完全相反：
#   超时(filtered) = 包被防火墙丢掉  → VPN 没通，或这个端口对校外不开放
#   拒绝(refused)  = 主机收到了包，但那个端口没有服务在听 → 端口号不对
set -u

HOST="${IHOST_HOST:-webhost8.ust.hk}"
USER="${IHOST_USER:-aifhack}"

echo "════ iHost 连通性诊断 ════"
echo "目标主机  $HOST"
echo

# ---------- 1. DNS ----------
IP=$(getent hosts "$HOST" 2>/dev/null | awk '{print $1; exit}')
[[ -z "$IP" ]] && IP=$(dscacheutil -q host -a name "$HOST" 2>/dev/null | awk '/^ip_address/{print $2; exit}')
[[ -z "$IP" ]] && IP=$(python3 -c "import socket,sys;print(socket.gethostbyname(sys.argv[1]))" "$HOST" 2>/dev/null)
if [[ -z "$IP" ]]; then
  echo "✗ DNS 解析不了 $HOST —— 先检查基本网络"; exit 1
fi
echo "① DNS   $HOST → $IP"

# ---------- 2. 端口探测 ----------
# bash 的 /dev/tcp 没有超时参数，macOS 也没有 timeout 命令，所以自己看着表
probe() {
  local h=$1 p=$2 pid rc
  ( exec 3<>"/dev/tcp/$h/$p" ) 2>/dev/null &
  pid=$!
  local i=0
  while kill -0 "$pid" 2>/dev/null && (( i < 60 )); do sleep 0.1; ((i++)); done
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
    return 2                      # 6 秒没结果 = 超时
  fi
  wait "$pid"; rc=$?
  return $(( rc == 0 ? 0 : 1 ))   # 0 通 / 1 被拒绝
}

echo "② 端口"
declare -a OPEN=() FILTERED=()
for entry in "22:SFTP（上传要用的）" "9003:phpMyAdmin（ITSC 给过这个）" "443:HTTPS" "80:HTTP" "21:FTP" "2222:备用 SFTP"; do
  p="${entry%%:*}"; label="${entry#*:}"
  probe "$IP" "$p"; rc=$?
  case $rc in
    0) echo "   $p  ✓ 通         $label"; OPEN+=("$p") ;;
    1) echo "   $p  ✗ 拒绝        $label（主机在，但没服务）" ;;
    2) echo "   $p  ✗ 超时/被丢弃  $label"; FILTERED+=("$p") ;;
  esac
done

# ---------- 3. VPN 是否真的在转发 ----------
echo "③ 路由"
if command -v route >/dev/null 2>&1 && [[ "$(uname)" == "Darwin" ]]; then
  IFACE=$(route -n get "$IP" 2>/dev/null | awk '/interface:/{print $2}')
  echo "   去 $IP 走的网卡：${IFACE:-未知}"
  case "$IFACE" in
    utun*|ppp*|tun*) echo "   ✓ 是隧道网卡，VPN 在接管这条路由" ;;
    "")              echo "   ? 拿不到路由信息" ;;
    *)               echo "   ⚠ 不是隧道网卡 —— 流量没走 VPN，多半 VPN 没连上或是分流模式没覆盖校内网段" ;;
  esac
elif command -v ip >/dev/null 2>&1; then
  ip route get "$IP" 2>/dev/null | head -1 | sed 's/^/   /'
fi
if command -v ifconfig >/dev/null 2>&1; then
  UP=$(ifconfig 2>/dev/null | awk '/^(utun|ppp|tun)/{n=$1} /inet /{if(n){print n" "$2; n=""}}')
  [[ -n "$UP" ]] && { echo "   活动的隧道网卡："; echo "$UP" | sed 's/^/     /'; } \
                 || echo "   ⚠ 没有任何隧道网卡带 IP —— VPN 看起来没连上"
fi

# ---------- 4. 结论 ----------
echo
echo "════ 判断 ════"
in_arr() { local x=$1; shift; for e in "$@"; do [[ "$e" == "$x" ]] && return 0; done; return 1; }
if in_arr 22 "${OPEN[@]:-}"; then
  echo "✓ 22 端口通了，可以上传："
  echo "    bash tools/deploy_ihost.sh"
  echo "  FileZilla 仍连不上的话，把「传输设置」改成「被动模式」，重试次数设为 1。"
elif (( ${#OPEN[@]} == 0 )); then
  echo "✗ 所有端口都不通 —— 这台主机对你现在的网络整体不可达。"
  echo "  基本可以确定 VPN 没有真正连上：打开 Pulse Secure 看状态，"
  echo "  断开重连一次，注意手机上的 2FA 一定要点批准（不批准会停在半连接状态）。"
elif in_arr 9003 "${OPEN[@]:-}"; then
  echo "! 9003 通、22 不通 —— 主机能到，唯独 SFTP 端口到不了。两种可能："
  echo "  a) 你的 IP 被临时封了（反复失败触发 fail2ban）。"
  echo "     关掉 FileZilla 别再重试，等 15–30 分钟再跑一次这个脚本。"
  echo "  b) 你现在的网络（家里/咖啡厅/公司）封了出站 22 端口。"
  echo "     换手机热点试一次，两分钟就能区分开。"
else
  echo "! 部分端口通、22 不通。把上面整段输出发给 ITSC，问两件事："
  echo "  ① SFTP 是不是 22 端口、是不是要另开权限；② 我的 IP 是不是被封了。"
fi
echo
echo "想看握手细节（会问密码，直接 Ctrl-C 也行）："
echo "    ssh -vvv -o ConnectTimeout=10 $USER@$HOST"
