import torch
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv
from ultralytics import YOLO
import json
import numpy as np
import cv2
import math
import os
from pathlib import Path
from PIL import Image, ImageOps
from rembg import remove
from scipy.spatial import distance
from sklearn.linear_model import LinearRegression

# --- 1. GNN ARCHITECTURE (GATv2 - 5 Channels: x, y, w, h, class) ---
class CrochetTiledGNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        # Heads=4 for spatial attention
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

# --- 2. THE INTEGRATED INFERENCE ENGINE ---
class CrochetInferenceEngine:
    def __init__(self, yolo_path, gnn_path, config_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 1. Load YOLO
        self.yolo = YOLO(yolo_path)
        
        # 2. Load GNN Config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # 3. Load GNN Model
        self.gnn = CrochetTiledGNN(
            in_channels=self.config['in_channels'], 
            hidden_channels=self.config['hidden_channels']
        ).to(self.device)
        
        # Load weights safely
        state_dict = torch.load(gnn_path, map_location=self.device)
        self.gnn.load_state_dict(state_dict)
        self.gnn.eval()

        # 4. Setup Class Mappings
        self.class_names = {v: k for k, v in self.config['class_map'].items()}
        self.class_map_rev = {k: v for k, v in self.config['class_map'].items()}

    def sanitize_image(self, img_path):
        """AI Background removal + CLAHE Grayscale."""
        input_img = Image.open(img_path)
        # Remove BG
        no_bg = remove(input_img)
        white_bg = Image.new("RGBA", no_bg.size, (255, 255, 255))
        final_rgba = Image.alpha_composite(white_bg, no_bg)
        
        # Grayscale
        gray = final_rgba.convert('L')
        gray_np = np.array(gray)
        
        # Enhance Contrast (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray_np)
        
        # Convert to 3-channel RGB for YOLO
        return Image.fromarray(enhanced).convert('RGB')

    def rectify_topology(self, node_list):
        """Calculates global slant and straightens rows."""
        if len(node_list) < 5: return node_list

        X = np.array([n['x'] for n in node_list]).reshape(-1, 1)
        Y = np.array([n['y'] for n in node_list])
        
        # 1. Calculate Tilt
        lr = LinearRegression().fit(X, Y)
        angle_rad = math.atan(lr.coef_[0])
        
        # 2. Rotate Points to Horizontal
        cos_a = math.cos(-angle_rad)
        sin_a = math.sin(-angle_rad)
        
        rectified = []
        for n in node_list:
            tx, ty = n['x'] - 0.5, n['y'] - 0.5
            rx = tx * cos_a - ty * sin_a
            ry = tx * sin_a + ty * cos_a
            
            new_node = n.copy()
            new_node['x'] = rx + 0.5
            new_node['y'] = ry + 0.5
            rectified.append(new_node)

        # 3. Vertical Quantization (Snap to rows)
        rectified.sort(key=lambda n: n['y'])
        final_nodes = []
        if rectified:
            row_clusters = []
            current_row = [rectified[0]]
            for i in range(1, len(rectified)):
                if abs(rectified[i]['y'] - current_row[0]['y']) < 0.06:
                    current_row.append(rectified[i])
                else:
                    row_clusters.append(current_row)
                    current_row = [rectified[i]]
            row_clusters.append(current_row)

            for cluster in row_clusters:
                avg_y = sum(n['y'] for n in cluster) / len(cluster)
                for n in cluster:
                    n['y'] = avg_y
                    final_nodes.append(n)

        return sorted(final_nodes, key=lambda n: n['id'])

    def calculate_radial_angle(self, node, center_x, center_y):
        """
        Calculates the angle based on the stitch's position relative 
        to the center of the Granny Square.
        """
        dx = node['x'] - center_x
        dy = node['y'] - center_y
        
        # Calculate angle from center to stitch
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # Adjust so 0 is 'Up'
        # We add 90 because in SVG/Math, 0 is 'Right'. 
        # In Crochet charts, symbols point 'Up' by default.
        return round(angle_deg + 90, 2)
    
    def calculate_stitch_angle(self, child, parent):
        """Used for Rows: Angle based on direction of the yarn path."""
        dx = child['x'] - parent['x']
        dy = child['y'] - parent['y']
        # If they are essentially in the same row, keep it upright (0)
        if abs(dy) < 0.05: return 0.0
        return round(math.degrees(math.atan2(dy, dx)) + 90, 2)

    def generate_technical_svg_string(self, nodes, edges):
        """Full international notation SVG generator."""
        PADDING, RANGE = 10, 80
        def to_vb(val): return (val * RANGE) + PADDING

        svg = ['<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">',
               '<rect width="100" height="100" fill="#f4e9e2" rx="2" />']

        # Draw Grid
        for pos in [10, 30, 50, 70, 90]:
            svg.append(f'<line x1="{pos}" y1="0" x2="{pos}" y2="100" stroke="#dcc3b4" stroke-width="0.05"/>')
            svg.append(f'<line x1="0" y1="{pos}" x2="100" y2="{pos}" stroke="#dcc3b4" stroke-width="0.05"/>')

        # Draw Edges
        for edge in edges:
            n1, n2 = nodes[edge["child_id"]], nodes[edge["parent_id"]]
            svg.append(f'<line x1="{to_vb(n1["x"])}" y1="{to_vb(n1["y"])}" x2="{to_vb(n2["x"])}" y2="{to_vb(n2["y"])}" stroke="#52a4b5" stroke-width="0.15" stroke-dasharray="0.5,0.5" />')

        # Symbol Paths
        paths = {
            "ch_stitch":  '<ellipse cx="0" cy="0" rx="1.5" ry="0.8" fill="none" stroke="#3a3335" stroke-width="0.6" />',
            "sc_stitch":  '<g transform="scale(0.8)"><line x1="0" y1="-1.5" x2="0" y2="1.5" stroke="#3a3335" stroke-width="0.7" /><line x1="-1.5" y1="0" x2="1.5" y2="0" stroke="#3a3335" stroke-width="0.7" /></g>',
            "hdc_stitch": '<g transform="scale(0.8)"><line x1="0" y1="-2.5" x2="0" y2="2.5" stroke="#3a3335" stroke-width="0.7" /><line x1="-2" y1="-2.5" x2="2" y2="-2.5" stroke="#3a3335" stroke-width="0.7" /></g>',
            "dc_stitch":  '<g transform="scale(0.8)"><line x1="0" y1="-3.2" x2="0" y2="3.2" stroke="#3a3335" stroke-width="0.7" /><line x1="-2" y1="-3.2" x2="2" y2="-3.2" stroke="#3a3335" stroke-width="0.7" /><line x1="-1.2" y1="-0.8" x2="1.2" y2="0.8" stroke="#3a3335" stroke-width="0.6" /></g>',
            "tr_stitch":  '<g transform="scale(0.8)"><line x1="0" y1="-4" x2="0" y2="4" stroke="#3a3335" stroke-width="0.7" /><line x1="-2" y1="-4" x2="2" y2="-4" stroke="#3a3335" stroke-width="0.7" /><line x1="-1" y1="-1.8" x2="1" y2="-0.5" stroke="#3a3335" stroke-width="0.5" /><line x1="-1" y1="0.5" x2="1" y2="1.8" stroke="#3a3335" stroke-width="0.5" /></g>',
            "sl_st":      '<circle cx="0" cy="0" r="0.7" fill="#3a3335" />'
        }

        for node in nodes:
            symbol = paths.get(node["type"], paths["sl_st"])
            svg.append(f'<g transform="translate({to_vb(node["x"])} {to_vb(node["y"])}) rotate({node.get("angle", 0)})">{symbol}</g>')

        svg.append('</svg>')
        return "".join(svg)

    def run_pipeline(self, image_path):
        # PHASE 0: SANITIZATION
        sanitized_img = self.sanitize_image(image_path)
        img_w, img_h = sanitized_img.size
        sanitized_np = np.array(sanitized_img)

        # PHASE 1: YOLO
        results = self.yolo.predict(sanitized_np, conf=0.18, imgsz=640, verbose=False)[0]
        nodes = []
        for i, box in enumerate(results.boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            nodes.append({
                "id": i, "type": self.class_names.get(int(box.cls[0]), "sc_stitch"),
                "x": (x1+x2)/2/img_w, "y": (y1+y2)/2/img_h, "w": (x2-x1)/img_w, "h": (y2-y1)/img_h
            })
        if len(nodes) < 2: return None


        # --- NEW: RADIAL VS LINEAR DETECTION ---
        # Calculate the bounding box of all stitches
        all_x = [n['x'] for n in nodes]
        all_y = [n['y'] for n in nodes]
        swatch_width = max(all_x) - min(all_x)
        swatch_height = max(all_y) - min(all_y)
        
        # Aspect ratio check: Granny squares are roughly 1:1
        # Swatches/Rows are usually long rectangles
        is_radial = 0.7 < (swatch_width / swatch_height) < 1.3
        
        swatch_center_x = sum(all_x) / len(all_x)
        swatch_center_y = sum(all_y) / len(all_y)

        # --- PHASE 2: POSITIONING & ROTATION ---
        if is_radial:
            print("📐 Radial Pattern (Granny Square) detected.")
            for node in nodes:
                node['angle'] = self.calculate_radial_angle(node, swatch_center_x, swatch_center_y)
                
                # OPTIONAL: Quantize to 0, 90, 180, 270 for a "Perfect" technical look
                # node['angle'] = round(node['angle'] / 90) * 90
        else:
            print("📏 Linear Pattern detected. Applying rectification.")
            nodes = self.rectify_topology(nodes)

        # PHASE 3: GNN
        node_feats = torch.tensor([[n['x'], n['y'], n['w'], n['h'], float(self.class_map_rev[n['type']])] for n in nodes], dtype=torch.float).to(self.device)
        
        # Adaptive search
        avg_h = node_feats[:, 3].mean().item()
        dist_matrix = distance.cdist(node_feats[:, :2].cpu().numpy(), node_feats[:, :2].cpu().numpy())
        
        pairs = []
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if i != j and dist_matrix[i,j] < avg_h * 2.8:
                    if node_feats[i, 1] < node_feats[j, 1] + 0.05:
                        pairs.append([i, j])

        if not pairs: return {"nodes": nodes, "edges": []}, self.generate_technical_svg_string(nodes, [])

        edge_label_index = torch.tensor(pairs, dtype=torch.long).t().to(self.device)
        with torch.no_grad():
            z = self.gnn.encode(node_feats, torch.zeros((2, 0), dtype=torch.long).to(self.device))
            out = torch.sigmoid(self.gnn.decode(z, edge_label_index))
        
        # Best Parent Logic
        probs, edge_idx = out.cpu().numpy(), edge_label_index.cpu().numpy()
        best_links = {}
        for i in range(len(probs)):
            if probs[i] > 0.35:
                c, p = int(edge_idx[0, i]), int(edge_idx[1, i])
                if c not in best_links or probs[i] > best_links[c][0]:
                    best_links[c] = (probs[i], p)

        final_edges = []
        for c, (prob, p) in best_links.items():
            nodes[c]['angle'] = self.calculate_stitch_angle(nodes[c], nodes[p])
            final_edges.append({"child_id": c, "parent_id": p})

        return {"nodes": nodes, "edges": final_edges}, self.generate_technical_svg_string(nodes, final_edges)