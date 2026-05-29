import torch
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv
from ultralytics import YOLO
import json
import numpy as np
import cv2
import math
from pathlib import Path
from PIL import Image, ImageOps
from rembg import remove
from scipy.spatial import distance

# --- 1. GNN ARCHITECTURE (GATv2 - 5 Channels) ---
class CrochetTiledGNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        self.conv1 = GATv2Conv(in_channels, hidden_channels, heads=4, concat=True)
        self.conv2 = GATv2Conv(hidden_channels * 4, hidden_channels, heads=1, concat=False)
        self.post_mp = torch.nn.Sequential(
            torch.nn.Linear(hidden_channels * 2, hidden_channels),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_channels, 1)
        )

    def encode(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)

    def decode(self, z, edge_label_index):
        src, dst = edge_label_index
        edge_feat = torch.cat([z[src], z[dst]], dim=-1)
        return self.post_mp(edge_feat).view(-1)

# --- 2. DATA-DRIVEN INFERENCE ENGINE ---
class CrochetInferenceEngine:
    def __init__(self, yolo_path, gnn_path, config_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load YOLO
        self.yolo = YOLO(yolo_path)
        
        # Load GNN Config & Model
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.gnn = CrochetTiledGNN(
            in_channels=self.config['in_channels'], 
            hidden_channels=self.config['hidden_channels']
        ).to(self.device)
        self.gnn.load_state_dict(torch.load(gnn_path, map_location=self.device))
        self.gnn.eval()

        self.class_names = {v: k for k, v in self.config['class_map'].items()}

    def sanitize_image(self, img_path):
        """Standard Preprocessing: BG Removal -> CLAHE Grayscale -> RGB."""
        input_img = Image.open(img_path)
        no_bg = remove(input_img)
        white_bg = Image.new("RGBA", no_bg.size, (255, 255, 255))
        final_rgba = Image.alpha_composite(white_bg, no_bg)
        
        gray = final_rgba.convert('L')
        gray_np = np.array(gray)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray_np)
        return Image.fromarray(enhanced).convert('RGB')

    def calculate_stitch_angle(self, child_node, parent_node):
        """
        Heuristic: Calculates the rotation angle based on the vector 
        from the parent stitch to the child stitch.
        """
        dx = child_node['x'] - parent_node['x']
        dy = child_node['y'] - parent_node['y']
        
        # Calculate angle in radians, then to degrees
        # We subtract 90 because crochet symbols are 'upright' by default
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad) + 90
        return round(angle_deg, 2)

    def run_pipeline(self, image_path):
        # --- PHASE 0: PREPROCESSING ---
        sanitized_img = self.sanitize_image(image_path)
        img_w, img_h = sanitized_img.size
        sanitized_np = np.array(sanitized_img)

        # --- PHASE 1: YOLO STITCH DETECTION ---
        yolo_results = self.yolo.predict(sanitized_np, conf=0.20, imgsz=640, verbose=False)[0]
        
        node_list = []
        node_features = []

        for i, box in enumerate(yolo_results.boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            bw, bh = (x2 - x1), (y2 - y1)
            cls = int(box.cls[0])
            
            # Core Node Data
            node_list.append({
                "id": i,
                "type": self.class_names.get(cls, "sc_stitch"),
                "x": round(cx / img_w, 4),
                "y": round(cy / img_h, 4),
                "w": round(bw / img_w, 4),
                "h": round(bh / img_h, 4),
                "angle": 0 # Default upright
            })
            # 5 Features for GNN
            node_features.append([cx/img_w, cy/img_h, bw/img_w, bh/img_h, float(cls)])

        if len(node_features) < 2: return None

        # --- PHASE 2: GNN TOPOLOGY PREDICTION ---
        x = torch.tensor(node_features, dtype=torch.float).to(self.device)
        
        # Adaptive search radius
        avg_h = np.mean([f[3] for f in node_features])
        max_dist = avg_h * 2.5 

        node_coords = np.array([f[:2] for f in node_features])
        dist_matrix = distance.cdist(node_coords, node_coords)
        
        candidate_pairs = []
        for i in range(len(node_features)):
            for j in range(len(node_features)):
                if i != j and dist_matrix[i, j] < max_dist:
                    # Directional Hint: Child (i) should be logically 'after' or 'above' parent (j)
                    if node_coords[i][1] < node_coords[j][1] + 0.05:
                        candidate_pairs.append([i, j])

        if not candidate_pairs:
            return {"nodes": node_list, "edges": []}, None

        edge_label_index = torch.tensor(candidate_pairs, dtype=torch.long).t().to(self.device)

        with torch.no_grad():
            z = self.gnn.encode(x, torch.zeros((2, 0), dtype=torch.long).to(self.device))
            out = torch.sigmoid(self.gnn.decode(z, edge_label_index))
        
        probs = out.cpu().numpy()
        pairs = edge_label_index.cpu().numpy()
        best_links = {}

        for i in range(len(probs)):
            if probs[i] > 0.35: # F1-optimized threshold
                c, p = int(pairs[0, i]), int(pairs[1, i])
                if c not in best_links or probs[i] > best_links[c][0]:
                    best_links[c] = (probs[i], p)

        # --- PHASE 3: REFINING ANGLES & JSON ---
        final_edges = []
        for child_idx, (prob, parent_idx) in best_links.items():
            # 1. Update the angle of the child based on its parent connection
            # Especially important for Granny Squares/Radial patterns
            angle = self.calculate_stitch_angle(node_list[child_idx], node_list[parent_idx])
            node_list[child_idx]['angle'] = angle
            
            # 2. Add to edge list
            final_edges.append({
                "child_id": child_idx,
                "parent_id": parent_idx,
                "connection_type": "standard" if prob > 0.7 else "loose"
            })

        # Return only the structured graph data
        return {"nodes": node_list, "edges": final_edges}, None