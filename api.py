"""
============================================
AKASIA v1.0 - API Backend Server
============================================
Asisten Akademik Berbasis AI untuk ILKOM

File ini berisi:
- Endpoint API untuk chat (/api/chat)
- Endpoint untuk upload dokumen (/api/upload)
- Endpoint untuk manajemen dokumen (/api/documents)
- Endpoint untuk statistik (/api/stats)

Jalankan dengan: python api.py
Server akan berjalan di http://localhost:8000
============================================
"""

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Depends,
    Header
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from rag_engine import RAGEngine
from typing import List
from datetime import datetime, timedelta
import uvicorn
import shutil
import os
import json
import asyncio
from app import extract_text_from_pdf
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# Inisialisasi FastAPI dengan metadata
app = FastAPI(
    title="AKASIA API",
    description="Asisten Akademik Berbasis AI untuk Jurusan Ilmu Komputer",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://akasia.kloudbox.my.id",
        "http://akasia.kloudbox.my.id"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RAGEngine()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

class ChatRequest(BaseModel):
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

def verify_admin(
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token tidak ditemukan"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Format token salah"
        )

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Akses ditolak"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token tidak valid"
        )
    
@app.post("/api/admin/login")
async def admin_login(req: LoginRequest):

    if (
        req.username != ADMIN_USERNAME
        or
        req.password != ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah"
        )

    token = jwt.encode(
        {
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=12)
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {
        "status": "success",
        "token": token
    }

@app.get("/api/admin/me")
async def admin_me(
    admin=Depends(verify_admin)
):
    return {
        "authenticated": True,
        "role": "admin"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "ILKOM Academic Chatbot API is running"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    async def generate():
        # Always reload vectorstore to ensure latest documents are used
        engine.vectorstore = engine.load_existing_vectorstore()
        if not engine.vectorstore:
            yield json.dumps({"response": "Knowledge base belum tersedia. Silakan upload dokumen terlebih dahulu di halaman Admin."}) + "\n"
            return

        for chunk in engine.query_stream(request.message):
             yield json.dumps(chunk) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...), admin=Depends(verify_admin)):
    all_text = ""
    processed_count = 0
    total_size = 0
    filenames = []
    
    for file in files:
        try:
            # Save temp file
            temp_filename = f"temp_{file.filename}"
            with open(temp_filename, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
                file_size = len(content)
                total_size += file_size
                
            class MockFile:
                def __init__(self, path, original_name, size):
                    with open(path, "rb") as f:
                        self.data = f.read()
                    self.name = original_name
                    self.size = size
                def getvalue(self):
                    return self.data
            
            mock_file = MockFile(temp_filename, file.filename, file_size)
            text = extract_text_from_pdf(mock_file)
            
            if text:
                all_text += f"\n\n=== {file.filename} ===\n\n{text}"
                processed_count += 1
                filenames.append(file.filename)
                
            os.remove(temp_filename)
            
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            continue

    if all_text:
        # Pass metadata to create_vectorstore
        combined_filename = ", ".join(filenames) if len(filenames) > 1 else filenames[0]
        success = engine.create_vectorstore(all_text, combined_filename, total_size)
        if success:
            return {
                "status": "success", 
                "processed": processed_count,
                "filenames": filenames,
                "total_size": total_size
            }
    
    raise HTTPException(status_code=500, detail="Failed to process documents")

@app.get("/api/documents")
async def get_documents(admin=Depends(verify_admin)):
    """Get list of all uploaded documents"""
    documents = engine.get_documents()
    return {"documents": documents}

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, admin=Depends(verify_admin)):
    """Delete a document by ID"""
    success = engine.delete_document(doc_id)
    if success:
        return {"status": "success", "message": f"Document {doc_id} deleted"}
    raise HTTPException(status_code=404, detail="Document not found")

@app.get("/api/stats")
async def get_stats(admin=Depends(verify_admin)):
    """Get statistics for admin dashboard"""
    stats = engine.get_stats()
    
    # Calculate vector DB size (approximate from FAISS index)
    faiss_size = 0
    if os.path.exists("./faiss_index"):
        for f in os.listdir("./faiss_index"):
            faiss_size += os.path.getsize(os.path.join("./faiss_index", f))
    
    stats["vector_db_size_bytes"] = faiss_size
    return stats

