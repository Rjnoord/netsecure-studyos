#!/usr/bin/env bash
set -euo pipefail

echo "Starting Streamlit on localhost:8501"
echo "Run this in another terminal if the app is not already running:"
echo "  streamlit run app.py"
echo
echo "Starting Cloudflare Quick Tunnel for testing"
cloudflared tunnel --url http://localhost:8501
