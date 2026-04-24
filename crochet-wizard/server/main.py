import json
import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- INITIALIZATION ---
app = FastAPI()

# Enable CORS for Mobile App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# --- SCHEMAS ---
class ModifyRequest(BaseModel):
    pattern_id: str  # We need this to update the specific database row
    prompt: str
    current_graph: Dict
    yarn_properties: Dict
    user_id: str

# --- API ENDPOINTS ---

@app.get("/")
async def health_check():
    return {"status": "online", "engine": "CrochetWizard-GNN"}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...), 
    yarn_properties: str = Form(...),
    output_mode: str = Form(...),
    user_id: str = Form(...)
):
    try:
        # 1. Save locally for YOLO processing
        temp_file_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / temp_file_name
        
        # Read content once to avoid stream exhaustion
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 2. RUN AI LOGIC (Placeholder for your GNN/YOLO)
        # nodes, edges = your_gnn_model.predict(file_path)
        graph_json = {"nodes": [{"id": 0, "type": "root", "x": 50, "y": 50}], "edges": []}
        
        # 3. GENERATE INITIAL SVG
        svg_string = f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="{json.loads(yarn_properties)["color"]}" /></svg>'

        # 4. Upload to Supabase Storage
        storage_path = f"{user_id}/{temp_file_name}"
        supabase.storage.from_("swatches").upload(
            path=storage_path,
            file=content,
            file_options={"content-type": "image/jpeg"}
        )
        image_url = supabase.storage.from_("swatches").get_public_url(storage_path)

        return {
            "success": True,
            "graph_json": graph_json,
            "svg_data": svg_string,
            "image_url": image_url, # Optional: return a preview link
            "message": "Preview generated"
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modify")
async def modify(request: ModifyRequest):
    try:
        # 1. AI Logic (Placeholder) - update the graph based on request.prompt
        updated_graph = request.current_graph.copy()
        
        # 2. Re-render SVG (Placeholder)
        new_svg = f'<svg viewBox="0 0 100 100"><rect x="30" y="30" width="40" height="40" fill="{request.yarn_properties.get("color")}" /></svg>'

    

        return {
            "success": True,
            "message": "Pattern updated in your library.",
            "graph_json": updated_graph,
            "svg_data": new_svg
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))