@app.post("/api/clear-knowledge-base")
async def clear_knowledge_base(admin=Depends(verify_admin)):
    """Clear all documents and reset the knowledge base"""
    try:
        # Clear vectorstore
        if os.path.exists("./faiss_index"):
            shutil.rmtree("./faiss_index")
        
        # Clear metadata
        engine.metadata = {
            "documents": [],
            "total_queries": 0,
            "last_query_at": None
        }
        engine.save_metadata()
        engine.vectorstore = None
        
        return {"status": "success", "message": "Knowledge base cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# FEEDBACK & ANALYTICS ENDPOINTS
# ============================================

FEEDBACK_FILE = "./data/feedback.json"

class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: str
    confidence: int = None

def load_feedback():
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_feedback(data):
    try:
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving feedback: {e}")

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    feedbacks = load_feedback()
    new_fb = {
        "query": req.query,
        "response": req.response,
        "rating": req.rating,
        "confidence": req.confidence,
        "timestamp": datetime.now().isoformat()
    }
    feedbacks.append(new_fb)
    save_feedback(feedbacks)
    return {"status": "success", "message": "Feedback submitted successfully"}

@app.get("/api/feedback/stats")
async def get_feedback_stats(admin=Depends(verify_admin)):
    feedbacks = load_feedback()
    total = len(feedbacks)
    thumbs_up = sum(1 for f in feedbacks if f["rating"] == "up")
    thumbs_down = sum(1 for f in feedbacks if f["rating"] == "down")
    satisfaction_rate = int((thumbs_up / total) * 100) if total > 0 else 100
    
    # Sort and take recent 10
    recent = list(reversed(feedbacks))[:10]
    
    return {
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "total": total,
        "satisfaction_rate": satisfaction_rate,
        "recent_feedback": recent
    }

@app.get("/api/analytics")
async def get_analytics(admin=Depends(verify_admin)):
    query_history = engine.metadata.get("query_history", [])
    now = datetime.now()
    
    # 1. Hourly Stats (Last 24 Hours)
    hourly_stats = []
    for i in range(23, -1, -1):
        target_time = now - timedelta(hours=i)
        time_str = target_time.strftime("%H:00")
        hourly_stats.append({"time": time_str, "queries": 0})
        
    for q in query_history:
        try:
            q_time = datetime.fromisoformat(q["timestamp"])
            if now - q_time <= timedelta(hours=24):
                hours_ago = int((now - q_time).total_seconds() / 3600)
                if 0 <= hours_ago < 24:
                    hourly_stats[23 - hours_ago]["queries"] += 1
        except Exception:
            pass
            
    # 2. Daily Stats (Last 7 Days)
    days_indonesian = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    daily_stats = []
    for i in range(6, -1, -1):
        target_date = now - timedelta(days=i)
        day_name = days_indonesian[target_date.weekday()]
        date_str = target_date.strftime("%d/%m")
        daily_stats.append({"day": day_name, "date": date_str, "queries": 0})
        
    for q in query_history:
        try:
            q_time = datetime.fromisoformat(q["timestamp"])
            if now - q_time <= timedelta(days=7):
                days_ago = int((now - q_time).total_seconds() / 86400)
                if 0 <= days_ago < 7:
                    daily_stats[6 - days_ago]["queries"] += 1
        except Exception:
            pass
            
    # 3. Popular Topics
    topics = [
        {"name": "Skripsi / Tugas Akhir", "keywords": ["skripsi", "ta", "tugas akhir", "judul", "proposal"]},
        {"name": "Cuti Akademik", "keywords": ["cuti", "aktif kembali", "krs", "registrasi"]},
        {"name": "Kelulusan / Cum Laude", "keywords": ["cum laude", "kelulusan", "lulus", "yudisium", "wisuda"]},
        {"name": "Ujian (UTS / UAS)", "keywords": ["uts", "uas", "ujian", "kalender"]},
        {"name": "Magang / KKN", "keywords": ["magang", "kkn", "praktik", "pkl"]},
        {"name": "Administrasi / UKT", "keywords": ["ukt", "bayar", "registrasi", "keuangan", "biaya"]}
    ]
    
    topic_counts = {t["name"]: 0 for t in topics}
    topic_counts["Lainnya"] = 0
    
    for q in query_history:
        query_text = q["query"].lower()
        matched = False
        for t in topics:
            if any(kw in query_text for kw in t["keywords"]):
                topic_counts[t["name"]] += 1
                matched = True
                break
        if not matched:
            topic_counts["Lainnya"] += 1
            
    total_matched = sum(topic_counts.values())
    popular_topics = []
    for topic, count in topic_counts.items():
        percentage = int((count / total_matched) * 100) if total_matched > 0 else 0
        popular_topics.append({
            "topic": topic,
            "count": count,
            "percentage": percentage
        })
    popular_topics.sort(key=lambda x: x["count"], reverse=True)
    
    # 4. Recent Queries
    recent_queries = []
    for q in reversed(query_history[-15:]):
        recent_queries.append({
            "query": q["query"],
            "timestamp": q["timestamp"]
        })
        
    total_queries_today = sum(1 for q in query_history if (now - datetime.fromisoformat(q["timestamp"])) <= timedelta(hours=24))
    total_queries_week = sum(1 for q in query_history if (now - datetime.fromisoformat(q["timestamp"])) <= timedelta(days=7))
    
    return {
        "hourly_stats": hourly_stats,
        "daily_stats": daily_stats,
        "popular_topics": popular_topics,
        "recent_queries": recent_queries,
        "total_queries_today": total_queries_today,
        "total_queries_week": total_queries_week
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
