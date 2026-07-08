#!/bin/bash
# Backend + frontend'i bu projenin .venv'i ile başlatır.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "🚀 Text-to-3D Generator başlatılıyor..."

# Portları temizle
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

mkdir -p logs

echo "⚙️  Backend başlatılıyor (port 8000)..."
nohup "$DIR/.venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
echo $! > logs/backend.pid

echo "🌐 Frontend başlatılıyor (port 3000)..."
nohup "$DIR/.venv/bin/python" -m http.server 3000 > logs/frontend.log 2>&1 &
echo $! > logs/frontend.pid

sleep 2

echo "🌍 Tarayıcı açılıyor..."
open http://localhost:3000/index.html

echo ""
echo "✅ Hazır!"
echo "   Frontend: http://localhost:3000/index.html"
echo "   Backend:  http://localhost:8000  (docs: http://localhost:8000/docs)"
echo "   Durdurmak için: ./stop.sh"
echo "   Loglar: logs/backend.log, logs/frontend.log"
