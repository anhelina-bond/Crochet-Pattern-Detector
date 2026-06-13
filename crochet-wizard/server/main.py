import os
import sys
import uuid
import uvicorn
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Dict
from supabase import create_client, Client
from dotenv import load_dotenv
# 1. FORCE the process to look inside the server directory
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
os.chdir(str(BASE_DIR))
sys.path.append(str(BASE_DIR))

# Now import your engine
from inference_engine import CrochetInferenceEngine
from llm_modifier import apply_generative_modification, normalize_graph_for_mobile, validate_graph

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


load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env", override=False)

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
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# --- SCHEMAS ---
class ModifyRequest(BaseModel):
    pattern_id: Optional[str] = None
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
        prompt = request.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Modification prompt cannot be empty.")

        base_graph = normalize_graph_for_mobile(validate_graph(request.current_graph))
        updated_graph = await apply_generative_modification(base_graph, prompt)

        return {
            "success": True,
            "message": "Pattern updated with AI.",
            "graph_json": updated_graph.dict(),
            "svg_data": ""
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
