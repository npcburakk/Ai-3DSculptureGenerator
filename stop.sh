#!/bin/bash
# start.sh ile açılan sunucuyu durdurur.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

for pidfile in logs/backend.pid logs/frontend.pid; do
  if [ -f "$pidfile" ]; then
    pid="$(cat "$pidfile")"
    kill "$pid" 2>/dev/null && echo "🛑 Durduruldu: PID $pid"
    rm -f "$pidfile"
  fi
done

lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

echo "✅ Sunucu durduruldu."
