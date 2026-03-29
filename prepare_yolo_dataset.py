"""
prepare_yolo_dataset.py
========================
Splits a CVAT YOLO 1.1 export into the Ultralytics directory structure
with an 80/20 train/validation split, and generates data.yaml.

Usage:
    python prepare_yolo_dataset.py

The script expects the following input layout (CVAT YOLO 1.1 export):
    granny_square_yolo/
    ├── obj_train_data/
    │   ├── IMG_xxx.jpg
    │   ├── IMG_xxx.txt
    │   └── ...
    ├── obj.names
    ├── obj.data
    └── train.txt

Output:
    dataset/
    ├── images/
    │   ├── train/
    │   └── val/
    ├── labels/
    │   ├── train/
    │   └── val/
    └── data.yaml
"""

import os
import random
import shutil
import yaml
from pathlib import Path

# ──────────────────────────── Configuration ────────────────────────────
SEED = 42
TRAIN_RATIO = 0.80  # 80 % train, 20 % val

# Paths (relative to the project root)
PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_ROOT / "granny_square_yolo" / "obj_train_data"
NAMES_FILE = PROJECT_ROOT / "granny_square_yolo" / "obj.names"
OUTPUT_DIR = PROJECT_ROOT / "dataset"

# Image extensions to look for (in priority order)
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"]


# ──────────────────────────── Helpers ──────────────────────────────────
def read_class_names(names_path: Path) -> list[str]:
    """Read class names from the obj.names file (one per line)."""
    with open(names_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def find_image_for_label(label_path: Path) -> Path | None:
    """Return the matching image path for a label file, or None."""
    for ext in IMAGE_EXTENSIONS:
        img_path = label_path.with_suffix(ext)
        if img_path.exists():
            return img_path
    return None


def create_directory_structure(base: Path) -> dict[str, Path]:
    """Create the YOLO directory tree and return a dict of paths."""
    dirs = {
        "images_train": base / "images" / "train",
        "images_val":   base / "images" / "val",
        "labels_train": base / "labels" / "train",
        "labels_val":   base / "labels" / "val",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def generate_data_yaml(
    output_dir: Path,
    class_names: list[str],
) -> Path:
    """Write data.yaml for Ultralytics training."""
    yaml_path = output_dir / "data.yaml"
    data = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "nc": len(class_names),
        "names": class_names,
    }
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return yaml_path


# ──────────────────────────── Main ─────────────────────────────────────
def main() -> None:
    random.seed(SEED)

    # 1. Read class names
    class_names = read_class_names(NAMES_FILE)
    print(f"[INFO] Found {len(class_names)} classes: {class_names}")

    # 2. Collect matched image + label pairs
    label_files = sorted(SOURCE_DIR.glob("*.txt"))
    pairs: list[tuple[Path, Path]] = []

    for lf in label_files:
        img = find_image_for_label(lf)
        if img is not None:
            pairs.append((img, lf))
        else:
            print(f"[WARN] No image found for label: {lf.name}  — skipping")

    if not pairs:
        print("[ERROR] No image+label pairs found. Make sure your .jpg images")
        print("        are in granny_square_yolo/obj_train_data/ next to the .txt files.")
        return

    print(f"[INFO] Found {len(pairs)} image+label pairs")

    # 3. Shuffle & split
    random.shuffle(pairs)
    split_idx = int(len(pairs) * TRAIN_RATIO)
    train_pairs = pairs[:split_idx]
    val_pairs = pairs[split_idx:]

    print(f"[INFO] Split → train: {len(train_pairs)}, val: {len(val_pairs)}")

    # 4. Create output directories
    dirs = create_directory_structure(OUTPUT_DIR)

    # 5. Copy files
    for img, lbl in train_pairs:
        shutil.copy2(img, dirs["images_train"] / img.name)
        shutil.copy2(lbl, dirs["labels_train"] / lbl.name)

    for img, lbl in val_pairs:
        shutil.copy2(img, dirs["images_val"] / img.name)
        shutil.copy2(lbl, dirs["labels_val"] / lbl.name)

    print(f"[INFO] Copied files to {OUTPUT_DIR}")

    # 6. Generate data.yaml
    yaml_path = generate_data_yaml(OUTPUT_DIR, class_names)
    print(f"[INFO] Generated {yaml_path}")
    print()
    print("─" * 50)
    print("data.yaml contents:")
    print("─" * 50)
    with open(yaml_path) as f:
        print(f.read())

    print("[DONE] Dataset is ready for training.")


if __name__ == "__main__":
    main()
