from networkx import nodes
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
from scipy.spatial import distance, cKDTree
from sklearn.linear_model import LinearRegression


def make_serializable(obj):
        """Recursively convert NumPy types to standard Python types for JSON."""
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(i) for i in obj]
        elif isinstance(obj, np.ndarray):
            return make_serializable(obj.tolist())
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        else:
            return obj
# --- 1. GNN ARCHITECTURE (GATv2 - 6 Channels: bx, by, hx, hy, class, conf) ---
# --- 1. FIXED GNN ARCHITECTURE (Matches your .pth weights) ---
class CrochetPoseGNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        # 1. conv1 MUST take 6 channels as seen in your error trace [512, 6]
        self.conv1 = GATv2Conv(in_channels, hidden_channels, heads=4, concat=True)
        self.conv2 = GATv2Conv(hidden_channels * 4, hidden_channels, heads=1, concat=False)

        # 2. post_mp MUST have 4 layers to match index 3 (Lin -> ReLU -> Drop -> Lin)
        self.post_mp = torch.nn.Sequential(
            torch.nn.Linear(hidden_channels * 2, hidden_channels), # Index 0
            torch.nn.ReLU(),                                      # Index 1
            torch.nn.Dropout(0.2),                                # Index 2 (The 'Missing' key)
            torch.nn.Linear(hidden_channels, 1)                    # Index 3 (The 'Unexpected' key)
        )

    def encode(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)

    def decode(self, z, edge_label_index):
        src, dst = edge_label_index
        edge_feat = torch.cat([z[src], z[dst]], dim=-1)
        return self.post_mp(edge_feat).view(-1)
