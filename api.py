"""
============================================
AKASIA v1.0 - API Backend Server
============================================
Asisten Akademik Berbasis AI untuk UHO

File ini berisi:
- Endpoint API untuk chat (/api/chat)
- Endpoint untuk upload dokumen (/api/upload)
- Endpoint untuk manajemen dokumen (/api/documents)
- Endpoint untuk statistik (/api/stats)

Jalankan dengan: python api.py
Server akan berjalan di http://localhost:8000
============================================
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from rag_engine import RAGEngine
from typing import List
import uvicorn
import shutil
import os
import json
import asyncio
from app import extract_text_from_pdf

# Inisialisasi FastAPI dengan metadata
app = FastAPI(
    title="AKASIA API",
    description="Asisten Akademik Berbasis AI untuk Universitas Halu Oleo",
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

class ChatRequest(BaseModel):
    message: str

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "UHO Academic Chatbot API is running"}

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
async def upload_files(files: List[UploadFile] = File(...)):
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
async def get_documents():
    """Get list of all uploaded documents"""
    documents = engine.get_documents()
    return {"documents": documents}

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by ID"""
    success = engine.delete_document(doc_id)
    if success:
        return {"status": "success", "message": f"Document {doc_id} deleted"}
    raise HTTPException(status_code=404, detail="Document not found")

@app.get("/api/stats")
async def get_stats():
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
async def clear_knowledge_base():
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
