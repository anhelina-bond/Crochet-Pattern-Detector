"""
parse_cvat_to_graph.py
========================
Parses a CVAT for Images 1.1 XML export and converts skeleton annotations
into per-image graph data compatible with PyTorch Geometric.

Each skeleton (stitch) becomes a graph node with features:
    [normalized_center_x, normalized_center_y, class_id]

Directed edges are constructed from the "parent_id" attribute — each stitch
points to its parent stitch, encoding the crochet topology.

Additional attributes saved per graph:
    - node_labels:      stitch type name per node
    - connection_types:  per-node connection type string
    - row_numbers:       per-node row number
    - image_name:        source image filename

Usage:
    python parse_cvat_to_graph.py

Output:
    granny_square_gnn/graph_data.pt   — list of Data objects (one per image)
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import OrderedDict

import torch
from torch_geometric.data import Data

# ──────────────────────────── Configuration ────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
XML_PATH = PROJECT_ROOT / "granny_square_gnn" / "annotations.xml"
OUTPUT_PATH = PROJECT_ROOT / "granny_square_gnn" / "graph_data.pt"

# Class name → integer ID mapping (matches obj.names order)
CLASS_MAP = {
    "sc_stitch":  0,
    "dc_stitch":  1,
    "hdc_stitch": 2,
    "tr_stitch":  3,
    "ch_stitch":  4,
    "sl_st":      5,
}


# ──────────────────────────── Parsing ──────────────────────────────────
def parse_skeleton(skeleton_elem) -> dict:
    """Extract info from a single <skeleton> element."""
    label = skeleton_elem.get("label")

    # Extract base & head keypoints
    base_pt = None
    head_pt = None
    for pts in skeleton_elem.findall("points"):
        coords = pts.get("points")  # "x,y"
        x, y = map(float, coords.split(","))
        if pts.get("label") == "base":
            base_pt = (x, y)
        elif pts.get("label") == "head":
            head_pt = (x, y)

    # Extract attributes
    parent_id_str = ""
    connection_type = "standard"
    row_number = 0
    for attr in skeleton_elem.findall("attribute"):
        name = attr.get("name")
        value = attr.text.strip() if attr.text else ""
        if name == "parent_id":
            parent_id_str = value
        elif name == "connection_type":
            connection_type = value if value else "standard"
        elif name == "row_number":
            row_number = int(value) if value else 0

    # Center = midpoint of base and head
    if base_pt and head_pt:
        cx = (base_pt[0] + head_pt[0]) / 2.0
        cy = (base_pt[1] + head_pt[1]) / 2.0
    elif base_pt:
        cx, cy = base_pt
    elif head_pt:
        cx, cy = head_pt
    else:
        cx, cy = 0.0, 0.0

    return {
        "label": label,
        "class_id": CLASS_MAP.get(label, -1),
        "center_x": cx,
        "center_y": cy,
        "base": base_pt,
        "head": head_pt,
        "parent_id_str": parent_id_str,
        "connection_type": connection_type,
        "row_number": row_number,
    }


def build_graph_for_image(image_elem) -> Data | None:
    """
    Build a PyTorch Geometric Data object for one <image> element.

    CVAT assigns a sequential integer ID to every annotation element
    within an image. Skeleton annotations use these IDs in the parent_id
    attribute. Each skeleton element spans 3 IDs (skeleton + base point
    + head point), so the skeleton-level IDs go 1, 4, 7, 10, ...
    We build a mapping from these CVAT element IDs to our 0-based node
    indices.
    """
    image_name = image_elem.get("name")
    img_w = float(image_elem.get("width"))
    img_h = float(image_elem.get("height"))

    skeletons = image_elem.findall("skeleton")
    if not skeletons:
        return None

    # Parse all skeletons and assign CVAT element IDs
    # CVAT assigns IDs sequentially: skeleton gets id N, its child points
    # get N+1, N+2, etc. So each skeleton with 2 child points consumes 3 IDs.
    parsed = []
    cvat_id = 1  # CVAT element IDs start at 1 within each image
    cvat_id_to_node_idx = {}

    for idx, skel in enumerate(skeletons):
        info = parse_skeleton(skel)
        info["cvat_id"] = cvat_id
        cvat_id_to_node_idx[cvat_id] = idx
        parsed.append(info)

        # Each skeleton has the skeleton element + child point elements
        num_child_points = len(skel.findall("points"))
        cvat_id += 1 + num_child_points  # skeleton + its child points

    num_nodes = len(parsed)

    # Build node features: [norm_cx, norm_cy, class_id]
    node_features = []
    node_labels = []
    connection_types = []
    row_numbers = []

    for info in parsed:
        norm_cx = info["center_x"] / img_w
        norm_cy = info["center_y"] / img_h
        node_features.append([norm_cx, norm_cy, float(info["class_id"])])
        node_labels.append(info["label"])
        connection_types.append(info["connection_type"])
        row_numbers.append(info["row_number"])

    x = torch.tensor(node_features, dtype=torch.float)

    # Build directed edges from parent_id
    src_list = []
    dst_list = []

    for idx, info in enumerate(parsed):
        pid_str = info["parent_id_str"]
        if not pid_str:
            continue
        try:
            parent_cvat_id = int(pid_str)
        except ValueError:
            continue

        if parent_cvat_id in cvat_id_to_node_idx:
            parent_node_idx = cvat_id_to_node_idx[parent_cvat_id]
            # Directed edge: child → parent
            src_list.append(idx)
            dst_list.append(parent_node_idx)

    if src_list:
        edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    # Assemble Data object
    data = Data(
        x=x,
        edge_index=edge_index,
        num_nodes=num_nodes,
    )
    # Additional metadata
    data.node_labels = node_labels
    data.connection_types = connection_types
    data.row_numbers = torch.tensor(row_numbers, dtype=torch.long)
    data.image_name = image_name
    data.image_width = img_w
    data.image_height = img_h

    return data


# ──────────────────────────── Main ─────────────────────────────────────
def main() -> None:
    print(f"[INFO] Parsing {XML_PATH} ...")
    tree = ET.parse(str(XML_PATH))
    root = tree.getroot()

    graphs = []
    total_nodes = 0
    total_edges = 0

    for image_elem in root.findall("image"):
        data = build_graph_for_image(image_elem)
        if data is not None:
            graphs.append(data)
            total_nodes += data.num_nodes
            total_edges += data.edge_index.size(1)

    print(f"[INFO] Parsed {len(graphs)} image graphs")
    print(f"       Total nodes: {total_nodes}")
    print(f"       Total edges: {total_edges}")

    # Save
    torch.save(graphs, str(OUTPUT_PATH))
    print(f"[INFO] Saved graph data to {OUTPUT_PATH}")

    # Print summary for first graph
    if graphs:
        g = graphs[0]
        print(f"\n── Sample graph: {g.image_name} ──")
        print(f"   Nodes: {g.num_nodes}")
        print(f"   Edges: {g.edge_index.size(1)}")
        print(f"   Node features shape: {g.x.shape}")
        print(f"   Edge index shape:    {g.edge_index.shape}")
        print(f"   Stitch types: {set(g.node_labels)}")
        print(f"   First 5 node features (cx, cy, class_id):")
        for i in range(min(5, g.num_nodes)):
            print(f"     [{i}] {g.node_labels[i]:12s} → "
                  f"({g.x[i, 0]:.4f}, {g.x[i, 1]:.4f}, class={int(g.x[i, 2])})")

    print("\n[DONE] Graph data is ready for PyTorch Geometric.")


if __name__ == "__main__":
    main()
