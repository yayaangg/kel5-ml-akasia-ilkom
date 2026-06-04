import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from pypdf import PdfReader
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Asisten Akademik Kampus",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        color: #155724;
        margin: 1rem 0;
    }
    .warning-message {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        color: #856404;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "llm" not in st.session_state:
    st.session_state.llm = None
if "processed" not in st.session_state:
    st.session_state.processed = False

# Persistent storage path
FAISS_INDEX_PATH = "./faiss_index"

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file with fallback methods"""
    
    # Method 1: Try pypdf first
    tmp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name
        
        st.write("📖 Metode 1: Menggunakan pypdf...")
        
        # Read PDF with pypdf
        pdf_reader = PdfReader(tmp_path)
        total_pages = len(pdf_reader.pages)
        
        st.write(f"� Membaca {total_pages} halaman...")
        
        text = ""
        pages_with_text = 0
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                    pages_with_text += 1
            except Exception as page_error:
                st.warning(f"⚠️ Gagal membaca halaman {i+1}: {str(page_error)}")
                continue
        
        text = text.strip()
        
        # If pypdf got good results, use it
        if text and len(text) > 100:
            os.unlink(tmp_path)
            st.write(f"✅ Berhasil ekstrak {len(text):,} karakter dari {pages_with_text}/{total_pages} halaman")
            return text
        
        # If pypdf failed or got minimal text, try PyMuPDF
        st.warning(f"⚠️ pypdf hanya mendapat {len(text)} karakter. Mencoba metode alternatif...")
        
    except Exception as e:
        st.warning(f"⚠️ pypdf gagal: {str(e)}. Mencoba metode alternatif...")
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        tmp_path = None # Reset tmp_path as it might have been deleted or not created
    
    # Method 2: Try PyMuPDF (fitz) as fallback
    try:
        import fitz  # PyMuPDF
        
        if not tmp_path:
            # Save file again if needed
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.getvalue())
                tmp_path = tmp_file.name
        
        st.write("📖 Metode 2: Menggunakan PyMuPDF (lebih powerful)...")
        
        # Open PDF with PyMuPDF
        doc = fitz.open(tmp_path)
        total_pages = len(doc)
        
        st.write(f"📄 Membaca {total_pages} halaman dengan PyMuPDF...")
        
        text = ""
        pages_with_text = 0
        
        for page_num in range(total_pages):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                    pages_with_text += 1
            except Exception as page_error:
                st.warning(f"⚠️ Gagal membaca halaman {page_num+1}: {str(page_error)}")
                continue
        
        doc.close()
        
        text = text.strip()
        
        # If PyMuPDF got good results, use it
        if text and len(text) > 100:
            os.unlink(tmp_path)
            st.write(f"✅ Berhasil ekstrak {len(text):,} karakter dari {pages_with_text}/{total_pages} halaman")
            return text
        
        # If PyMuPDF also failed, try OCR
        st.warning(f"⚠️ PyMuPDF hanya mendapat {len(text)} karakter.")
        st.info("🔍 PDF kemungkinan berisi gambar/scan. Mencoba OCR...")
        st.warning("⏱️ OCR membutuhkan waktu lebih lama (~30 detik per halaman)")
        
    except Exception as e:
        st.warning(f"⚠️ PyMuPDF gagal: {str(e)}. Mencoba OCR...")
    
    # Method 3: Try OCR for scanned PDFs
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        if not tmp_path or not os.path.exists(tmp_path):
            # Save file again if needed
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.getvalue())
                tmp_path = tmp_file.name
        
        st.write("📖 Metode 3: Menggunakan OCR (Optical Character Recognition)...")
        st.write("🖼️ Mengkonversi PDF ke gambar...")
        
        # Convert PDF to images
        images = convert_from_path(tmp_path)
        total_pages = len(images)
        
        st.write(f"📄 Melakukan OCR pada {total_pages} halaman...")
        st.warning(f"⏱️ Estimasi waktu: ~{total_pages * 30} detik ({total_pages} halaman × 30 detik)")
        
        text = ""
        ocr_progress = st.progress(0)
        
        for i, image in enumerate(images):
            try:
                st.write(f"� OCR halaman {i+1}/{total_pages}...")
                
                # Perform OCR on the image
                page_text = pytesseract.image_to_string(image, lang='ind+eng')  # Indonesian + English
                
                if page_text and page_text.strip():
                    text += page_text + "\n"
                
                # Update progress
                progress = int((i + 1) / total_pages * 100)
                ocr_progress.progress(progress)
                
            except Exception as page_error:
                st.warning(f"⚠️ OCR gagal pada halaman {i+1}: {str(page_error)}")
                continue
        
        ocr_progress.empty()
        os.unlink(tmp_path)
        
        text = text.strip()
        
        if not text:
            st.error(f"❌ OCR tidak berhasil mengekstrak teks dari {total_pages} halaman.")
            st.error("💡 Kemungkinan penyebab:")
            st.error("   • Kualitas gambar terlalu rendah")
            st.error("   • PDF terenkripsi atau terproteksi")
            st.error("   • Bahasa tidak didukung")
            return None
        
        if len(text) < 100:
            st.warning(f"⚠️ OCR hanya mendapat {len(text)} karakter")
            st.warning("Kualitas scan mungkin rendah atau teks sangat sedikit")
        
        st.success(f"✅ OCR berhasil! Ekstrak {len(text):,} karakter dari {total_pages} halaman")
        
        return text
        
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        st.error(f"❌ Semua metode gagal membaca PDF: {str(e)}")
        st.exception(e)
        return None

def create_vectorstore(text):
    """Create vector store from text using FAISS"""
    try:
        # Split text into chunks with larger size for better context
        st.write("🔪 Memotong dokumen menjadi chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Increased from 1000 for more context
            chunk_overlap=300,  # Increased from 200 for better continuity
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        st.write(f"✅ Berhasil membuat {len(chunks)} chunks")
        
        # Create embeddings
        st.write("🧠 Membuat embeddings (pertama kali akan download model ~90MB)...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Create and persist vectorstore
        st.write(f"💾 Membuat vector database dari {len(chunks)} chunks...")
        vectorstore = FAISS.from_texts(
            texts=chunks,
            embedding=embeddings
        )
        
        # Save to disk
        st.write("💾 Menyimpan ke disk...")
        vectorstore.save_local(FAISS_INDEX_PATH)
        st.write("✅ Vector store berhasil disimpan!")
        
        return vectorstore
    except Exception as e:
        st.error(f"Error membuat vector store: {str(e)}")
        return None

def load_existing_vectorstore():
    """Load existing vectorstore if available"""
    try:
        # Check if the FAISS index directory exists and contains FAISS files
        if os.path.exists(FAISS_INDEX_PATH) and os.path.isdir(FAISS_INDEX_PATH) and any(f.endswith(".faiss") for f in os.listdir(FAISS_INDEX_PATH)):
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            vectorstore = FAISS.load_local(
                folder_path=FAISS_INDEX_PATH,
                embeddings=embeddings,
                allow_dangerous_deserialization=True # Required for FAISS.load_local
            )
            return vectorstore
    except Exception as e:
        st.warning(f"Tidak dapat memuat knowledge base yang ada: {str(e)}")
    return None

def create_llm(api_token=None):
    """Create LLM instance using Ollama (local model)"""
    try:
        import requests
        
        # Create a simple wrapper class for Ollama
        class OllamaWrapper:
            def __init__(self, model="llama3.2:3b", base_url="http://localhost:11434"):
                self.model = model
                self.base_url = base_url
            
            def invoke(self, prompt):
                """Generate text using Ollama local model"""
                try:
                    response = requests.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.3,  # Lower for more focused, strict answers
                                "top_p": 0.9,  # Nucleus sampling for coherence
                                "num_predict": 1024,  # Longer responses
                                "repeat_penalty": 1.1,  # Reduce repetition
                            }
                        },
                        timeout=90  # Longer timeout for better responses
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("response", "No response generated")
                    else:
                        error_msg = f"Ollama error (status {response.status_code}): {response.text}"
                        st.error(error_msg)
                        return error_msg
                        
                except requests.exceptions.ConnectionError:
                    error_msg = "Tidak dapat terhubung ke Ollama. Pastikan Ollama service berjalan: brew services start ollama"
                    st.error(error_msg)
                    return error_msg
                except Exception as e:
                    error_msg = f"Error generating response: {str(e)}"
                    st.error(error_msg)
                    return error_msg
        
        # Initialize Ollama wrapper
        llm = OllamaWrapper(model="llama3.2:3b")
        
        # Test connection
        st.info("🤖 Menggunakan Ollama (model lokal) - Tidak perlu API token!")
        
        return llm
    except Exception as e:
        st.error(f"Error membuat LLM: {str(e)}")
        st.exception(e)
        return None

def answer_question(question, vectorstore, llm):
    """Answer question using RAG with enhanced customer service quality"""
    try:
        # Retrieve more relevant documents for better coverage
        docs = vectorstore.similarity_search(question, k=5)
        
        # Combine documents into context
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Create professional customer service prompt with strict context enforcement
        prompt = f"""Anda adalah Asisten Akademik Virtual Jurusan Ilmu Komputer (ILKOM) yang profesional dan ramah.

ATURAN KETAT - WAJIB DIIKUTI:
1. HANYA jawab pertanyaan yang BERKAITAN dengan dokumen akademik yang telah di-upload
2. Jika pertanyaan TIDAK ADA dalam konteks dokumen, TOLAK dengan sopan
3. JANGAN jawab pertanyaan umum, chitchat, atau topik di luar dokumen
4. JANGAN gunakan pengetahuan di luar konteks dokumen yang diberikan

ATURAN PENOLAKAN:
Jika pertanyaan di luar konteks dokumen, gunakan template ini:
"Maaf, saya hanya dapat menjawab pertanyaan yang berkaitan dengan dokumen akademik yang telah di-upload. Pertanyaan Anda sepertinya di luar konteks dokumen tersebut. Silakan ajukan pertanyaan seputar informasi akademik dalam dokumen."

CONTOH PERTANYAAN YANG HARUS DITOLAK:
- "Siapa presiden Indonesia?"
- "Bagaimana cara memasak nasi goreng?"
- "Ceritakan tentang sejarah dunia"
- "Halo, apa kabar?" (chitchat umum)

CONTOH PERTANYAAN YANG BOLEH DIJAWAB (jika ada dalam dokumen):
- "Apa persyaratan kelulusan?"
- "Berapa SKS minimal per semester?"
- "Bagaimana prosedur pengajuan cuti akademik?"

PANDUAN MENJAWAB (untuk pertanyaan yang relevan):
1. Berikan jawaban yang jelas, lengkap, dan terstruktur
2. Gunakan bullet points atau numbering jika ada beberapa poin
3. Sebutkan sumber informasi jika relevan (misal: "Berdasarkan Kalender Akademik...")
4. Bersikap profesional dan ramah seperti customer service

KONTEKS DOKUMEN:
{context}

PERTANYAAN MAHASISWA:
{question}

INSTRUKSI:
- Baca pertanyaan dengan teliti
- Periksa apakah pertanyaan relevan dengan konteks dokumen di atas
- Jika TIDAK relevan, gunakan template penolakan
- Jika relevan, jawab dengan profesional berdasarkan konteks

JAWABAN ANDA:"""
        
        # Get answer from LLM using invoke method
        answer = llm.invoke(prompt)
        
        # Clean up answer
        answer = answer.strip()
        
        # Post-process: ensure answer doesn't start with redundant phrases
        redundant_starts = [
            "Jawaban:",
            "Jawaban Anda:",
            "JAWABAN:",
            "Berdasarkan konteks di atas,",
        ]
        for phrase in redundant_starts:
            if answer.startswith(phrase):
                answer = answer[len(phrase):].strip()
        
        return answer
    except Exception as e:
        return f"Maaf, terjadi kesalahan teknis: {str(e)}. Silakan coba lagi atau hubungi administrator jika masalah berlanjut."

# Sidebar
with st.sidebar:
    st.title("⚙️ Konfigurasi")
    
    # Info about local model
    st.info("🤖 Menggunakan Ollama (Model Lokal)")
    st.caption("Tidak perlu API token - model berjalan di komputer Anda!")
    
    st.divider()
    
    # File uploader
    st.subheader("📄 Upload Dokumen")
    uploaded_files = st.file_uploader(
        "Upload PDF Panduan Akademik (bisa lebih dari 1 file)",
        type=['pdf'],
        accept_multiple_files=True,  # Enable multiple files
        help="Upload satu atau lebih dokumen PDF yang berisi panduan akademik kampus"
    )
    
    # Show file info if uploaded
    if uploaded_files:
        total_size = sum([f.size for f in uploaded_files]) / (1024 * 1024)
        st.info(f"📁 **{len(uploaded_files)} file** dipilih | Total: **{total_size:.2f} MB**")
        
        # Show individual files
        for i, file in enumerate(uploaded_files, 1):
            file_size_mb = file.size / (1024 * 1024)
            st.caption(f"{i}. {file.name} ({file_size_mb:.2f} MB)")
        
        # Estimate processing time based on total size
        if total_size < 1:
            est_time = "30 detik - 1 menit"
        elif total_size < 5:
            est_time = "1-3 menit"
        elif total_size < 10:
            est_time = "3-5 menit"
        else:
            est_time = "5-10 menit"
        st.caption(f"⏱️ Estimasi waktu proses: {est_time} (pertama kali akan lebih lama karena download model)")
    
    # Process button
    if st.button("🔄 Proses Dokumen", type="primary", use_container_width=True):
        if not uploaded_files:
            st.error("⚠️ Silakan upload file PDF terlebih dahulu!")
        else:
            # Create progress container
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Extract text from all PDFs
                status_text.text(f"📄 Mengekstrak teks dari {len(uploaded_files)} file PDF...")
                progress_bar.progress(5)
                
                all_text = ""
                total_chars = 0
                
                for idx, uploaded_file in enumerate(uploaded_files, 1):
                    status_text.text(f"📄 Mengekstrak file {idx}/{len(uploaded_files)}: {uploaded_file.name}")
                    progress = 5 + (idx / len(uploaded_files) * 15)  # 5-20%
                    progress_bar.progress(int(progress))
                    
                    text = extract_text_from_pdf(uploaded_file)
                    
                    if text:
                        all_text += f"\n\n=== Dokumen: {uploaded_file.name} ===\n\n{text}"
                        total_chars += len(text)
                    else:
                        st.warning(f"⚠️ Gagal ekstrak {uploaded_file.name}, dilewati...")
                
                if not all_text:
                    st.error("❌ Gagal mengekstrak teks dari PDF. Pastikan PDF tidak terenkripsi dan berisi teks.")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    # Show file info
                    status_text.text(f"✅ Berhasil ekstrak {total_chars:,} karakter dari {len(uploaded_files)} file")
                    progress_bar.progress(25)
                    
                    # Step 2: Create vectorstore
                    status_text.text("🔨 Memotong teks menjadi chunks...")
                    progress_bar.progress(40)
                    
                    vectorstore = create_vectorstore(all_text)
                    
                    if not vectorstore:
                        st.error("❌ Gagal membuat vector store. Periksa koneksi internet untuk download model embeddings.")
                        progress_bar.empty()
                        status_text.empty()
                    else:
                        status_text.text("✅ Vector store berhasil dibuat")
                        progress_bar.progress(70)
                        
                        # Step 3: Create LLM
                        status_text.text("🤖 Menginisialisasi LLM...")
                        progress_bar.progress(85)
                        
                        llm = create_llm()
                        
                        if not llm:
                            st.error("❌ Gagal menginisialisasi LLM. Periksa API token Anda.")
                            progress_bar.empty()
                            status_text.empty()
                        else:
                            # Success!
                            status_text.text("✅ Semua proses selesai!")
                            progress_bar.progress(100)
                            
                            st.session_state.vectorstore = vectorstore
                            st.session_state.llm = llm
                            st.session_state.processed = True
                            
                            # Clear progress indicators
                            import time
                            time.sleep(0.5)
                            progress_bar.empty()
                            status_text.empty()
                            
                            # Show success
                            st.success("✅ Knowledge Base Updated!")
                            st.info(f"📊 {len(uploaded_files)} dokumen berhasil diproses: {total_chars:,} karakter")
                            st.balloons()
                            
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Terjadi kesalahan: {str(e)}")
                st.exception(e)  # Show full traceback for debugging
    
    st.divider()
    
    # Try to load existing vectorstore on startup
    if st.session_state.vectorstore is None:
        existing_vs = load_existing_vectorstore()
        if existing_vs:
            st.session_state.vectorstore = existing_vs
            llm = create_llm()
            if llm:
                st.session_state.llm = llm
                st.session_state.processed = True
                st.info("📚 Knowledge base yang ada telah dimuat")
    
    # Status
    st.subheader("📊 Status")
    if st.session_state.processed:
        st.success("✅ Sistem siap digunakan")
    else:
        st.warning("⏳ Menunggu dokumen diproses")
    
    # Instructions
    with st.expander("ℹ️ Cara Penggunaan"):
        st.markdown("""
        1. Masukkan **Hugging Face API Token** Anda
        2. Upload file **PDF Panduan Akademik**
        3. Klik tombol **Proses Dokumen**
        4. Tunggu hingga proses selesai
        5. Mulai bertanya di chat!
        
        **Contoh Pertanyaan:**
        - Apa saja persyaratan kelulusan?
        - Bagaimana cara mengajukan cuti akademik?
        - Berapa SKS minimal per semester?
        """)

# Main chat interface
st.title("🎓 Asisten Akademik Kampus")
st.markdown("Tanyakan apapun tentang panduan akademik kampus Anda!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ketik pertanyaan Anda di sini..."):
    # Check if system is ready
    if not st.session_state.processed or st.session_state.llm is None:
        st.warning("⚠️ Silakan upload dan proses dokumen terlebih dahulu di sidebar!")
    else:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                try:
                    answer = answer_question(
                        prompt, 
                        st.session_state.vectorstore, 
                        st.session_state.llm
                    )
                    
                    # Display answer
                    st.markdown(answer)
                    
                    # Add to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    error_msg = f"Maaf, terjadi kesalahan: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <small>🤖 Powered by LangChain, FAISS & HuggingFace | 
        Asisten Akademik Kampus v1.0</small>
    </div>
    """,
    unsafe_allow_html=True
)
