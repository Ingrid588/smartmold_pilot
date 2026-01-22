#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p fonts

REG_OUT="fonts/NotoSansSC-Regular.otf"
BOLD_OUT="fonts/NotoSansSC-Bold.otf"

# Note: In some corporate / sandbox environments, outbound network to GitHub/CDNs is blocked.
# If downloads fail, the app will fall back to system fonts (and we suppress fontTools noise in code).

REG_URLS=(
  "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
  "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
  "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
)

BOLD_URLS=(
  "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf"
  "https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf"
  "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf"
)

fetch_any() {
  local out="$1"; shift
  local -a urls=("$@")

  if [[ -f "$out" ]]; then
    echo "[SKIP] $out already exists"
    return 0
  fi

  if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
    echo "[WARN] Need curl or wget; skipping font download" >&2
    return 1
  fi

  for url in "${urls[@]}"; do
    echo "[TRY] $url"
    set +e
    if command -v curl >/dev/null 2>&1; then
      curl -L --fail --max-time 20 --retry 2 --retry-delay 1 -o "$out" "$url"
      rc=$?
    else
      wget -O "$out" "$url"
      rc=$?
    fi
    set -e

    if [[ $rc -eq 0 && -s "$out" ]]; then
      echo "[OK] Wrote $out ($(wc -c <"$out") bytes)"
      return 0
    fi

    rm -f "$out" || true
  done

  echo "[WARN] Failed to download $out (network may be blocked)" >&2
  return 1
}

ok=0
fetch_any "$REG_OUT" "${REG_URLS[@]}" || ok=1
fetch_any "$BOLD_OUT" "${BOLD_URLS[@]}" || ok=1

if [[ $ok -ne 0 ]]; then
  echo "[INFO] Fonts not installed. This is OK: PDF generation will use system fonts." >&2
  echo "[INFO] If you later enable outbound network, re-run: ./scripts/download_fonts.sh" >&2
  exit 0
fi

echo "[DONE] Fonts installed under ./fonts"
