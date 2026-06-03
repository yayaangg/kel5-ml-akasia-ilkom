#!/bin/bash
# ============================================
# AKASIA v1.0 - Script Setup Otomatis
# ============================================
# Jalankan script ini untuk setup cepat:
# chmod +x setup.sh && ./setup.sh
# ============================================

echo "🎓 AKASIA v1.0 - Setup Otomatis"
echo "================================"

# Cek Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 tidak ditemukan. Silakan install Python 3.10+"
    exit 1
fi

# Buat virtual environment jika belum ada
if [ ! -d "venv" ]; then
    echo "📦 Membuat virtual environment..."
    python3 -m venv venv
fi

# Aktivasi virtual environment
echo "🔄 Mengaktifkan virtual environment..."
source venv/bin/activate

# Install dependensi Python
echo "📥 Menginstall dependensi Python..."
pip install -r requirements.txt --quiet

# Cek .env file
if [ ! -f ".env" ]; then
    echo "📄 Membuat file .env dari template..."
    cp .env.example .env
fi

echo ""
echo "✅ Setup selesai!"
echo ""
echo "================================"
echo "CARA MENJALANKAN:"
echo "================================"
echo ""
echo "Terminal 1 (Backend):"
echo "  source venv/bin/activate"
echo "  python api.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd rag-app"
echo "  npm install"
echo "  npm run dev"
echo ""
echo "Akses:"
echo "  Chat: http://localhost:3000"
echo "  Admin: http://localhost:3000/admin"
echo ""
echo "🎓 Selamat menggunakan AKASIA!"
