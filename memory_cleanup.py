import torch
import gc
import cv2

def cleanup_memory():
    """Frees up GPU memory, releases OpenCV resources, and resets CUDA device."""
    try:
        # Clear PyTorch CUDA memory
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        # Force Python garbage collection
        gc.collect()

        # Release OpenCV resources if used
        cv2.destroyAllWindows()

        # Reset CUDA device (optional, for thorough cleanup)
        torch.cuda.device(0)
        torch.cuda.reset_max_memory_allocated()
        torch.cuda.reset_max_memory_cached()

        print("[INFO] GPU memory and resources have been cleaned up.")
    except Exception as e:
        print(f"[ERROR] Memory cleanup failed: {e}")

def cleanup_onnx_session(session):
    """Explicitly cleans up ONNX runtime session."""
    try:
        session.end_profiling()
        del session
    except NameError:
        pass

def cleanup_gui(root):
    """Closes Tkinter or other GUI elements safely."""
    try:
        root.quit()
        root.destroy()
    except Exception as e:
        print(f"[ERROR] GUI cleanup failed: {e}")

if __name__ == "__main__":
    cleanup_memory()
