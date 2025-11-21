#!/usr/bin/env python3
"""
rope_cli.py — menjalankan hilo/rope secara headless (no-GUI) untuk Kaggle/remote.
Cara pakai (contoh):
  python rope_cli.py \
    --source /kaggle/input/source/source.jpg \
    --target /kaggle/input/target/target.mp4 \
    --output /kaggle/working/hasil.mp4 \
    --enhancer codeformer

Catatan:
- Script ini mencoba memanggil Coordinator.run() dari modul rope/Coordinator.py
  setelah menggantikan modul tkinter dengan dummy agar tidak memerlukan X11.
- Jika repo memiliki API run_cli/run_headless, script akan pakai itu bila tersedia.
"""

import os
import sys
import argparse
import importlib
import types
from pathlib import Path

# ---------------------------
# Argparse
# ---------------------------
parser = argparse.ArgumentParser(description="Run Rope/Hilo headless (no GUI)")
parser.add_argument("--source", required=True, help="path ke gambar source (jpg/png)")
parser.add_argument("--target", required=True, help="path ke video/frames target (mp4 atau folder)")
parser.add_argument("--output", required=True, help="path output video (mp4)")
parser.add_argument("--enhancer", choices=["none", "codeformer", "gfpgan", "gpen"], default="none",
                    help="enhancer yang dipakai setelah swap")
parser.add_argument("--models-dir", default="models", help="folder model relatif dari root repo")
parser.add_argument("--keep-fps", action="store_true", help="pertahankan fps asli target")
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

ROOT = Path.cwd()
MODELS = (ROOT / args.models_dir).resolve()

# ---------------------------
# Safety: pastikan folder models ada
# ---------------------------
if not MODELS.exists():
    print(f"[ERROR] models folder tidak ditemukan: {MODELS}")
    print("Letakkan file-file model (onnx/ckpt/pth) ke folder tersebut, atau set --models-dir")
    sys.exit(2)

# ---------------------------
# Monkeypatch tkinter dengan dummy module (menghindari TclError pada headless)
# ---------------------------
def install_dummy_tkinter():
    """
    Pasang modul dummy 'tkinter' dan 'tkinter.ttk' jika belum ada.
    Ini mencegah error _tkinter.TclError: no display name and no $DISPLAY environment variable
    """
    if "tkinter" in sys.modules:
        # sudah terimport — biarkan (kemungkinan GUI mode)
        return

    dummy = types.ModuleType("tkinter")
    # minimal class Tk() yang hanya menahan pemanggilan
    class DummyTk:
        def __init__(self, *a, **k): pass
        def withdraw(self, *a, **k): pass
        def mainloop(self, *a, **k): pass
        def title(self, *a, **k): pass
        def geometry(self, *a, **k): pass
        def destroy(self, *a, **k): pass

    dummy.Tk = DummyTk
    dummy.Frame = object
    dummy.Label = object
    dummy.Button = object
    dummy.Canvas = object
    dummy.StringVar = lambda *a, **k: None
    dummy.IntVar = lambda *a, **k: None

    # simple ttk minimal
    ttk = types.ModuleType("tkinter.ttk")
    ttk.Frame = object
    ttk.Label = object
    ttk.Button = object
    ttk.Entry = object
    ttk.Combobox = object

    sys.modules["tkinter"] = dummy
    sys.modules["tkinter.ttk"] = ttk

    # also guard _tkinter (C extension) name to avoid accidental import attempts
    if "_tkinter" not in sys.modules:
        sys.modules["_tkinter"] = types.ModuleType("_tkinter")

install_dummy_tkinter()

# ---------------------------
# Import repo internals safely
# ---------------------------
# Adjust path: jika repo dalam subfolder (misal kamu menjalankan dari /kaggle/working/hilo)
# pastikan path sudah pada repo root.
# Jika modul-package bernama 'rope' atau 'hilo', coba import keduanya.
sys.path.insert(0, str(ROOT))

# Try candidate package names (prefer 'rope', fallback to repo-specific names)
candidates = ["rope", "hilo", "Hilo", "Rope"]
imported = None
for name in candidates:
    try:
        imported = importlib.import_module(name)
        pkg_name = name
        break
    except Exception:
        imported = None

if imported is None:
    # If package not found, try to import main script file names
    # Search for Coordinator.py in repo
    coord_candidates = list(ROOT.rglob("Coordinator.py"))
    if coord_candidates:
        coord_path = coord_candidates[0]
        coord_dir = str(coord_path.parent)
        sys.path.insert(0, coord_dir)
        try:
            imported = importlib.import_module("Coordinator")
            pkg_name = "Coordinator_module"
        except Exception as e:
            print("[ERROR] Gagal import Coordinator.py:", e)
            imported = None

if imported is None:
    print("[ERROR] Tidak dapat menemukan modul 'rope' atau 'hilo' di repo. Pastikan kamu menjalankan script ini di root repo.")
    sys.exit(3)

if args.verbose:
    print(f"[INFO] berhasil import package: {pkg_name}")

