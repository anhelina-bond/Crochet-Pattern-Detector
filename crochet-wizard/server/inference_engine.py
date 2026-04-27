import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from ultralytics import YOLO
import json
import numpy as np
from pathlib import Path
from PIL import Image

# --- GNN ARCHITECTURE (Must match your Colab code exactly) ---
class CrochetGNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
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

# --- INFERENCE ENGINE ---
class CrochetInferenceEngine:
    def __init__(self, yolo_path, gnn_path, config_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 1. Load YOLO
        self.yolo = YOLO(yolo_path)
        
        # 2. Load GNN Config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # 3. Load GNN Model
        self.gnn = CrochetGNN(
            in_channels=self.config['in_channels'], 
            hidden_channels=self.config['hidden_channels']
        ).to(self.device)
        self.gnn.load_state_dict(torch.load(gnn_path, map_location=self.device))
        self.gnn.eval()

        self.class_names = {v: k for k, v in self.config['class_map'].items()}

    def generate_svg(self, nodes, edges):
        """Converts graph to technical SVG symbols"""
        svg_parts = ['<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">']
        
        # Draw connections (Edges) first so they are in the background
        for edge in edges:
            start_node = nodes[edge[0]]
            end_node = nodes[edge[1]]
            svg_parts.append(f'<line x1="{start_node["x"]*100}" y1="{start_node["y"]*100}" x2="{end_node["x"]*100}" y2="{end_node["y"]*100}" stroke="#D3D3D3" stroke-width="0.5" />')

        # Draw Stitch Symbols (Nodes)
        symbols = {
            "sc_stitch": "x", 
            "dc_stitch": "†", 
            "ch_stitch": "o", 
            "tr_stitch": "‡", 
            "sl_st": "•"
        }
        
        for node in nodes:
            char = symbols.get(node['type'], "?")
            svg_parts.append(
                f'<text x="{node["x"]*100}" y="{node["y"]*100}" font-size="5" text-anchor="middle" fill="#3a3335">{char}</text>'
            )
            
        svg_parts.append('</svg>')
        return "".join(svg_parts)

    def run_pipeline(self, image_path):
        # --- PHASE 1: YOLO DETECTION ---
        yolo_results = self.yolo.predict(image_path, conf=0.15, imgsz=1024)[0]
        img_w, img_h = yolo_results.orig_shape[1], yolo_results.orig_shape[0]
        
        node_list = []
        node_features = []

        for box in yolo_results.boxes:
            # Get center coordinates and normalize
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx, cy = (x1 + x2) / 2 / img_w, (y1 + y2) / 2 / img_h
            cls = int(box.cls[0])
            
            node_list.append({"type": self.class_names.get(cls, "unknown"), "x": cx, "y": cy})
            node_features.append([cx, cy, float(cls)])

        if not node_features:
            return None

        # --- PHASE 2: GNN TOPOLOGY ---
        x = torch.tensor(node_features, dtype=torch.float).to(self.device)
        
        # Generate all possible pairs for link prediction (Cartesian product)
        num_nodes = x.size(0)
        idx = torch.arange(num_nodes)
        grid_x, grid_y = torch.meshgrid(idx, idx, indexing='ij')
        edge_label_index = torch.stack([grid_x.reshape(-1), grid_y.reshape(-1)], dim=0).to(self.device)

        # We use an empty edge_index for the initial embedding (inductive)
        edge_index = torch.zeros((2, 0), dtype=torch.long).to(self.device)

        with torch.no_grad():
            z = self.gnn.encode(x, edge_index)
            out = torch.sigmoid(self.gnn.decode(z, edge_label_index))
        
        # Filter predicted edges (Threshold > 0.8)
        predicted_edges = []
        probs = out.cpu().numpy()
        edge_candidates = edge_label_index.cpu().numpy()

        for i in range(len(probs)):
            if probs[i] > 0.8:
                u, v = int(edge_candidates[0, i]), int(edge_candidates[1, i])
                if u != v: # No self-loops
                    predicted_edges.append([u, v])

        # --- PHASE 3: RESULT COMPILATION ---
        final_graph = {"nodes": node_list, "edges": predicted_edges}
        svg_data = self.generate_svg(node_list, predicted_edges)

        return final_graph, svg_data