# --- 2. THE INTEGRATED POSE-AWARE ENGINE ---
class CrochetInferenceEngine:
    def __init__(self, yolo_path, gnn_path, config_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load YOLO-Pose
        self.yolo = YOLO(yolo_path)
        
        # Load GNN Config (Expects 6 channels)
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.gnn = CrochetPoseGNN(
            in_channels=self.config['in_channels'], 
            hidden_channels=self.config['hidden_channels']
        ).to(self.device)
        
        self.gnn.load_state_dict(torch.load(gnn_path, map_location=self.device))
        self.gnn.eval()

        self.class_names = {v: k for k, v in self.config['class_map'].items()}

    def sanitize_image(self, img_path):
        """Preprocesses raw color into high-contrast 3-channel grayscale."""
        input_img = Image.open(img_path)
        # Background removal (using CPU mode to avoid DLL errors)
        no_bg = remove(input_img)
        white_bg = Image.new("RGBA", no_bg.size, (255, 255, 255))
        final_rgba = Image.alpha_composite(white_bg, no_bg)
        
        gray = final_rgba.convert('L')
        gray_np = np.array(gray)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray_np)
        
        # Must return 3 channels for YOLOv11 architecture
        return Image.fromarray(enhanced).convert('RGB')

    def rectify_topology(self, node_list):
        if len(node_list) < 5: return node_list
        X = np.array([n['x'] for n in node_list]).reshape(-1, 1)
        Y = np.array([n['y'] for n in node_list])
        lr = LinearRegression().fit(X, Y)
        
        # FIX: Explicitly cast the slope to a Python float
        angle_rad = float(math.atan(lr.coef_[0])) 
        
        cos_a = math.cos(-angle_rad)
        sin_a = math.sin(-angle_rad)
        
        for n in node_list:
            tx, ty = float(n['x']) - 0.5, float(n['y']) - 0.5
            # FIX: Ensure new coordinates are standard floats
            n['x'] = float((tx * cos_a - ty * sin_a) + 0.5)
            n['y'] = float((tx * sin_a + ty * cos_a) + 0.5)
            n['angle'] = 0.0 
        return node_list

    def build_spatial_bridge(self, node_features, k=6, dist_thresh=0.25):
        """
        CRITICAL: Creates the candidate graph for Message Passing.
        Connects every stitch's HEAD to the K nearest BASES.
        """
        # Node features: [bx, by, hx, hy, class, conf]
        bases = np.array([[f[0], f[1]] for f in node_features])
        heads = np.array([[f[2], f[3]] for f in node_features])
        
        tree = cKDTree(bases)
        src_list, dst_list = [], []
        
        for i, head_pt in enumerate(heads):
            dists, idxs = tree.query(head_pt, k=min(k, len(node_features)))
            if isinstance(dists, float): dists, idxs = [dists], [idxs] # Handle single result
            
            for d, j in zip(dists, idxs):
                if i != j and d < dist_thresh:
                    src_list.append(i) # Child (Current)
                    dst_list.append(j) # Parent (Target)
        
        if not src_list:
            return torch.zeros((2, 0), dtype=torch.long).to(self.device)
        return torch.tensor([src_list, dst_list], dtype=torch.long).to(self.device)

    def generate_technical_svg_string(self, nodes, edges):
        """Generates the professional international notation chart."""
        PADDING, RANGE = 10, 80
        def to_vb(val): return (val * RANGE) + PADDING
        
        svg = ['<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">',
               '<rect width="100" height="100" fill="#f4e9e2" rx="2" />'] # Powder Petal BG

        # Draw Edges (Dashed connections)
        for edge in edges:
            n1, n2 = nodes[edge["child_id"]], nodes[edge["parent_id"]]
            svg.append(f'<line x1="{to_vb(n1["x"])}" y1="{to_vb(n1["y"])}" x2="{to_vb(n2["x"])}" y2="{to_vb(n2["y"])}" stroke="#52a4b5" stroke-width="0.15" stroke-dasharray="0.5,0.5" opacity="0.4" />')

        # Stitch Symbols (Paths match StitchLibrary.tsx)
        paths = {
            "ch_stitch":  '<ellipse cx="0" cy="0" rx="1.5" ry="0.8" fill="none" stroke="#3a3335" stroke-width="0.6" />',
            "sc_stitch":  '<g transform="scale(0.8)"><line x1="0" y1="-1.5" x2="0" y2="1.5" stroke="#3a3335" stroke-width="0.6" /><line x1="-1.5" y1="0" x2="1.5" y2="0" stroke="#3a3335" stroke-width="0.6" /></g>',
            "hdc_stitch": '<g transform="scale(0.8)"><line x1="0" y1="-2.5" x2="0" y2="2.5" stroke="#3a3335" stroke-width="0.6" /><line x1="-1.5" y1="-2.5" x2="1.5" y2="-2.5" stroke="#3a3335" stroke-width="0.6" /></g>',
            "dc_stitch":  '<g transform="scale(0.8)"><line x1="0" y1="-3" x2="0" y2="3" stroke="#3a3335" stroke-width="0.6" /><line x1="-1.5" y1="-3" x2="1.5" y2="-3" stroke="#3a3335" stroke-width="0.6" /><line x1="-1" y1="-0.5" x2="1" y2="0.5" stroke="#3a3335" stroke-width="0.4" /></g>',
            "tr_stitch":  '<g transform="scale(0.8)"><line x1="0" y1="-4" x2="0" y2="4" stroke="#3a3335" stroke-width="0.6" /><line x1="-1.5" y1="-4" x2="1.5" y2="-4" stroke="#3a3335" stroke-width="0.6" /><line x1="-1" y1="-2" x2="1" y2="-1" stroke="#3a3335" stroke-width="0.4" /><line x1="-1" y1="0.5" x2="1" y2="1.5" stroke="#3a3335" stroke-width="0.4" /></g>',
            "sl_st":      '<circle cx="0" cy="0" r="0.8" fill="#3a3335" />'
        }

        for node in nodes:
            symbol = paths.get(node["type"], paths["sl_st"])
            svg.append(f'<g transform="translate({to_vb(node["x"])} {to_vb(node["y"])}) rotate({node.get("angle", 0)})">{symbol}</g>')

        svg.append('</svg>')
        return "".join(svg)

    
        
    def calculate_radial_angle(self, node, center_x, center_y):
        """Calculates angle based on distance from center (for Granny Squares)."""
        dx = node['x'] - center_x
        dy = node['y'] - center_y
        return round(math.degrees(math.atan2(dy, dx)) + 90, 2)

    def calculate_stitch_angle(self, child_node, parent_node):
        """Calculates angle based on connection vector (for Linear Rows)."""
        dx = child_node['x'] - parent_node['x']
        dy = child_node['y'] - parent_node['y']
        
        # HEURISTIC: If stitches are in the same horizontal row, keep them upright (0 deg)
        if abs(dy) < 0.05: 
            return 0.0
            
        # Otherwise, calculate the rotation to point toward the parent
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad) + 90
        return round(angle_deg, 2)


    from scipy.spatial import distance

    def find_swatch_medoid(self, node_list):
        """
        Finds the 'most central' stitch. 
        Much more robust than mean() which is skewed by background noise.
        """
        coords = np.array([[n['x'], n['y']] for n in node_list])
        # Calculate all-pairs distances
        dist_matrix = distance.cdist(coords, coords)
        # The medoid is the node with the minimum sum of distances to all others
        sum_dists = np.sum(dist_matrix, axis=1)
        medoid_idx = np.argmin(sum_dists)
        return coords[medoid_idx][0], coords[medoid_idx][1]

    def apply_cluster_orientation(self, node_list, cx, cy):
        """
        Groups nearby stitches into clusters (like Granny Square 3-dc groups)
        and ensures they all share the same logical angle.
        """
        coords = np.array([[n['x'], n['y']] for n in node_list])
        # Use a small radius to find clusters (3% of screen)
        tree = cKDTree(coords)
        
        processed = set()
        for i, node in enumerate(node_list):
            if i in processed: continue
            
            # Find neighbors within a very tight radius
            indices = tree.query_ball_point(coords[i], r=0.04)
            
            # Calculate one angle for the whole cluster based on its average position
            cluster_xs = [node_list[idx]['x'] for idx in indices]
            cluster_ys = [node_list[idx]['y'] for idx in indices]
            avg_x, avg_y = np.mean(cluster_xs), np.mean(cluster_ys)
            
            # The common angle for this cluster
            shared_angle = self.calculate_radial_angle({"x": avg_x, "y": avg_y}, cx, cy)
            
            for idx in indices:
                node_list[idx]['angle'] = shared_angle
                processed.add(idx)
                
        return node_list

    def run_pipeline(self, image_path):
        # --- STAGE 0: PREPROCESSING ---
        sanitized_img = self.sanitize_image(image_path)
        img_w, img_h = sanitized_img.size
        img_np = np.array(sanitized_img)

        # --- STAGE 1: DETECTION (Nodes) ---
        yolo_results = self.yolo.predict(img_np, conf=0.15, imgsz=1024, verbose=False)[0]
        if not yolo_results.keypoints:
            return None

        node_list = []
        node_features = []
        kpts = yolo_results.keypoints.xy.cpu().numpy()
        classes = yolo_results.boxes.cls.cpu().numpy()
        confs = yolo_results.boxes.conf.cpu().numpy()

        for i in range(len(kpts)):
            base, head = kpts[i][0], kpts[i][1]
            cx, cy = (base + head) / 2
            
            # 6 Features: [base_x, base_y, head_x, head_y, class, confidence]
            feat = [base[0]/img_w, base[1]/img_h, head[0]/img_w, head[1]/img_h, float(classes[i]), float(confs[i])]
            node_features.append(feat)
            
            node_list.append({
                "id": i, 
                "type": self.class_names.get(int(classes[i]), "sc_stitch"),
                "x": cx/img_w, 
                "y": cy/img_h, 
                "angle": 0.0
            })

        if len(node_list) < 2:
            return None

        # --- STAGE 2: GEOMETRY ANALYSIS (REFINED) ---
    
        # 1. Use Medoid for the center (Fixes the Top-Left bias)
        swatch_center_x, swatch_center_y = self.find_swatch_medoid(node_list)
        
        # 2. Re-calculate R-magnitude (Parallelism check)
        stitch_vectors = []
        for f in node_features:
            dx, dy = f[2] - f[0], f[3] - f[1]
            mag = math.sqrt(dx**2 + dy**2) + 1e-6
            stitch_vectors.append((dx/mag, dy/mag))
        
        r_magnitude = math.sqrt(np.mean([v[0] for v in stitch_vectors])**2 + 
                                np.mean([v[1] for v in stitch_vectors])**2)

        # 3. Decision Logic
        # We only rectify if the stitches are VERY parallel (R > 0.7)
        is_radial = r_magnitude < 0.65 

        if is_radial:
            print(f"📐 RADIAL MODE: R={r_magnitude:.2f}. Preserving square geometry.")
            # DO NOT call rectify_topology. Keep detected coordinates.
            node_list = self.apply_cluster_orientation(node_list, swatch_center_x, swatch_center_y)
        else:
            print(f"📏 LINEAR MODE: R={r_magnitude:.2f}. Straightening rows.")
            node_list = self.rectify_topology(node_list)
            for node in node_list:
                node['angle'] = 0.0
        # --- STAGE 3: TOPOLOGY (GNN Edges) ---
        x = torch.tensor(node_features, dtype=torch.float).to(self.device)
        edge_label_index = self.build_spatial_bridge(node_features)
        
        if edge_label_index.shape[1] == 0:
            return make_serializable({"nodes": node_list, "edges": []}), self.generate_technical_svg_string(node_list, [])

        with torch.no_grad():
            z = self.gnn.encode(x, edge_label_index)
            out = torch.sigmoid(self.gnn.decode(z, edge_label_index))
        
        probs = out.cpu().numpy()
        pairs = edge_label_index.cpu().numpy()
        
        # Best-Parent Filter (Ensures each child has max 1 parent)
        best_links = {}
        for i in range(len(probs)):
            if probs[i] > 0.35:
                c, p = int(pairs[0, i]), int(pairs[1, i])
                if c not in best_links or probs[i] > best_links[c][0]:
                    best_links[c] = (float(probs[i]), p)

        final_edges = []
        for child_idx, (prob, parent_idx) in best_links.items():
            final_edges.append({
                "child_id": child_idx, 
                "parent_id": parent_idx,
                "probability": prob
            })

        # --- STAGE 4: SERIALIZATION & SVG ---
        final_result = make_serializable({"nodes": node_list, "edges": final_edges})
        svg_data = self.generate_technical_svg_string(final_result["nodes"], final_result["edges"])

        return final_result, svg_data