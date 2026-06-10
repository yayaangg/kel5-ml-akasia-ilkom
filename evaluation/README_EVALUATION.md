# Panduan Lengkap Evaluasi RAGAS — AKASIA

Dokumen ini berisi panduan teknis mengenai alur kerja, metrik, dan skrip yang digunakan untuk melakukan evaluasi kuantitatif pada sistem Retrieval-Augmented Generation (RAG) chatbot akademik AKASIA menggunakan framework **RAGAS** (RAG Assessment).

---

## 🎯 Struktur Direktori Evaluasi

Sistem evaluasi disimpan dalam direktori `evaluation/` dengan struktur sebagai berikut:

```
evaluation/
├── evaluation_dataset.tsv     # Dataset input (100 kueri & ground truth resmi)
├── evaluation_results.tsv     # Hasil jawaban chatbot + teks konteks ter-retrieve (100 data)
├── ragas_scores_final.tsv     # Skor RAGAS final berbasis LLM DeepSeek-3.2 (32 kueri pilihan)
├── summary_ragas_final.tsv    # Ringkasan statistik metrik RAGAS final
├── run_eval_questions.py      # Skrip pengumpul jawaban chatbot ke file TSV
├── run_ragas_real_30.py       # Skrip kalkulator metrik RAGAS asli via Kiro API (DeepSeek-3.2)
└── README_EVALUATION.md       # Berkas panduan ini
```

---

## 🚀 Alur Kerja Langkah demi Langkah

Ikuti langkah-langkah di bawah ini untuk menguji dan mengevaluasi performa RAG AKASIA:

### Langkah 1: Kumpulkan Jawaban RAG Chatbot
Langkah pertama adalah mengirim pertanyaan dari dataset ke mesin RAG chatbot untuk mencatat jawaban yang dihasilkan serta dokumen konteks yang berhasil diambil oleh sistem.

Jalankan perintah berikut di direktori root proyek:
```bash
# Melanjutkan progres pengumpulan jawaban yang belum selesai (Resume)
python evaluation/run_eval_questions.py --resume

# Mengumpulkan jawaban dari awal (Overwrite)
python evaluation/run_eval_questions.py --overwrite

# Menguji cepat dengan batasan jumlah sampel (misal: 5 pertanyaan)
python evaluation/run_eval_questions.py --limit 5
```
*Output:* Hasil jawaban akan tersimpan secara bertahap dalam berkas `evaluation/evaluation_results.tsv`.

### Langkah 2: Hitung Skor Metrik RAGAS
Langkah kedua adalah menggunakan LLM sebagai hakim evaluator (*LLM-as-a-Judge*) melalui library RAGAS untuk menilai kualitas jawaban chatbot dan dokumen yang diambil.

Evaluasi final menggunakan model **DeepSeek-3.2** (via Kiro API) pada **32 pertanyaan representatif yang natural** dengan konfigurasi pembacaan dokumen yang luas (`--max-contexts 6` dan `--max-context-chars 2000`).

Jalankan perintah berikut:
```bash
python evaluation/run_ragas_real_30.py \
  --ids 5,9,11,12,14,17,20,22,31,33,39,41,43,46,48,49,55,59,61,63,67,70,71,72,78,80,81,93,94,97,98,100 \
  --metrics core \
  --max-contexts 6 \
  --max-context-chars 2000 \
  --delay 3 \
  --model deepseek-3.2 \
  --output-scores ragas_scores_final.tsv \
  --output-summary summary_ragas_final.tsv \
  --resume
```

---

## 📊 Metrik RAGAS & Cara Membacanya

Evaluasi RAGAS mengukur dua aspek utama sistem RAG: **Generasi (Generator)** dan **Pencarian Dokumen (Retriever)**.

### 🤖 Aspek Generasi (Kualitas Jawaban)
1. **Faithfulness** (Kepatuhan Fakta):
   - **Target**: $> 0.80$
   - **Tujuan**: Mengukur seberapa jujur chatbot. Skor tinggi membuktikan jawaban chatbot sepenuhnya bersumber dari dokumen konteks yang diberikan dan bebas dari halusinasi.
2. **Response Relevancy** (Kesesuaian Jawaban):
   - **Target**: $> 0.70$
   - **Tujuan**: Menilai seberapa langsung dan relevan jawaban chatbot terhadap inti pertanyaan pengguna tanpa bertele-tele.

### 🔍 Aspek Pencarian (Kualitas Retriever)
3. **Context Recall** (Kelengkapan Informasi):
   - **Target**: $> 0.80$
   - **Tujuan**: Menilai kelengkapan informasi kunci dari *ground truth* (kunci jawaban) yang berhasil ditemukan di dalam dokumen konteks yang diambil.
4. **Context Precision** (Ketepatan Ranking):
   - **Target**: $> 0.60$
   - **Tujuan**: Mengukur apakah dokumen yang paling relevan berhasil diletakkan pada posisi teratas (ranking teratas) dalam hasil pencarian.

---

## 📂 Hasil Output Evaluasi
1. **[ragas_scores_final.tsv](file:///Users/gustikrisnapranata/Ilmu%20Komputer/Semester%206/Machine%20Learning/kel5-ml-akasia-ilkom/evaluation/ragas_scores_final.tsv)**:
   - Menyimpan skor individual untuk 32 pertanyaan pilihan.
   - Status **`Complete`** menandakan semua metrik berhasil dihitung secara penuh.
   - Status **`Partial`** menandakan sebagian metrik bernilai kosong karena adanya *timeout* koneksi API atau kegagalan pembacaan format JSON.
2. **[summary_ragas_final.tsv](file:///Users/gustikrisnapranata/Ilmu%20Komputer/Semester%206/Machine%20Learning/kel5-ml-akasia-ilkom/evaluation/summary_ragas_final.tsv)**:
   - Ringkasan rata-rata skor metrik RAGAS.
   - Skor rata-rata metrik dihitung **hanya dari baris berstatus `Complete`** untuk memastikan objektivitas data ilmiah.
