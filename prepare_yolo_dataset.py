"""
prepare_yolo_dataset.py
========================
Splits a CVAT YOLO 1.1 export into the Ultralytics directory structure
with an 80/20 train/validation split, and generates data.yaml.

Usage:
    python prepare_yolo_dataset.py

"""

import os
import random
import shutil
import yaml
from pathlib import Path

# ──────────────────────────── Configuration ────────────────────────────
SEED = 42
TRAIN_RATIO = 0.80 

PROJECT_ROOT = Path(__file__).resolve().parent
# According to your screenshot:
RAW_LABEL_DIR = PROJECT_ROOT / "dataset" / "labels"
RAW_IMAGE_DIR = PROJECT_ROOT / "dataset" / "images"
NAMES_FILE = PROJECT_ROOT / "dataset" / "obj.names"

# We will move organized data here to avoid "folder-in-folder" confusion
EXPORT_DIR = PROJECT_ROOT / "yolo_dataset" 

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"]

# ──────────────────────────── Helpers ──────────────────────────────────
def read_class_names(names_path: Path) -> list[str]:
    with open(names_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def find_image_for_label(label_path: Path) -> Path | None:
    for ext in IMAGE_EXTENSIONS:
        img_path = RAW_IMAGE_DIR / (label_path.stem + ext)
        if img_path.exists():
            return img_path
    return None

def create_directory_structure(base: Path) -> dict[str, Path]:
    dirs = {
        "images_train": base / "train" / "images",
        "images_val":   base / "val" / "images",
        "labels_train": base / "train" / "labels",
        "labels_val":   base / "val" / "labels",
    }
    # Clean previous attempts to avoid mixing old/new data
    if base.exists():
        print(f"[INFO] Cleaning old export directory: {base}")
        shutil.rmtree(base)
        
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def generate_data_yaml(output_dir: Path, class_names: list[str]) -> Path:
    yaml_path = output_dir / "data.yaml"
    # Ultralytics likes 'nc' and 'names'
    data = {
        "path": str(output_dir.resolve()), # Absolute path is most robust
        "train": "train/images",
        "val": "val/images",
        "nc": len(class_names),
        "names": class_names,
    }
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return yaml_path

# ──────────────────────────── Main ─────────────────────────────────────
def main() -> None:
    random.seed(SEED)

    if not NAMES_FILE.exists():
        print(f"[ERROR] Could not find {NAMES_FILE}")
        return

    class_names = read_class_names(NAMES_FILE)
    print(f"[INFO] Found {len(class_names)} classes.")

    # 2. Collect matched pairs
    label_files = list(RAW_LABEL_DIR.glob("*.txt"))
    pairs = []

    for lf in label_files:
        img = find_image_for_label(lf)
        if img:
            pairs.append((img, lf))

    if not pairs:
        print(f"[ERROR] No pairs found in {RAW_IMAGE_DIR} and {RAW_LABEL_DIR}")
        return

    print(f"[INFO] Found {len(pairs)} valid image+label pairs")

    # 3. Shuffle & split
    random.shuffle(pairs)
    split_idx = int(len(pairs) * TRAIN_RATIO)
    train_pairs = pairs[:split_idx]
    val_pairs = pairs[split_idx:]

    # 4. Create structure
    dirs = create_directory_structure(EXPORT_DIR)

    # 5. Copy (safer than move)
    print(f"[INFO] Copying {len(train_pairs)} files to Train...")
    for img, lbl in train_pairs:
        shutil.copy2(img, dirs["images_train"] / img.name)
        shutil.copy2(lbl, dirs["labels_train"] / lbl.name)

    print(f"[INFO] Copying {len(val_pairs)} files to Val...")
    for img, lbl in val_pairs:
        shutil.copy2(img, dirs["images_val"] / img.name)
        shutil.copy2(lbl, dirs["labels_val"] / lbl.name)

    # 6. Generate YAML
    yaml_path = generate_data_yaml(EXPORT_DIR, class_names)
    print(f"[SUCCESS] Dataset ready at: {EXPORT_DIR}")
    print(f"[INFO] data.yaml created. You can now run train_yolo.py")

if __name__ == "__main__":
    main()