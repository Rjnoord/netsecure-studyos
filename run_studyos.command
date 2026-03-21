#!/bin/zsh
set -e

cd "$(dirname "$0")"

if [ -d "venv" ]; then
  source venv/bin/activate
fi

IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"

echo ""
echo "NetSecure StudyOS starting..."
echo "Mac URL: http://localhost:8501"
if [ -n "$IP" ]; then
  echo "iPhone URL on the same Wi-Fi: http://$IP:8501"
fi
echo ""

streamlit run app.py
