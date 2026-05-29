#!/bin/bash

echo "🚀 Text-to-3D Generator başlatılıyor..."

# conda'yı aktifleştir
source "$(conda info --base)/etc/profile.d/conda.sh"

# text3d ortamı yoksa oluştur
if ! conda env list | grep -q "text3d"; then
  echo "📦 text3d ortamı oluşturuluyor (Python 3.10)..."
  conda create -n text3d python=3.10 -y
fi

deactivate 2>/dev/null
conda activate text3d
cd ~/Downloads/files-2

# Gerekli paketleri kontrol et ve yükle
echo "📦 Bağımlılıklar kontrol ediliyor..."
pip install -q fastapi uvicorn pydantic pydantic-settings python-dotenv httpx sqlalchemy "python-jose[cryptography]" bcrypt python-multipart "pydantic[email]"
pip install -q pyyaml Pillow numpy

if ! python -c "import torch" 2>/dev/null; then
  echo "⚙️  PyTorch yükleniyor..."
  pip install -q torch torchvision
fi

if ! python -c "import shap_e" 2>/dev/null; then
  echo "⚙️  Shap-E yükleniyor..."
  pip install -q git+https://github.com/openai/shap-e.git
fi

if ! python -c "import trimesh" 2>/dev/null; then
  echo "⚙️  Trimesh yükleniyor..."
  pip install -q trimesh
fi

if ! python -c "import ipywidgets" 2>/dev/null; then
  echo "⚙️  ipywidgets yükleniyor..."
  pip install -q ipywidgets
fi

echo "✅ Tüm bağımlılıklar hazır!"

# Portları temizle
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 1

# Backend'i başlat
echo "⚙️  Backend başlatılıyor (port 8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3

# Frontend'i başlat
echo "🌐 Frontend başlatılıyor (port 3000)..."
python -m http.server 3000 &
FRONTEND_PID=$!
sleep 1

# Tarayıcıyı aç
echo "🌍 Tarayıcı açılıyor..."
open http://localhost:3000

echo ""
echo "✅ Her şey hazır! http://localhost:3000 adresinde çalışıyor."
echo "   Durdurmak için Ctrl+C'ye bas."
echo ""

trap "echo '🛑 Durduruluyor...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
