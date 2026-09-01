#!/usr/bin/env bash
# 把作品打包成可以直接丢进 iHost public_html 的一个文件夹。
#
#   bash tools/build_site.sh            # 产出 dist/public_html/
#   bash tools/build_site.sh --zip      # 顺便打个 zip，方便网页版上传
#
# 只拷贝页面真正会请求的文件：index.html + assets/{manifest.js,atlas,sheet,audio}。
# data/ 里的原图、tools/、README 都不上传 —— 服务器只需要成品。
set -euo pipefail

cd "$(dirname "$0")/.."
OUT="dist/public_html"
MAKE_ZIP=0
[[ "${1:-}" == "--zip" ]] && MAKE_ZIP=1

[[ -f index.html ]] || { echo "✗ 找不到 index.html，请在项目根目录运行" >&2; exit 1; }

rm -rf dist
mkdir -p "$OUT/assets"

cp index.html "$OUT/index.html"

if [[ -f assets/manifest.js ]]; then
  cp assets/manifest.js "$OUT/assets/manifest.js"
else
  echo "/* 无素材清单，页面回退到内置程序化纹样 */" > "$OUT/assets/manifest.js"
  echo "window.ATTENTION_GARDEN_ASSETS = null;"    >> "$OUT/assets/manifest.js"
fi

for d in atlas sheet audio; do
  if [[ -d "assets/$d" ]] && [[ -n "$(ls -A "assets/$d" 2>/dev/null)" ]]; then
    cp -r "assets/$d" "$OUT/assets/$d"
    echo "  + assets/$d/  ($(ls "assets/$d" | wc -l | tr -d ' ') 个文件)"
  fi
done

# 可选：开 gzip 和缓存。iHost 若关掉了 AllowOverride，传上去也可能 500，
# 所以默认不叫 .htaccess，你想用再自己改名（见 DEPLOY.md）。
cat > "$OUT/htaccess.optional" <<'HT'
# 改名为 .htaccess 才生效。若网站变成 500，删掉它即可恢复。
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html application/javascript text/css
</IfModule>
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/jpeg "access plus 30 days"
  ExpiresByType audio/mp4  "access plus 30 days"
  ExpiresByType text/html  "access plus 0 seconds"
</IfModule>
HT

# 页面必须自包含：任何 http:// 或外站引用都会在 HTTPS 下被浏览器拦掉
if grep -qE '(src|href)="http://' "$OUT/index.html"; then
  echo "⚠ index.html 里有 http:// 引用，HTTPS 站点上会被拦截，请改成 https:// 或本地文件" >&2
fi

SIZE=$(du -sh "$OUT" | cut -f1)
BYTES=$(du -sk "$OUT" | cut -f1)
echo "✓ 打包完成：$OUT  共 $(find "$OUT" -type f | wc -l | tr -d ' ') 个文件，$SIZE"
(( BYTES > 500000 )) && echo "⚠ 超过 500MB，先问 ITSC 确认 iHost 配额，或用 build_assets.py --max 减素材" || true

if (( MAKE_ZIP )); then
  ( cd dist && zip -qr public_html.zip public_html )
  echo "✓ 压缩包：dist/public_html.zip"
fi

echo
echo "下一步：bash tools/deploy_ihost.sh   （需先连上 HKUST VPN）"
