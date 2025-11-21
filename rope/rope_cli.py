#!/usr/bin/env python3
import os, sys, argparse, importlib, types
from pathlib import Path

parser = argparse.ArgumentParser(description="Run Rope/Hilo headless (no GUI)")
parser.add_argument("--source", required=True)
parser.add_argument("--target", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--enhancer", choices=["none", "codeformer", "gfpgan", "gpen"], default="none")
parser.add_argument("--keep-fps", action="store_true")
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

ROOT = Path.cwd()

# ====================================================
# 1. AUTO-DETECT MODELS FOLDER
# ====================================================
def autodetect_models():
    candidates = [
        ROOT / "models",
        ROOT.parent / "models",
        ROOT.parent.parent / "models",
        ROOT / "rope" / "models",
    ]

    # Add auto-search for folders containing .onnx/.ckpt/.pth
    for p in ROOT.rglob("*"):
        if p.suffix.lower() in (".onnx", ".ckpt", ".pth"):
            return p.parent

    for c in candidates:
        if c.exists():
            return c
    
    return None

MODELS = autodetect_models()

if MODELS is None:
    print("[ERROR] Tidak dapat menemukan folder model secara otomatis.")
    print("Pastikan ada folder 'models' berisi file .onnx/.ckpt/.pth di repo.")
    sys.exit(3)

print(f"[INFO] Models-folder otomatis = {MODELS}")

os.environ["MODELS_DIR"] = str(MODELS)
os.environ["HEADLESS"] = "1"

# ====================================================
# 2. Pasang dummy tkinter agar GUI tidak jalan
# ====================================================
def patch_tk():
    if "tkinter" in sys.modules:
        return
    dummy = types.ModuleType("tkinter")
    class DummyTk:
        def __init__(self,*a,**k): pass
        def mainloop(self,*a,**k): pass
    dummy.Tk = DummyTk
    sys.modules["tkinter"] = dummy
    sys.modules["tkinter.ttk"] = types.ModuleType("ttk")
    sys.modules["_tkinter"] = types.ModuleType("_tkinter")

patch_tk()

sys.path.insert(0, str(ROOT))

# ====================================================
# 3. Import Coordinator dan panggil run_headless()
# ====================================================
try:
    rope_pkg = importlib.import_module("rope.Coordinator")
    Coordinator = rope_pkg.Coordinator
except Exception:
    print("[ERROR] tidak dapat import rope.Coordinator")
    sys.exit(4)

coord = Coordinator()

if hasattr(coord, "run_headless"):
    print("[INFO] Menjalankan Coordinator.run_headless()")
    coord.run_headless(
        source=args.source,
        target=args.target,
        output=args.output,
        enhancer=args.enhancer,
        keep_fps=args.keep_fps,
        models_dir=str(MODELS)
    )
else:
    print("[ERROR] Coordinator.run_headless() tidak ditemukan.")
    print("Patch Coordinator.py terlebih dahulu.")
    sys.exit(5)

print("[OK] Proses selesai.")
