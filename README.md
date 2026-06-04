# 🎓 AKASIA

**Asisten Akademik Berbasis AI untuk Program Studi Ilmu Komputer**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## 📋 Deskripsi

AKASIA (Asisten Akademik Sistem Informasi Answering) adalah chatbot berbasis RAG (Retrieval-Augmented Generation) yang dirancang khusus untuk menjawab pertanyaan seputar peraturan akademik dan kalender akademik Program Studi Ilmu Komputer (ILKOM).

### ✨ Fitur Utama

- 🤖 **AI Chatbot** - Jawaban cerdas berbasis dokumen akademik
- 📄 **PDF Processing** - Ekstraksi teks otomatis dari dokumen PDF
- 🔍 **OCR Support** - Mendukung PDF hasil scan dengan Tesseract
- 📊 **Multi-Strategy Retrieval** - Pencarian semantik, keyword, dan regulatory
- 💬 **Streaming Response** - Respons real-time seperti ChatGPT
- 📁 **Auto-Load Documents** - Dokumen otomatis dimuat dari folder `data/`
- 🎨 **Modern UI** - Antarmuka modern dengan tema biru-ungu

---

## 🏗️ Struktur Folder

```
chatbot_uho/
├── 📁 data/                    # Folder dokumen PDF (auto-load)
│   ├── Kalender_Akademik.pdf
│   └── Peraturan_Rektor.pdf
│
├── 📁 rag-app/                 # Frontend Next.js
│   ├── app/                    # Halaman aplikasi
│   │   ├── page.tsx           # Halaman utama chat
│   │   ├── admin/             # Halaman admin
│   │   └── globals.css        # Style global  
│   ├── components/            # Komponen React
│   │   ├── chat/              # Komponen chat
│   │   └── ui/                # Komponen UI
│   └── package.json
│
├── 📁 faiss_index/             # Index vektor FAISS
├── 📄 api.py                   # FastAPI Backend Server
├── 📄 rag_engine.py            # Mesin RAG utama
├── 📄 app.py                   # Fungsi pendukung Streamlit
├── 📄 requirements.txt         # Dependensi Python
├── 📄 .env                     # Konfigurasi environment
└── 📄 README.md                # Dokumentasi ini
```

---

## 🚀 Cara Menjalankan

### Prasyarat

- Python 3.10+
- Node.js 18+

### 🚀 Quick Start (3 Langkah)

```bash
# 1. Clone repository
git clone https://github.com/gstkrsnaprnta/akasia-uho.git
cd akasia-uho

# 2. Setup otomatis (install dependencies + buat .env)
chmod +x setup.sh && ./setup.sh

# 3. Jalankan backend (Terminal 1)
source venv/bin/activate && python api.py
```

```bash
# 4. Jalankan frontend (Terminal 2)
cd rag-app && npm install && npm run dev
```

**Akses:** http://localhost:3000

> ✅ **Catatan:** Knowledge base sudah ter-index (3 dokumen akademik ILKOM).
> API key demo sudah tersedia di `.env.example`.

---

### Instalasi Manual (Opsional)

### 2. Setup Backend Python

```bash
# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# atau: venv\Scripts\activate  # Windows

# Install dependensi
pip install -r requirements.txt

# Salin file environment
cp .env.example .env
# Edit .env dan masukkan GROQ_API_KEY
```

### 3. Setup Frontend Next.js

```bash
cd rag-app
npm install
```

### 4. Jalankan Aplikasi

**Terminal 1 - Backend:**
```bash
# Di folder utama
source venv/bin/activate
export GROQ_API_KEY="your_api_key"
python api.py
```

**Terminal 2 - Frontend:**
```bash
# Di folder rag-app
cd rag-app
npm run dev
```

### 5. Akses Aplikasi

- **Chat**: http://localhost:3000
- **Admin**: http://localhost:3000/admin
- **API**: http://localhost:8000

---

## 📄 Menambah Dokumen

### Cara 1: Auto-Load (Rekomendasi)

Cukup letakkan file PDF ke folder `data/`, lalu restart backend:

```bash
# Tambahkan PDF ke folder data
cp dokumen_baru.pdf data/

# Restart backend
python api.py
```

Sistem akan otomatis memuat dokumen baru.

### Cara 2: Via Admin Panel

1. Buka http://localhost:3000/admin
2. Klik "Upload Dokumen"
3. Pilih file PDF

---

## ⚙️ Konfigurasi

### Environment Variables (.env)

```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxx  # API Key dari console.groq.com
```

### Parameter RAG (rag_engine.py)

| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| `chunk_size` | 1500 | Ukuran chunk teks |
| `chunk_overlap` | 300 | Overlap antar chunk |
| `k_semantic` | 25 | Jumlah hasil pencarian semantik |
| `k_keyword` | 15 | Jumlah hasil pencarian keyword |

---

## 🔧 Teknologi

### Backend
- **Python 3.10+** - Bahasa pemrograman utama
- **FastAPI** - Web framework untuk API
- **LangChain** - Framework RAG
- **FAISS** - Vector database
- **Groq API** - LLM (Llama 3.1)
- **Tesseract** - OCR untuk PDF scan
- **PyMuPDF** - Ekstraksi tabel PDF

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Framer Motion** - Animasi
- **Lucide Icons** - Ikon

---

## 📝 Changelog

- ✅ Rilis AKASIA
- ✅ Fitur chat dengan streaming response
- ✅ Multi-strategy retrieval (semantic, keyword, regulatory)
- ✅ Auto-load dokumen dari folder `data/`
- ✅ OCR support untuk PDF scan
- ✅ Admin panel untuk manajemen dokumen
- ✅ UI modern dengan tema biru-ungu
- ✅ Riwayat chat dengan localStorage

---

## 📄 Lisensi

MIT License - Bebas digunakan untuk keperluan akademik.

---

## 🐛 Troubleshooting

### Port 8000 sudah digunakan
```bash
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Error OCR
```bash
brew install tesseract tesseract-lang
```

### Frontend tidak bisa connect ke backend
Pastikan backend berjalan di http://localhost:8000 dan periksa CORS settings.

---

**AKASIA** - Dikembangkan dengan ❤️ untuk Program Studi Ilmu Komputer