# ---------------------------
# Try to find Coordinator object / class
# ---------------------------
Coordinator = None
# Common places
possible_paths = [
    "rope.Coordinator", "hilo.Coordinator", "Coordinator",
    "rope.coordinator", "hilo.coordinator"
]
for p in possible_paths:
    modname = p.rsplit(".", 1)[0]
    try:
        mod = importlib.import_module(modname)
        if hasattr(mod, "Coordinator"):
            Coordinator = getattr(mod, "Coordinator")
            if args.verbose:
                print(f"[INFO] found Coordinator in {modname}")
            break
    except Exception:
        pass

# fallback: search for classes named 'Coordinator' across modules in package
if Coordinator is None:
    for modname, mod in list(sys.modules.items()):
        try:
            if hasattr(mod, "Coordinator"):
                Coordinator = getattr(mod, "Coordinator")
                if args.verbose:
                    print(f"[INFO] found Coordinator in imported module {modname}")
                break
        except Exception:
            pass

if Coordinator is None:
    print("[WARN] Coordinator class/function tidak ditemukan otomatis. Kita coba panggil module-level run/run_cli/run_headless jika ada.")

# ---------------------------
# Attempt 1: call run_cli/run_headless/run with HEADLESS env
# ---------------------------
os.environ["HEADLESS"] = "1"
os.environ["MODELS_DIR"] = str(MODELS)

# Helper to call functions if exist
def call_if_exists(mod, names, *a, **kw):
    for n in names:
        if hasattr(mod, n):
            fn = getattr(mod, n)
            if callable(fn):
                if args.verbose:
                    print(f"[INFO] memanggil {mod.__name__}.{n}()")
                try:
                    return fn(*a, **kw)
                except TypeError:
                    # try without args
                    return fn()
    return None

# If Coordinator is a class instance or class, instantiate then try run_cli/run_headless
if Coordinator is not None:
    try:
        coord_instance = None
        if isinstance(Coordinator, type):
            try:
                coord_instance = Coordinator()  # coba instantiate tanpa argumen
            except Exception:
                # instantiate with models dir if available
                try:
                    coord_instance = Coordinator(str(MODELS))
                except Exception:
                    coord_instance = None
        else:
            coord_instance = Coordinator

        if coord_instance is not None:
            # Try common method names
            res = None
            for method_name in ["run_cli", "run_headless", "run_headless_pipeline", "start_headless", "start"]:
                if hasattr(coord_instance, method_name):
                    meth = getattr(coord_instance, method_name)
                    if callable(meth):
                        if args.verbose:
                            print(f"[INFO] memanggil Coordinator.{method_name}()")
                        try:
                            res = meth(source=args.source, target=args.target, output=args.output,
                                       enhancer=args.enhancer, models_dir=str(MODELS), keep_fps=args.keep_fps)
                        except TypeError:
                            # fallback no-kwargs
                            res = meth()
                        break

            # fallback: try generic run()
            if res is None and hasattr(coord_instance, "run"):
                try:
                    if args.verbose:
                        print("[INFO] memanggil Coordinator.run() (fallback)")
                    # Some run() reads sys.argv internally; set sys.argv accordingly
                    saved_argv = sys.argv[:]
                    sys.argv = [saved_argv[0],
                                "--source", args.source,
                                "--target", args.target,
                                "--output", args.output,
                                "--enhancer", args.enhancer,
                                "--models-dir", str(MODELS)]
                    res = coord_instance.run()
                    sys.argv = saved_argv
                except Exception as e:
                    print("[ERROR] Coordinator.run() gagal:", e)

            if res is not None:
                print("[OK] Proses selesai (Coordinator returned result).")
                sys.exit(0)

    except Exception as e:
        print("[WARN] Gagal instantiate/panggil Coordinator secara langsung:", e)

# ---------------------------
# Attempt 2: try top-level CLI files (common names)
# ---------------------------
top_candidates = ["run.py", "main.py", "app.py", "server.py", "inference.py", "infer.py"]
for fname in top_candidates:
    p = ROOT / fname
    if p.exists():
        if args.verbose:
            print(f"[INFO] Menemukan {fname}, coba jalankan sebagai modul.")
        # jalankan via subprocess to avoid import issues
        cmd = [
            sys.executable, str(p),
            "--source", args.source,
            "--target", args.target,
            "--output", args.output,
            "--enhancer", args.enhancer,
            "--models-dir", str(MODELS)
        ]
        print("[INFO] menjalankan:", " ".join(cmd))
        os.execv(sys.executable, cmd)

# ---------------------------
# Jika sampai sini belum berhasil, berikan petunjuk manual
# ---------------------------
print("")
print("=============================================")
print("Gagal memanggil pipeline headless otomatis.")
print("Saran:")
print("1) Periksa struktur repo dan cari file yang menjalankan pipeline (run.py, main.py, app.py, Coordinator.py).")
print("2) Jika Coordinator.run() ada tetapi memerlukan argumen, tambahkan wrapper yang memanggilnya.")
print("3) Jika mau, kirim listing: `!ls -R` dan `!sed -n '1,200p' rope/Coordinator.py` ke saya; saya akan buatkan wrapper spesifik.")
print("Contoh cara paling mudah (manual):")
print("  python run.py --source /path/source.jpg --target /path/target.mp4 --output /path/out.mp4 --enhancer codeformer")
print("=============================================")
sys.exit(5)
