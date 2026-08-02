#!/bin/bash
# Backend + frontend'i (tek FastAPI süreci, port 8000) bu projenin .venv'i ile başlatır.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "🚀 Text-to-3D Generator başlatılıyor..."

# Portu temizle
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

mkdir -p logs

echo "⚙️  Sunucu başlatılıyor (port 8000, frontend + API aynı süreçte)..."
nohup "$DIR/.venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
echo $! > logs/backend.pid

sleep 2

echo "🌍 Tarayıcı açılıyor..."
open http://localhost:8000

echo ""
echo "✅ Hazır!"
echo "   Uygulama: http://localhost:8000  (API docs: http://localhost:8000/docs)"
echo "   Durdurmak için: ./stop.sh"
echo "   Loglar: logs/backend.log"
