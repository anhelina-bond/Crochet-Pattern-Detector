"""
train_yolo.py
==============
Baseline YOLOv11 training script for crochet stitch detection.
Optimized for NVIDIA RTX 3060 (12 GB VRAM) with CUDA.

Usage:
    python train_yolo.py

Prerequisites:
    pip install ultralytics
    Run prepare_yolo_dataset.py first to create the dataset/ folder.
"""

from ultralytics import YOLO
from pathlib import Path

# ──────────────────────────── Configuration ────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_YAML = PROJECT_ROOT / "dataset" / "data.yaml"

# Model — YOLOv11 nano (best starting point for a small dataset)
# Change to "yolo11s.pt" or "yolo11m.pt" if you have more data/VRAM
MODEL_VARIANT = "yolo11n.pt"

# Training hyper-parameters tuned for RTX 3060 (12 GB)
TRAIN_CONFIG = {
    "data":       str(DATA_YAML),
    "epochs":     100,
    "imgsz":      640,
    "batch":      -1,              # auto-batch: Ultralytics picks the largest
                                   # batch size that fits in 12 GB VRAM
    "device":     0,               # first CUDA GPU
    "workers":    8,               # dataloader workers
    "amp":        True,            # mixed-precision (FP16) for speed on RTX 30xx
    "patience":   15,              # early-stopping patience (epochs)
    "optimizer":  "auto",          # AdamW by default
    "lr0":        0.01,            # initial learning rate
    "lrf":        0.01,            # final LR factor (cosine decay)
    "project":    str(PROJECT_ROOT / "runs" / "detect"),
    "name":       "crochet_baseline",
    "exist_ok":   True,            # overwrite previous run with same name
    "pretrained": True,            # use COCO-pretrained weights
    "seed":       42,
    "verbose":    True,
    # Augmentation — sensible defaults for macro crochet photos
    "hsv_h":      0.015,
    "hsv_s":      0.7,
    "hsv_v":      0.4,
    "degrees":    10.0,
    "translate":  0.1,
    "scale":      0.5,
    "flipud":     0.5,            # crochet can be viewed from any angle
    "fliplr":     0.5,
    "mosaic":     1.0,
    "close_mosaic": 10,           # disable mosaic for last 10 epochs
}


# ──────────────────────────── Main ─────────────────────────────────────
def main() -> None:
    # Verify data.yaml exists
    if not DATA_YAML.exists():
        print(f"[ERROR] {DATA_YAML} not found.")
        print("        Run prepare_yolo_dataset.py first to create the dataset.")
        return

    print("=" * 60)
    print("  Crochet Stitch Detection — YOLOv11 Baseline Training")
    print("=" * 60)
    print(f"  Model:   {MODEL_VARIANT}")
    print(f"  Data:    {DATA_YAML}")
    print(f"  Device:  CUDA:0 (RTX 3060)")
    print(f"  Epochs:  {TRAIN_CONFIG['epochs']}")
    print(f"  ImgSize: {TRAIN_CONFIG['imgsz']}")
    print(f"  AMP:     {TRAIN_CONFIG['amp']}")
    print("=" * 60)

    # Load model
    model = YOLO(MODEL_VARIANT)

    # Train
    results = model.train(**TRAIN_CONFIG)

    # Print summary
    print("\n" + "=" * 60)
    print("  Training complete!")
    print(f"  Best weights: {Path(results.save_dir) / 'weights' / 'best.pt'}")
    print(f"  Results dir:  {results.save_dir}")
    print("=" * 60)

    # Run validation on the best model
    print("\n[INFO] Running validation on best weights...")
    best_model = YOLO(str(Path(results.save_dir) / "weights" / "best.pt"))
    val_results = best_model.val(data=str(DATA_YAML), device=0)

    print(f"\n  mAP50:    {val_results.box.map50:.4f}")
    print(f"  mAP50-95: {val_results.box.map:.4f}")


if __name__ == "__main__":
    main()
