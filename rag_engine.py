"""
============================================
AKASIA - RAG Engine
============================================
Retrieval-Augmented Generation Engine

Fitur:
- Hybrid Search: FAISS semantic + BM25 keyword
- Cross-Encoder Re-ranking: Neural relevance scoring
- Confidence Scoring: Tampilkan keyakinan jawaban
- Enhanced Chunking: Pasal-aware + semantic

Model yang digunakan:
- Embedding: paraphrase-multilingual-MiniLM-L12-v2
- Re-ranker: cross-encoder/ms-marco-MiniLM-L-6-v2
- LLM: Groq Llama 3.1 8B Instant
============================================
"""

import os
import json
import time
import re
from datetime import datetime
from groq import Groq
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

# Konfigurasi path untuk penyimpanan data
FAISS_INDEX_PATH = "./faiss_index"      # Folder untuk index vektor FAISS
METADATA_FILE = "./documents_metadata.json"  # File metadata dokumen
DATA_FOLDER = "./data"                   # Folder dokumen PDF untuk auto-load

class RAGEngine:
    def __init__(self):
        self.embeddings = self._get_embeddings()
        self.vectorstore = self.load_existing_vectorstore()
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.llm_model = "llama-3.1-8b-instant"
        self.fallback_model = "llama-3.3-70b-versatile"
        self.metadata = self.load_metadata()
        
        # Initialize BM25 index and cross-encoder
        self.bm25_index = None
        self.bm25_corpus = []
        self.cross_encoder = None
        self._init_cross_encoder()
        self._build_bm25_index()
        
        # Response caching for instant responses
        self.response_cache = {}  # query_hash -> {response, citations, confidence, timestamp}
        self.cache_max_size = 100  # Max cached responses
        self.cache_ttl = 3600  # Cache time-to-live in seconds (1 hour)
        self.cache_stats = {"hits": 0, "misses": 0}
        
        # Auto-load documents from data folder on startup
        self._auto_load_documents()
    
    def _get_embeddings(self):
        """Get embeddings model - use multilingual for Indonesian"""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'}
        )
    
    # ========================================
    # BM25 Index for Hybrid Search
    # ========================================
    
    def _build_bm25_index(self):
        """Build BM25 index from existing vectorstore documents"""
        try:
            from rank_bm25 import BM25Okapi
            
            if not self.vectorstore:
                print("  ℹ️ No vectorstore yet, BM25 index will be built after document load")
                return
            
            # Get all documents from vectorstore
            all_docs = self.vectorstore.docstore._dict.values()
            self.bm25_corpus = []
            self.bm25_doc_map = {}
            
            for i, doc in enumerate(all_docs):
                # Tokenize for BM25
                tokens = self._tokenize_for_bm25(doc.page_content)
                self.bm25_corpus.append(tokens)
                self.bm25_doc_map[i] = doc
            
            if self.bm25_corpus:
                self.bm25_index = BM25Okapi(self.bm25_corpus)
                print(f"  ✓ BM25 index built: {len(self.bm25_corpus)} documents")
            
        except Exception as e:
            print(f"  ⚠️ BM25 index build failed: {e}")
            self.bm25_index = None
    
    def _tokenize_for_bm25(self, text):
        """Tokenize text for BM25 (simple whitespace + lowercase)"""
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text.split()
        # Remove short tokens
        return [t for t in tokens if len(t) > 2]
    
    def _bm25_search(self, query, k=20):
        """Search using BM25 keyword matching""" 
        if not self.bm25_index or not self.bm25_corpus:
            return []
        
        query_tokens = self._tokenize_for_bm25(query)
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Get top k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for idx in top_indices:
            if idx in self.bm25_doc_map and scores[idx] > 0:
                results.append((self.bm25_doc_map[idx], scores[idx]))
        
        return results
    
    # ========================================
    # Cross-Encoder Re-ranking
    # ========================================
    
    def _init_cross_encoder(self):
        """Initialize cross-encoder model for neural re-ranking"""
        try:
            from sentence_transformers import CrossEncoder
            print("  ⏳ Loading cross-encoder model...")
            self.cross_encoder = CrossEncoder(
                'cross-encoder/ms-marco-MiniLM-L-6-v2',
                max_length=512
            )
            print("  ✓ Cross-encoder loaded")
        except Exception as e:
            print(f"  ⚠️ Cross-encoder init failed: {e}")
            self.cross_encoder = None
    
    def _cross_encoder_rerank(self, query, docs, top_k=10):
        """
        Re-rank documents using cross-encoder neural model
        with query-aware term boosting for S1/S2/S3/D3/D4 mappings
        """
        if not self.cross_encoder or not docs:
            return docs[:top_k]
        
        try:
            # Prepare query-document pairs
            pairs = [[query, doc.page_content[:512]] for doc, _, _ in docs]
            
            # Get cross-encoder scores
            scores = self.cross_encoder.predict(pairs)
            
            # Query-aware term boosting
            query_lower = query.lower()
            boost_mappings = {
                's1': {'match': ['program sarjana', 'sarjana'], 'exclude': ['magister', 'doktor']},
                's2': {'match': ['program magister', 'magister'], 'exclude': ['doktor']},
                's3': {'match': ['program doktor', 'doktor'], 'exclude': []},
                'd3': {'match': ['diploma 3', 'diploma tiga'], 'exclude': []},
                'd4': {'match': ['diploma 4', 'diploma empat', 'sarjana terapan'], 'exclude': []},
            }
            
            boosted_scores = []
            for i, score in enumerate(scores):
                boost = 0.0
                doc_content = docs[i][0].page_content.lower()
                
                # Check if query contains a program code
                for code, config in boost_mappings.items():
                    if code in query_lower:
                        has_match = any(term in doc_content for term in config['match'])
                        has_exclude = any(term in doc_content for term in config['exclude'])
                        
                        if has_match and not has_exclude:
                            # Perfect match: has target program, no conflicting programs
                            boost = 5.0
                        elif has_match and has_exclude:
                            # Mixed doc: has target but also has other programs (e.g., "S1 for magister")
                            boost = -5.0  # Strong penalize to outweigh high CE
                        elif has_exclude:
                            # Wrong program entirely
                            boost = -4.0
                        break
                
                # Semester date detection for calendar queries
                # Gasal 2025.1 = Aug-Dec 2025 (dates with /08/2025 - /12/2025 or /01/2026)
                # Genap 2025.2 = Feb-Jun 2026 (dates with /02/2026 - /06/2026)
                import re
                if 'gasal' in query_lower or '2025.1' in query_lower:
                    # Look for Gasal dates: Aug 2025 - Jan 2026
                    gasal_dates = re.findall(r'/(?:0[789]|1[012])/2025|/01/2026', doc_content)
                    genap_dates = re.findall(r'/0[2-6]/2026', doc_content)
                    gasal_count = len(gasal_dates)
                    genap_count = len(genap_dates)
                    
                    if gasal_count > 0 and genap_count == 0:
                        boost += 6.0  # Pure Gasal doc
                    elif gasal_count > genap_count:
                        ratio = gasal_count / (gasal_count + genap_count)
                        boost += 4.0 * ratio  # Mostly Gasal
                    elif genap_count > 0 and gasal_count == 0:
                        boost -= 6.0  # Pure Genap = wrong semester
                    elif genap_count > gasal_count:
                        boost -= 4.0  # Mostly Genap
                        
                elif 'genap' in query_lower or '2025.2' in query_lower:
                    gasal_dates = re.findall(r'/(?:0[789]|1[012])/2025', doc_content)
                    genap_dates = re.findall(r'/0[2-6]/2026', doc_content)
                    gasal_count = len(gasal_dates)
                    genap_count = len(genap_dates)
                    
                    if genap_count > 0 and gasal_count == 0:
                        boost += 6.0
                    elif genap_count > gasal_count:
                        ratio = genap_count / (gasal_count + genap_count)
                        boost += 4.0 * ratio
                    elif gasal_count > 0 and genap_count == 0:
                        boost -= 6.0
                    elif gasal_count > genap_count:
                        boost -= 4.0
                
                boosted_scores.append(float(score) + boost)
            
            # Combine with original docs
            scored_docs = [(docs[i][0], docs[i][1], docs[i][2], boosted_scores[i]) 
                          for i in range(len(docs))]
            
            # Sort by boosted cross-encoder score (higher is better)
            scored_docs.sort(key=lambda x: x[3], reverse=True)
            
            return scored_docs[:top_k]
        except Exception as e:
            print(f"  ⚠️ Cross-encoder rerank failed: {e}")
            return [(d, s, st, 0.5) for d, s, st in docs[:top_k]]
    
    # ========================================
    # Hybrid Search (Semantic + BM25)
    # ========================================
    
    def _hybrid_search(self, query, k=30, alpha=0.7):
        """
        Hybrid search combining semantic (FAISS) and keyword (BM25) search.
        alpha: weight for semantic search (1-alpha for BM25)
        """
        all_results = []
        seen_hashes = set()
        
        # 1. Semantic search via FAISS
        semantic_results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        # Normalize FAISS scores (lower is better, convert to 0-1 higher is better)
        if semantic_results:
            max_score = max(score for _, score in semantic_results) + 0.001
            for doc, score in semantic_results:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen_hashes:
                    normalized_semantic = 1 - (score / max_score)
                    all_results.append({
                        'doc': doc,
                        'semantic_score': normalized_semantic,
                        'bm25_score': 0,
                        'hash': content_hash
                    })
                    seen_hashes.add(content_hash)
        
        # 2. BM25 keyword search
        bm25_results = self._bm25_search(query, k=k)
        
        if bm25_results:
            max_bm25 = max(score for _, score in bm25_results) + 0.001
            for doc, score in bm25_results:
                content_hash = hash(doc.page_content[:100])
                normalized_bm25 = score / max_bm25
                
                # Check if already in results from semantic search
                found = False
                for r in all_results:
                    if r['hash'] == content_hash:
                        r['bm25_score'] = normalized_bm25
                        found = True
                        break
                
                if not found:
                    all_results.append({
                        'doc': doc,
                        'semantic_score': 0,
                        'bm25_score': normalized_bm25,
                        'hash': content_hash
                    })
        
        # 3. Calculate hybrid score
        for r in all_results:
            r['hybrid_score'] = alpha * r['semantic_score'] + (1 - alpha) * r['bm25_score']
        
        # Sort by hybrid score (higher is better)
        all_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        # Return in format compatible with existing code
        return [(r['doc'], 1 - r['hybrid_score'], 'hybrid') for r in all_results[:k]]
    
    # ========================================
    #: Confidence Scoring
    # ========================================
    
    def _calculate_confidence(self, query, retrieved_docs, cross_encoder_scores=None):
        """
        Calculate confidence score (0-100) based on multiple factors:
        - Top document relevance
        - Score consistency (gap between top docs)
        - Keyword coverage
        - Cross-encoder agreement
        """
        if not retrieved_docs:
            return 0
        
        confidence_factors = []
        
        # Factor 1: Top document score (40% weight)
        if cross_encoder_scores and len(cross_encoder_scores) > 0:
            top_score = cross_encoder_scores[0]
            # Cross-encoder scores range roughly -10 to 10
            top_confidence = min(100, max(0, (top_score + 5) * 10))
            confidence_factors.append(('top_score', top_confidence, 0.4))
        
        # Factor 2: Score consistency (20% weight)
        # If top docs have similar scores, more confident
        if cross_encoder_scores and len(cross_encoder_scores) >= 3:
            score_std = self._calculate_std(cross_encoder_scores[:3])
            consistency = max(0, 100 - score_std * 20)
            confidence_factors.append(('consistency', consistency, 0.2))
        
        # Factor 3: Keyword coverage (25% weight)
        query_words = set(self._tokenize_for_bm25(query))
        if query_words and retrieved_docs:
            top_doc_content = retrieved_docs[0].page_content.lower()
            matches = sum(1 for w in query_words if w in top_doc_content)
            coverage = (matches / len(query_words)) * 100
            confidence_factors.append(('keyword_coverage', coverage, 0.25))
        
        # Factor 4: Multiple supporting docs (15% weight)
        if cross_encoder_scores and len(cross_encoder_scores) >= 2:
            # If multiple docs score highly, more confident
            high_scorers = sum(1 for s in cross_encoder_scores[:5] if s > 0)
            support = min(100, high_scorers * 25)
            confidence_factors.append(('support', support, 0.15))
        
        # Calculate weighted average
        if not confidence_factors:
            return 50  # Default medium confidence
        
        total_weight = sum(w for _, _, w in confidence_factors)
        weighted_sum = sum(score * weight for _, score, weight in confidence_factors)
        
        final_confidence = int(weighted_sum / total_weight) if total_weight > 0 else 50
        return max(0, min(100, final_confidence))
    
    def _calculate_std(self, values):
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _auto_load_documents(self):
        """Auto-load PDFs from data folder if not already indexed"""
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER, exist_ok=True)
            return
            
        pdf_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.pdf')]
        if not pdf_files:
            return
            
        print(f"Checking {len(pdf_files)} documents in {DATA_FOLDER} for auto-loading...")
        
        # Get list of already indexed files
        indexed_files = [d.get("filename") for d in self.metadata.get("documents", [])]
        
        files_to_load = []
        for pdf_file in pdf_files:
            if pdf_file not in indexed_files:
                files_to_load.append(pdf_file)
            else:
                print(f"  • Already indexed: {pdf_file}")
                
        if not files_to_load:
            print("All documents are up to date.")
            return
            
        print(f"Found {len(files_to_load)} new documents to index...")
        
        for pdf_file in files_to_load:
            try:
                print(f"  → Indexing: {pdf_file}...")
                pdf_path = os.path.join(DATA_FOLDER, pdf_file)
                text = self._extract_pdf_text(pdf_path)
                if text:
                    self.create_vectorstore(text, pdf_file, os.path.getsize(pdf_path))
                    print(f"  ✓ Successfully loaded: {pdf_file}")
            except Exception as e:
                print(f"  ✗ Failed to load {pdf_file}: {e}")
    
    def _extract_pdf_text(self, pdf_path):
        """Extract text from PDF with special handling for calendar tables and scanned documents"""
        filename = os.path.basename(pdf_path).lower()
        is_calendar = 'kalender' in filename or 'akademik' in filename
        
        text = ""
        
        # For calendar documents, try to extract tables as markdown
        if is_calendar:
            text = self._extract_tables_as_markdown(pdf_path)
            if text and len(text.strip()) > 200:
                return text
        
        # Standard text extraction
        # Method 1: Try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception:
            pass
        
        # Method 2: Try PyMuPDF if pypdf failed or returned little text
        if len(text.strip()) < 100:
            try:
                import fitz
                doc = fitz.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
            except Exception:
                pass
        
        # Method 3: OCR for scanned documents if still not enough text
        if len(text.strip()) < 100:
            print(f"Using OCR for scanned PDF: {pdf_path}")
            text = self._extract_with_ocr(pdf_path)
        
        return text.strip()
    
    def _extract_with_ocr(self, pdf_path):
        """Extract text from scanned PDF using OCR"""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convert PDF pages to images
            print("Converting PDF to images for OCR...")
            images = convert_from_path(pdf_path, dpi=200)
            
            all_text = []
            for i, image in enumerate(images):
                print(f"  OCR processing page {i+1}/{len(images)}...")
                # Run OCR with Indonesian language support
                page_text = pytesseract.image_to_string(image, lang='ind+eng')
                if page_text.strip():
                    all_text.append(f"=== Halaman {i+1} ===\n{page_text}")
            
            return "\n\n".join(all_text)
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
    
    def _extract_tables_as_markdown(self, pdf_path):
        """Extract tables from PDF and convert to markdown format"""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num, page in enumerate(doc):
                # Get all text first
                page_text = page.get_text()
                all_text.append(f"=== Halaman {page_num + 1} ===\n{page_text}")
                
                # Try to find and extract tables
                try:
                    tables = page.find_tables()
                    for table in tables:
                        if table.row_count > 1:
                            # Convert table to markdown
                            md_table = "\n| " + " | ".join([str(cell) if cell else "" for cell in table.extract()[0]]) + " |\n"
                            md_table += "|" + "|".join(["---"] * len(table.extract()[0])) + "|\n"
                            for row in table.extract()[1:]:
                                md_table += "| " + " | ".join([str(cell) if cell else "" for cell in row]) + " |\n"
                            all_text.append(f"\n=== TABEL Halaman {page_num + 1} ===\n{md_table}")
                except Exception:
                    pass
            
            doc.close()
            return "\n\n".join(all_text)
        except Exception as e:
            print(f"Table extraction failed: {e}")
            return ""
    
    def load_metadata(self):
        try:
            if os.path.exists(METADATA_FILE):
                with open(METADATA_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"documents": [], "total_queries": 0, "last_query_at": None}
    
    def save_metadata(self):
        try:
            with open(METADATA_FILE, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def add_document_metadata(self, filename: str, size_bytes: int, chunks_count: int):
        import uuid
        # Check if already exists
        for doc in self.metadata["documents"]:
            if doc["filename"] == filename:
                return doc["id"]
        
        doc_meta = {
            "id": str(uuid.uuid4()),
            "filename": filename,
            "size_bytes": size_bytes,
            "uploaded_at": datetime.now().isoformat(),
            "status": "indexed",
            "chunks_count": chunks_count
        }
        self.metadata["documents"].append(doc_meta)
        self.save_metadata()
        return doc_meta["id"]
    
    def get_documents(self):
        return self.metadata.get("documents", [])
    
    def delete_document(self, doc_id: str):
        self.metadata["documents"] = [d for d in self.metadata["documents"] if d["id"] != doc_id]
        self.save_metadata()
        return True
    
    def get_stats(self):
        docs = self.metadata.get("documents", [])
        total_size = sum(d.get("size_bytes", 0) for d in docs)
        return {
            "total_documents": len(docs),
            "total_queries": self.metadata.get("total_queries", 0),
            "total_size_bytes": total_size,
            "last_query_at": self.metadata.get("last_query_at")
        }
    
    def increment_query_count(self, query_text: str = ""):
        """Track query for analytics"""
        self.metadata["total_queries"] = self.metadata.get("total_queries", 0) + 1
        self.metadata["last_query_at"] = datetime.now().isoformat()
        
        # Track query history (keep last 500 queries)
        if "query_history" not in self.metadata:
            self.metadata["query_history"] = []
        
        self.metadata["query_history"].append({
            "query": query_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 500 queries to avoid large files
        if len(self.metadata["query_history"]) > 500:
            self.metadata["query_history"] = self.metadata["query_history"][-500:]
        
        self.save_metadata()

    def load_existing_vectorstore(self):
        try:
            if os.path.exists(FAISS_INDEX_PATH) and os.path.isdir(FAISS_INDEX_PATH):
                return FAISS.load_local(
                    folder_path=FAISS_INDEX_PATH,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
        except Exception:
            pass
        return None
    
    def refresh_vectorstore(self):
        self.vectorstore = self.load_existing_vectorstore()
        return self.vectorstore is not None

    def create_vectorstore(self, text, filename="unknown", file_size=0):
        """
        Membuat vector store dengan Pasal-aware chunking.
        Setiap Pasal/artikel dijaga agar tetap utuh dalam 1 chunk.
        """
        try:
            # Preprocess text
            text = self._preprocess_text(text)
            
            #: Pasal-aware semantic chunking
            chunks = self._pasal_aware_chunking(text, filename)
            
            # Process chunks with rich metadata
            processed_chunks = []
            for chunk_data in chunks:
                chunk = chunk_data['content']
                chunk = re.sub(r'\s+', ' ', chunk).strip()
                
                if len(chunk) > 30:
                    # Build source info with pasal reference
                    source_info = f"[Sumber: {filename}"
                    if chunk_data.get('pasal'):
                        source_info += f", {chunk_data['pasal']}"
                    if chunk_data.get('bab'):
                        source_info += f", {chunk_data['bab']}"
                    source_info += "]"
                    
                    processed_chunks.append(f"{source_info}\n{chunk}")
            
            print(f"  → Created {len(processed_chunks)} chunks from {filename}")
            
            if self.vectorstore:
                self.vectorstore.add_texts(texts=processed_chunks)
            else:
                self.vectorstore = FAISS.from_texts(texts=processed_chunks, embedding=self.embeddings)
            
            self.vectorstore.save_local(FAISS_INDEX_PATH)
            self.add_document_metadata(filename, file_size, len(processed_chunks))
            
            return True
        except Exception as e:
            print(f"Error creating vectorstore: {e}")
            return False
    
    def _pasal_aware_chunking(self, text, filename):
        """
        Chunking yang menjaga setiap Pasal tetap utuh.
        Untuk dokumen peraturan, setiap Pasal menjadi 1 chunk.
        Untuk dokumen lain, gunakan semantic chunking.
        """
        chunks = []
        
        # Detect if this is a regulatory document
        is_regulation = 'peraturan' in filename.lower() or 'rektor' in filename.lower()
        is_calendar = 'kalender' in filename.lower()
        
        if is_regulation:
            # Split by Pasal
            pasal_pattern = r'(Pasal\s+\d+.*?)(?=Pasal\s+\d+|BAB\s+[IVXLCDM]+|$)'
            pasal_matches = re.findall(pasal_pattern, text, re.DOTALL | re.IGNORECASE)
            
            # Also extract BAB headers
            bab_pattern = r'(BAB\s+[IVXLCDM]+[^\n]*)'
            current_bab = ""
            
            for match in re.finditer(bab_pattern, text, re.IGNORECASE):
                current_bab = match.group(1).strip()
            
            for pasal_text in pasal_matches:
                pasal_text = pasal_text.strip()
                if len(pasal_text) > 50:
                    # Extract pasal number
                    pasal_match = re.search(r'Pasal\s+(\d+)', pasal_text, re.IGNORECASE)
                    pasal_num = f"Pasal {pasal_match.group(1)}" if pasal_match else ""
                    
                    # If pasal is too long, split by ayat
                    if len(pasal_text) > 1500:
                        ayat_chunks = self._split_pasal_by_ayat(pasal_text, pasal_num)
                        chunks.extend(ayat_chunks)
                    else:
                        chunks.append({
                            'content': pasal_text,
                            'pasal': pasal_num,
                            'bab': current_bab,
                            'type': 'pasal'
                        })
            
            # If no pasals found, fallback to regular chunking
            if not chunks:
                chunks = self._fallback_chunking(text)
        
        elif is_calendar:
            # For calendar, chunk by table/section
            chunks = self._calendar_chunking(text)
        
        else:
            # Regular semantic chunking for other documents
            chunks = self._fallback_chunking(text)
        
        return chunks
    
    def _split_pasal_by_ayat(self, pasal_text, pasal_num):
        """Split a long Pasal into individual ayat chunks"""
        chunks = []
        
        # Pattern for ayat: (1), (2), etc.
        ayat_pattern = r'(\(\d+\)[^(]*?)(?=\(\d+\)|$)'
        ayat_matches = re.findall(ayat_pattern, pasal_text, re.DOTALL)
        
        if ayat_matches and len(ayat_matches) > 1:
            # Add header (everything before first ayat)
            header_match = re.match(r'(Pasal\s+\d+[^\(]*)', pasal_text)
            header = header_match.group(1).strip() if header_match else ""
            
            for ayat_text in ayat_matches:
                ayat_text = ayat_text.strip()
                if len(ayat_text) > 30:
                    # Extract ayat number
                    ayat_match = re.search(r'\((\d+)\)', ayat_text)
                    ayat_num = f"Ayat {ayat_match.group(1)}" if ayat_match else ""
                    
                    chunks.append({
                        'content': f"{header}\n{ayat_text}" if header else ayat_text,
                        'pasal': f"{pasal_num} {ayat_num}".strip(),
                        'bab': '',
                        'type': 'ayat'
                    })
        else:
            # Can't split by ayat, keep as one chunk
            chunks.append({
                'content': pasal_text,
                'pasal': pasal_num,
                'bab': '',
                'type': 'pasal'
            })
        
        return chunks
    
    def _calendar_chunking(self, text):
        """Special chunking for calendar documents - by event/row"""
        chunks = []
        
        # Split by lines and group related content
        lines = text.split('\n')
        current_chunk = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) > 30:
                        chunks.append({
                            'content': chunk_text,
                            'pasal': '',
                            'bab': 'Kalender Akademik',
                            'type': 'calendar'
                        })
                    current_chunk = []
            else:
                current_chunk.append(line)
                # If chunk is getting long, save it
                if len('\n'.join(current_chunk)) > 500:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'pasal': '',
                        'bab': 'Kalender Akademik',
                        'type': 'calendar'
                    })
                    current_chunk = []
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > 30:
                chunks.append({
                    'content': chunk_text,
                    'pasal': '',
                    'bab': 'Kalender Akademik',
                    'type': 'calendar'
                })
        
        return chunks if chunks else self._fallback_chunking(text)
    
    def _fallback_chunking(self, text):
        """Fallback chunking using RecursiveCharacterTextSplitter"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=150,
            length_function=len,
            separators=["Pasal ", "\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
        )
        raw_chunks = text_splitter.split_text(text)
        
        chunks = []
        for chunk in raw_chunks:
            if len(chunk) > 30:
                pasal_refs = self._extract_pasal_refs(chunk)
                chunks.append({
                    'content': chunk,
                    'pasal': pasal_refs,
                    'bab': '',
                    'type': 'general'
                })
        
        return chunks

    def _preprocess_text(self, text):
        """Clean and normalize text while preserving structure"""
        # Normalize whitespace but keep paragraph breaks
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = re.sub(r'[ \t]+', ' ', line).strip()
            if line:
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    def _extract_pasal_refs(self, text):
        """Extract Pasal/Ayat references from text"""
        patterns = [
            r'Pasal\s+\d+(?:\s+ayat\s+\([^)]+\))?',
            r'BAB\s+[IVXLCDM]+',
            r'Bagian\s+(?:Ke)?[a-zA-Z]+',
        ]
        refs = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            refs.extend(matches[:2])
        return ', '.join(refs[:2]) if refs else ""

    def _call_llm(self, messages, stream=False, max_retries=2):
        models = [self.llm_model, self.fallback_model]
        for model in models:
            for attempt in range(max_retries):
                try:
                    return self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.1,
                        max_tokens=1500,
                        top_p=0.95,
                        stream=stream
                    )
                except Exception as e:
                    if "rate_limit" in str(e).lower() or "429" in str(e):
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        break
                    raise e
        raise Exception("Semua model sedang sibuk. Coba lagi.")

    def query_stream(self, question, history=None):
        """
       Enhanced RAG query dengan:
        - Hybrid Search (Semantic + BM25)
        - Cross-Encoder Neural Re-ranking
        - Confidence Scoring
        - Anti-hallucination prompting
        - Conversation Memory ()
        """
        self.refresh_vectorstore()
        
        if not self.vectorstore:
            yield {"response": "Knowledge base belum tersedia. Silakan upload dokumen di halaman Admin, atau letakkan file PDF di folder 'data/'."}
            return
         
        self.increment_query_count(question)
        
        # Apply synonym mapping early for better retrieval
        question_expanded = self._apply_synonym_mapping(question)
        
        # ========================================
        # Check Response Cache
        # ========================================
        import hashlib
        from time import time
        
        query_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
        
        if query_hash in self.response_cache:
            cached = self.response_cache[query_hash]
            # Check if cache is still valid (within TTL)
            if time() - cached["timestamp"] < self.cache_ttl:
                self.cache_stats["hits"] += 1
                print(f"  ⚡ CACHE HIT for: {question[:50]}...")
                # Return cached response
                yield {"confidence": cached["confidence"]}
                yield {"citations": cached["citations"]}
                for char in cached["response"]:
                    yield {"response": char}
                if cached.get("related_questions"):
                    yield {"related_questions": cached["related_questions"]}
                return
            else:
                # Cache expired, remove it
                del self.response_cache[query_hash]
        
        self.cache_stats["misses"] += 1
        
        # ========================================
        # STAGE 1: Multi-Query Retrieval
        # ========================================
        try:
            hybrid_results = self._multi_query_retrieval(question, k=50, alpha=0.7)
        except Exception as e:
            print(f"  ⚠️ Multi-query retrieval failed, falling back to hybrid: {e}")
            try:
                hybrid_results = self._hybrid_search(question_expanded, k=30, alpha=0.7)
            except Exception as e2:
                print(f"  ⚠️ Hybrid search also failed: {e2}")
                # Fallback to semantic only
                hybrid_results = [(doc, score, "semantic") 
                                 for doc, score in self.vectorstore.similarity_search_with_score(question_expanded, k=30)]
        
        # ========================================
        # STAGE 2: Cross-Encoder Neural Re-ranking
        # ========================================
        reranked_docs = self._cross_encoder_rerank(question, hybrid_results, top_k=12)
        
        # Extract cross-encoder scores for confidence calculation
        cross_encoder_scores = [doc[3] for doc in reranked_docs] if reranked_docs else []
        
        # ========================================
        # STAGE 3: Calculate Confidence Score
        # ========================================
        relevant_doc_contents = [doc[0] for doc in reranked_docs]
        confidence = self._calculate_confidence(question, relevant_doc_contents, cross_encoder_scores)
        
        # Yield confidence score to frontend
        yield {"confidence": confidence}
        
        # ========================================
        # STAGE 4: Build Context
        # ========================================
        context_parts = []
        for i, (doc, score, strategy, ce_score) in enumerate(reranked_docs, 1):
            # Include relevance indicator for debugging
            context_parts.append(f"=== BAGIAN {i} (skor: {ce_score:.2f}) ===\n{doc.page_content}")
        context = "\n\n".join(context_parts)
        
        # Limit context size but keep complete chunks
        if len(context) > 10000:
            context = context[:10000]
        
        # Citations for UI
        citations = []
        for doc, _, _, _ in reranked_docs[:3]:
            citation = doc.page_content[:60].replace('[Sumber:', '').replace(']', '')
            citations.append(citation + "...")
        yield {"citations": citations}
        
        # ========================================
        # STAGE 5: Enhanced Anti-Hallucination Prompt
        # ========================================
        system_prompt = """Anda adalah AKASIA, Asisten Akademik ramah untuk Jurusan Ilmu Komputer.
Anda berbicara dengan sopan dan membantu seperti Customer Service yang baik.

TUGAS UTAMA:
Bantu mahasiswa dengan menjawab pertanyaan akademik berdasarkan informasi yang tersedia.

CARA MENJAWAB:
1. Cari informasi yang relevan dari konteks yang diberikan
2. Jawab LANGSUNG tanpa kata pembuka seperti "Berdasarkan informasi..." atau "Saya menemukan bahwa..."
3. Cukup berikan jawaban singkat + sumber di akhir
4. Maksimal 2 kalimat saja

CONTOH FORMAT JAWABAN YANG BENAR:
"Masa studi maksimal S1 adalah 7 tahun akademik. [Sumber: Pasal 44]"

FORMAT YANG SALAH (terlalu panjang):
"Berdasarkan informasi yang tersedia, saya menemukan bahwa masa studi maksimal untuk Program Sarjana (S1) adalah... Jadi, jawaban untuk pertanyaan mahasiswa adalah..."

PEMETAAN SEMESTER:
- Semester Gasal 2025.1 = SEMESTER GASAL tahun 2025 (mulai Agustus 2025)
- Semester Genap 2025.2 = SEMESTER GENAP tahun 2026 (mulai Februari 2026)
- Semester Antara 2025.3 = SEMESTER ANTARA tahun 2026 (mulai Juli 2026)

CARA BACA KALENDER AKADEMIK:
- Format: "No | Kegiatan | Tanggal Mulai | Tanggal Selesai"
- Jika ada 2 tanggal berurutan = periode mulai dan selesai

PEMETAAN ISTILAH:
- S1 = "program sarjana"
- S2 = "program magister"
- S3 = "program doktor"
- D3 = "diploma 3"
- D4 = "diploma empat" / "sarjana terapan"
- "masa studi maksimal" = "ditempuh paling lama"

JIKA INFORMASI TIDAK DITEMUKAN:
Gunakan respons yang ramah seperti:
"Mohon maaf, saya belum memiliki informasi mengenai [topik] saat ini. 🙏

Saran untuk Anda:
• Hubungi Bagian Akademik ILKOM di jam kerja
• Kunjungi website resmi ILKOM: fmipa.uho.ac.id/ilmukomputer
• Tanyakan ke Jurusan/Program Studi Anda

Apakah ada pertanyaan lain yang bisa saya bantu?"

PENTING: 
- Jangan mengarang informasi yang tidak ada
- Gunakan bahasa yang sopan dan ramah
- Jangan gunakan istilah teknis seperti "REFERENSI" atau "dokumen"
- Bersikaplah seperti teman yang membantu"""

        prompt = f"""INFORMASI AKADEMIK ILKOM:
{context}

---
PERTANYAAN MAHASISWA: {question}

Instruksi: Bantu mahasiswa dengan menjawab pertanyaannya. Jika ada informasi yang relevan, berikan jawaban yang jelas. Jika tidak ada, berikan respons ramah dengan saran yang membantu."""

# Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Include conversation history for context (max 6 turns)
        if history:
            for role, content in history[-6:]:
                if role == "user":
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": "assistant", "content": content})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self._call_llm(messages, stream=True)
            full_response = ""  # Collect for caching
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield {"response": content}
            
            # Generate related questions after response
            related = self._generate_related_questions(question, reranked_docs)
            if related:
                yield {"related_questions": related}
            
            # Save to cache
            # Evict oldest if cache full
            if len(self.response_cache) >= self.cache_max_size:
                oldest_key = min(self.response_cache, key=lambda k: self.response_cache[k]["timestamp"])
                del self.response_cache[oldest_key]
            
            self.response_cache[query_hash] = {
                "response": full_response,
                "citations": citations,
                "confidence": confidence,
                "related_questions": related,
                "timestamp": time()
            }
                
        except Exception as e:
            yield {"response": f"Error: {str(e)}"}
    
    def _generate_related_questions(self, question, docs, max_questions=4):
        """
        Generate related questions based on current query and documents.
        Uses keywords and document topics to suggest follow-up questions.
        """
        question_lower = question.lower()
        related = []
        
        # Define topic-based related questions
        topic_questions = {
            "masa studi": [
                "Apa sanksi jika melebihi masa studi maksimal?",
                "Bagaimana cara mengajukan perpanjangan masa studi?",
                "Berapa SKS minimum per semester?"
            ],
            "sks": [
                "Berapa beban SKS maksimal per semester?",
                "Bagaimana konversi nilai ke huruf?",
                "Apa syarat mengambil SKS maksimal?"
            ],
            "wisuda": [
                "Kapan jadwal pendaftaran wisuda?",
                "Apa saja berkas yang diperlukan untuk wisuda?",
                "Bagaimana cara mengecek status kelulusan?"
            ],
            "cuti": [
                "Berapa lama maksimal cuti akademik?",
                "Apa saja syarat mengajukan cuti?",
                "Bagaimana prosedur aktivasi setelah cuti?"
            ],
            "ipk": [
                "Berapa IPK minimum untuk lulus cum laude?",
                "Bagaimana cara menghitung IPK?",
                "Apa predikat kelulusan berdasarkan IPK?"
            ],
            "krs": [
                "Kapan jadwal pengisian KRS?",
                "Bagaimana cara mengubah KRS?",
                "Berapa batas waktu pembatalan mata kuliah?"
            ],
            "jadwal": [
                "Kapan ujian akhir semester?",
                "Kapan libur semester genap?",
                "Kapan perkuliahan dimulai?"
            ],
            "syarat": [
                "Apa syarat mengikuti ujian skripsi?",
                "Apa syarat magang/KKN?",
                "Apa syarat pindah jurusan?"
            ]
        }
        
        # Find matching topic
        for topic, questions in topic_questions.items():
            if topic in question_lower:
                # Add questions that are different from original
                for q in questions:
                    if q.lower() != question_lower and len(related) < max_questions:
                        related.append(q)
        
        # If no specific topic match, add general academic questions
        if len(related) < 2:
            general_questions = [
                "Apa syarat kelulusan program S1?",
                "Bagaimana prosedur pengajuan surat keterangan?",
                "Siapa yang bisa dihubungi untuk konsultasi akademik?"
            ]
            for q in general_questions:
                if len(related) < max_questions:
                    related.append(q)
        
        return related[:max_questions]
    
    def _rerank_documents(self, question, docs):
        """
        Re-rank documents based on relevance signals
        Uses keyword overlap and position weighting
        """
        question_lower = question.lower()
        question_words = set(re.findall(r'\b\w+\b', question_lower))
        
        # Remove stopwords
        stopwords = {'apa', 'berapa', 'kapan', 'dimana', 'bagaimana', 'siapa', 
                     'yang', 'dan', 'atau', 'untuk', 'dengan', 'ke', 'di', 'dari',
                     'adalah', 'ini', 'itu', 'ada', 'tidak', 'bisa', 'dapat'}
        question_words = question_words - stopwords
        
        reranked = []
        for doc, score, strategy in docs:
            content_lower = doc.page_content.lower()
            content_words = set(re.findall(r'\b\w+\b', content_lower))
            
            # Calculate relevance score
            overlap = len(question_words & content_words)
            overlap_ratio = overlap / max(len(question_words), 1)
            
            # Bonus for exact phrase match
            phrase_bonus = 0.2 if question_lower[:20] in content_lower else 0
            
            # Bonus for Pasal reference in question matching content
            pasal_match = re.search(r'pasal\s*(\d+)', question_lower)
            pasal_bonus = 0.3 if pasal_match and f"pasal {pasal_match.group(1)}" in content_lower else 0
            
            # Calculate final relevance (lower is better for FAISS scores)
            relevance = overlap_ratio + phrase_bonus + pasal_bonus
            adjusted_score = score * (1 - relevance * 0.3)  # Boost relevant docs
            
            reranked.append((doc, adjusted_score, strategy, relevance))
        
        # Sort by adjusted score (lower is better)
        reranked.sort(key=lambda x: x[1])
        return reranked

    def _apply_synonym_mapping(self, question):
        """
        Expand abbreviations dan istilah untuk retrieval lebih baik.
        Menambahkan variasi kata kunci untuk meningkatkan kemungkinan match.
        """
        # Direct replacements
        mappings = {
            r'\bS1\b': 'S1 sarjana program sarjana',
            r'\bS2\b': 'S2 magister program magister pascasarjana',
            r'\bS3\b': 'S3 doktor program doktor',
            r'\bD3\b': 'D3 diploma tiga vokasi',
            r'\bD4\b': 'D4 diploma empat sarjana terapan',
            r'\bKRS\b': 'KRS kartu rencana studi pengisian',
            r'\bKHS\b': 'KHS kartu hasil studi',
            r'\bUKT\b': 'UKT uang kuliah tunggal SPP pembayaran',
            r'\bSPP\b': 'SPP UKT uang kuliah tunggal pembayaran',
            r'\bIPK\b': 'IPK indeks prestasi kumulatif',
            r'\bIPS\b': 'IPS indeks prestasi semester beban studi sks Pasal 21',
            r'\bSKS\b': 'SKS satuan kredit semester beban studi',
            r'\bUTS\b': 'UTS ujian tengah semester',
            r'\bUAS\b': 'UAS ujian akhir semester',
            r'\bKKN\b': 'KKN kuliah kerja nyata',
            r'\bTA\b': 'tugas akhir skripsi',
            r'\bDO\b': 'drop out dikeluarkan',
            r'\bcuti\b': 'cuti akademik izin tidak aktif',
            r'\bwisuda\b': 'wisuda kelulusan yudisium',
            r'\blulus\b': 'lulus kelulusan yudisium predikat',
            #: Calendar/semester terms
            r'\bgasal\b': 'gasal ganjil semester I',
            r'\bgenap\b': 'genap semester II',
            r'\bongoing\b': 'ongoing mahasiswa lama aktif',
            r'\bbayar\b': 'bayar pembayaran registrasi',
            r'\bpembayaran\b': 'pembayaran bayar registrasi UKT SPP',
            r'\b2025\.1\b': '2025.1 semester gasal 2025',
            r'\b2025\.2\b': '2025.2 semester genap 2026',
            r'\b2025\.3\b': '2025.3 semester antara 2026',
        }
        result = question
        for pattern, replacement in mappings.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Add key terms based on question type
        q_lower = question.lower()
        additions = []
        
        if 'masa studi' in q_lower or 'berapa lama' in q_lower:
            additions.append('beban studi tahun akademik sks')
        if 'syarat' in q_lower or 'ketentuan' in q_lower:
            additions.append('pasal peraturan')
        if 'nilai' in q_lower or 'ipk' in q_lower:
            additions.append('indeks prestasi huruf mutu')
        if 'jadwal' in q_lower or 'kapan' in q_lower:
            additions.append('tanggal kalender akademik jadwal')
        # Payment-related additions
        if 'pembayaran' in q_lower or 'bayar' in q_lower or 'ukt' in q_lower or 'spp' in q_lower:
            additions.append('registrasi mahasiswa ongoing')
            
        if additions:
            result = result + ' ' + ' '.join(additions)
        
        return result

    def _extract_keywords(self, text):
        """Extract meaningful keywords"""
        stopwords = {'apa', 'adalah', 'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan',
                     'pada', 'ini', 'itu', 'atau', 'juga', 'saya', 'kamu', 'dia', 'mereka',
                     'bagaimana', 'kapan', 'dimana', 'siapa', 'mengapa', 'berapa', 'apakah',
                     'bisa', 'dapat', 'akan', 'sudah', 'belum', 'tidak', 'ada', 'harus',
                     'mau', 'ingin', 'tolong', 'mohon', 'coba', 'jelaskan', 'sebutkan',
                     'jika', 'bila', 'ketika', 'saat', 'agar', 'supaya', 'sehingga'}
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [w for w in words if w not in stopwords and len(w) > 2]

    # ========================================
    # Multi-Query Retrieval for Higher Accuracy
    # ========================================
    
    def _generate_query_variations(self, question):
        """
        Generate multiple query variations for better retrieval.
        Returns 3 variations: original expanded, rephrased, keyword-focused.
        """
        variations = []
        q_lower = question.lower()
        
        # Variation 1: Original with synonym expansion (already done)
        variations.append(self._apply_synonym_mapping(question))
        
        # Variation 2: Rephrased formal academic
        rephrase_patterns = {
            r'berapa lama': 'durasi waktu',
            r'berapa': 'jumlah total',
            r'apa saja': 'syarat ketentuan',
            r'bagaimana': 'prosedur cara mekanisme',
            r'kapan': 'jadwal tanggal waktu',
            r'apa itu': 'definisi pengertian',
            r'syarat': 'persyaratan ketentuan kriteria',
            r'cara': 'prosedur langkah mekanisme',
            r'biaya': 'tarif pembayaran nominal',
        }
        
        rephrased = question
        for pattern, replacement in rephrase_patterns.items():
            if re.search(pattern, q_lower):
                rephrased = re.sub(pattern, replacement, rephrased, flags=re.IGNORECASE)
        
        if rephrased != question:
            variations.append(self._apply_synonym_mapping(rephrased))
        
        # Variation 3: Keyword extraction + context
        keywords = self._extract_keywords(question)
        if keywords:
            # Add academic context keywords
            context_additions = []
            if any(k in ['lulus', 'kelulusan', 'wisuda', 'yudisium'] for k in keywords):
                context_additions.extend(['predikat', 'IPK', 'SKS', 'syarat'])
            if any(k in ['studi', 'kuliah', 'semester'] for k in keywords):
                context_additions.extend(['beban', 'akademik', 'tahun'])
            if any(k in ['cuti', 'izin', 'libur'] for k in keywords):
                context_additions.extend(['akademik', 'prosedur', 'permohonan'])
            if any(k in ['nilai', 'ipk', 'ips'] for k in keywords):
                context_additions.extend(['huruf', 'mutu', 'prestasi'])
                
            keyword_query = ' '.join(keywords + context_additions[:4])
            variations.append(keyword_query)
        
        # Ensure we have unique variations
        unique_variations = list(dict.fromkeys(variations))
        return unique_variations[:3]  # Max 3 variations
    
    def _multi_query_retrieval(self, question, k=30, alpha=0.7):
        """
        Retrieve documents using multiple query variations.
        Merges results from all variations and deduplicates.
        """
        query_variations = self._generate_query_variations(question)
        print(f"  🔄 Multi-query retrieval with {len(query_variations)} variations")
        
        all_results = {}  # hash -> (doc, best_score, strategy)
        
        for i, query in enumerate(query_variations):
            try:
                results = self._hybrid_search(query, k=k, alpha=alpha)
                
                for doc, score, strategy in results:
                    content_hash = hash(doc.page_content[:100])
                    
                    if content_hash not in all_results:
                        all_results[content_hash] = (doc, score, strategy)
                    else:
                        # Keep the better score (lower is better in our normalized scheme)
                        existing_score = all_results[content_hash][1]
                        if score < existing_score:
                            all_results[content_hash] = (doc, score, strategy)
                            
            except Exception as e:
                print(f"  ⚠️ Query variation {i+1} failed: {e}")
                continue
        
        # Sort by score and return top k
        sorted_results = sorted(all_results.values(), key=lambda x: x[1])
        print(f"  ✓ Retrieved {len(sorted_results)} unique documents from multi-query")
        
        return sorted_results[:k]

    def _extract_entities(self, text):
        """Extract important entities like numbers, dates, proper nouns"""
        entities = []
        
        # Numbers with context
        nums = re.findall(r'\d+(?:[.,]\d+)?(?:\s*(?:tahun|semester|sks|persen|%|bulan|minggu|hari))?', text, re.IGNORECASE)
        entities.extend(nums)
        
        # Dates
        dates = re.findall(r'\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4}', text, re.IGNORECASE)
        entities.extend(dates)
        
        # Academic terms
        terms = re.findall(r'(?:IPK|IPS|SKS|KRS|UKT|SPP|S1|S2|S3|D3|D4)\b', text, re.IGNORECASE)
        entities.extend(terms)
        
        # Proper nouns (capitalized words)
        caps = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
        entities.extend(caps[:3])
        
        return list(set(entities))[:10]

    def _get_regulatory_terms(self, question):
        """Generate specific regulatory search terms based on question"""
        terms = []
        q = question.lower()
        
        # === KALENDER AKADEMIK ===
        if any(w in q for w in ['kapan', 'jadwal', 'tanggal', 'periode', 'semester']):
            terms.append("jadwal pembayaran UKT SPP registrasi")
            terms.append("pengisian KRS online SIAKAD")
            terms.append("masa perkuliahan praktikum")
        
        if any(w in q for w in ['ukt', 'spp', 'pembayaran', 'registrasi']):
            terms.append("pembayaran UKT SPP semester gasal genap")
            terms.append("batas akhir registrasi ulang")
        
        if any(w in q for w in ['uts', 'uas', 'ujian tengah', 'ujian akhir']):
            terms.append("ujian tengah semester UTS")
            terms.append("ujian akhir semester UAS")
        
        if any(w in q for w in ['wisuda', 'yudisium', 'dies natalis']):
            terms.append("pelaksanaan wisuda periode")
            terms.append("dies natalis upacara akademik")
        
        if any(w in q for w in ['kkn', 'kuliah kerja nyata', 'magang']):
            terms.append("KKN Kuliah Kerja Nyata batch")
            terms.append("magang praktik kerja lapangan")
        
        if any(w in q for w in ['snbp', 'snbt', 'utbk', 'smmuho', 'seleksi']):
            terms.append("SNBP SNBT UTBK seleksi masuk")
            terms.append("SMMUHO pendaftaran ujian")
        
        # === MASA STUDI & BEBAN SKS ===
        if any(w in q for w in ['masa studi', 'lama studi', 'beban studi', 'beban']):
            terms.append("beban studi program ditempuh paling lama tahun")
            terms.append("Pasal 44 sarjana 144 sks 7 tahun")
            terms.append("Pasal 43 diploma 108 sks 5 tahun")
        
        if any(w in q for w in ['d3', 'diploma']):
            terms.append("Pasal 43 diploma 3 108 sks 5 tahun")
        
        if any(w in q for w in ['s1', 'sarjana']):
            terms.append("Pasal 44 sarjana 144 sks 7 tahun akademik")
        
        if any(w in q for w in ['s2', 'magister']):
            terms.append("Pasal 46 magister 36 sks 4 tahun")
        
        if any(w in q for w in ['s3', 'doktor']):
            terms.append("Pasal 47 doktor 42 sks 7 tahun disertasi")
        
        if any(w in q for w in ['ips', 'sks', 'diprogramkan', 'diprogram', 'ambil']):
            terms.append("IPS Jumlah sks maksimal diprogramkan")
            terms.append("3,01 4,00 24 sks 2,75 22 sks 2,51 20 sks")
        
        if any(w in q for w in ['1 sks', 'bobot sks', 'nilai sks']):
            terms.append("1 sks tatap muka praktikum per minggu")
        
        # === PENILAIAN & RUMUS ===
        if any(w in q for w in ['nilai', 'huruf', 'rentang', 'konversi']):
            terms.append("nilai huruf A B C D E konversi angka")
            terms.append("rentang nilai 81 100 66 80 56 65")
        
        if any(w in q for w in ['rumus', 'nilai akhir', 'na', 'komponen']):
            terms.append("rumus nilai akhir NA tugas UTS UAS")
            terms.append("komponen penilaian praktikum")
        
        if any(w in q for w in ['kehadiran', 'hadir', 'absen', 'persentase']):
            terms.append("kehadiran minimal 75 persen ujian")
            terms.append("syarat mengikuti ujian mahasiswa")
        
        # === KELULUSAN & PREDIKAT ===
        if any(w in q for w in ['lulus', 'kelulusan', 'syarat lulus']):
            terms.append("syarat kelulusan IPK minimal")
            terms.append("dinyatakan lulus program")
        
        if any(w in q for w in ['predikat', 'cum laude', 'pujian', 'memuaskan']):
            terms.append("predikat kelulusan cum laude dengan pujian")
            terms.append("sangat memuaskan memuaskan IPK")
        
        if any(w in q for w in ['wisudawan', 'terbaik']):
            terms.append("wisudawan terbaik IPK tertinggi masa studi")
        
        # === ADMINISTRASI & CUTI ===
        if any(w in q for w in ['cuti', 'akademik', 'berhenti sementara']):
            terms.append("Pasal 96 cuti akademik syarat")
            terms.append("maksimum cuti semester berturutan")
        
        if any(w in q for w in ['pindah', 'alih program', 'transfer']):
            terms.append("pindah kuliah antar program studi")
            terms.append("syarat IPK pindah semester")
        
        if any(w in q for w in ['daftar ulang', 'registrasi', 'non aktif']):
            terms.append("registrasi ulang status mahasiswa")
            terms.append("non aktif dua semester berturut")
        
        if any(w in q for w in ['ktm', 'kartu tanda mahasiswa']):
            terms.append("Pasal 109 KTM hilang surat keterangan")
        
        # === SKRIPSI, TESIS, DISERTASI ===
        if any(w in q for w in ['skripsi', 'tugas akhir', 'ta']):
            terms.append("skripsi tugas akhir syarat")
            terms.append("masa penulisan skripsi maksimal")
        
        if any(w in q for w in ['tesis']):
            terms.append("tesis magister S2 syarat")
        
        if any(w in q for w in ['disertasi']):
            terms.append("disertasi doktor S3 promotor")
        
        if any(w in q for w in ['toefl', 'bahasa inggris']):
            terms.append("TOEFL skor minimal ujian akhir")
        
        if any(w in q for w in ['publikasi', 'jurnal']):
            terms.append("publikasi jurnal syarat kelulusan")
        
        if any(w in q for w in ['pembimbing', 'promotor', 'dosen']):
            terms.append("pembimbing utama skripsi promotor")
            terms.append("syarat jabatan fungsional")
        
        # === EVALUASI & DROP OUT ===
        if any(w in q for w in ['evaluasi', 'do', 'drop out', 'gagal studi']):
            terms.append("evaluasi program mahasiswa DO")
            terms.append("gagal studi dikeluarkan")
        
        if any(w in q for w in ['perpanjangan', 'masa studi']):
            terms.append("perpanjangan masa studi syarat")
        
        if any(w in q for w in ['skorsing']):
            terms.append("masa skorsing dihitung")
        
        # === ETIKA & SANKSI ===
        if any(w in q for w in ['plagiat', 'sanksi', 'pelanggaran']):
            terms.append("sanksi plagiat pelanggaran")
            terms.append("teguran skorsing dikeluarkan")
        
        if any(w in q for w in ['larangan', 'dilarang', 'tidak boleh']):
            terms.append("larangan mahasiswa kampus")
        
        if any(w in q for w in ['demonstrasi', 'demo', 'unjuk rasa']):
            terms.append("demonstrasi radius izin tertulis")
        
        if any(w in q for w in ['narkoba', 'obat terlarang']):
            terms.append("narkoba sanksi berat dikeluarkan")
        
        if any(w in q for w in ['pemalsuan', 'palsu', 'tanda tangan']):
            terms.append("memalsukan tanda tangan sanksi")
        
        if any(w in q for w in ['skpi', 'surat keterangan']):
            terms.append("SKPI Surat Keterangan Pendamping Ijazah")
        
        if any(w in q for w in ['gelar', 'dicabut']):
            terms.append("gelar akademik dicabut tidak sah")
        
        if any(w in q for w in ['dosen pa', 'pembimbing akademik']):
            terms.append("dosen pembimbing akademik PA kewajiban")
        
        return terms