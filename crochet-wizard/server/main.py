import json
import os
import sys
import shutil
import uuid
from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
# 1. FORCE the process to look inside the server directory
BASE_DIR = Path(__file__).resolve().parent
os.chdir(str(BASE_DIR))
sys.path.append(str(BASE_DIR))

# Now import your engine
from inference_engine import CrochetInferenceEngine

# 2. Use simple filenames now that we are "inside" the folder
engine = CrochetInferenceEngine(
    yolo_path="yolo_model.pt", 
    gnn_path="crochet_gnn_model.pth", 
    config_path="gnn_config.json"
)

# Safety Check: Print these to your console to verify they exist
# print(f"--- Path Verification ---")
# print(f"Looking for YOLO at: {yolo_abs_path} | Found: {os.path.exists(yolo_abs_path)}")
# print(f"Looking for GNN at:  {gnn_abs_path} | Found: {os.path.exists(gnn_abs_path)}")
# print(f"-------------------------")

# if not os.path.exists(yolo_abs_path):
#     raise FileNotFoundError(f"FATAL: Could not find yolo_model.pt at {yolo_abs_path}")

# # Initialize the engine
# engine = CrochetInferenceEngine(
#     yolo_path=yolo_abs_path, 
#     gnn_path=gnn_abs_path, 
#     config_path=config_abs_path
# )


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

engine = CrochetInferenceEngine(
    yolo_path="yolo_model.pt", 
    gnn_path="crochet_gnn_model.pth", 
    config_path="gnn_config.json"
)

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...), 
    yarn_properties: str = Form(...),
    output_mode: str = Form(...),
    user_id: str = Form(...)
):
    try:
        content = await file.read()
        temp_name = f"{uuid.uuid4()}.jpg"
        file_path = UPLOAD_DIR / temp_name
        with open(file_path, "wb") as f:
            f.write(content)

        # 1. RUN THE FULL AI PIPELINE
        # Result is now (graph_json, None)
        pipeline_result = engine.run_pipeline(str(file_path))

        if pipeline_result is None:
            return {"success": False, "message": "No stitches detected."}

        # IMPORTANT: Use index 0 to get the graph_json
        graph_json = pipeline_result[0] 

        # 2. Upload photo to Supabase (Your existing code...)
        storage_path = f"{user_id}/temp/{temp_name}"
        supabase.storage.from_("swatches").upload(path=storage_path, file=content)
        image_url = supabase.storage.from_("swatches").get_public_url(storage_path)

        # 3. Return the result (NOTICE: svg_data is removed or set to empty string)
        return {
            "success": True,
            "graph_json": graph_json,
            "svg_data": "",  # Frontend now generates this from graph_json
            "image_url": str(image_url)
        }
    except Exception as e:
        print(f"PIPELINE ERROR: {e}")
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