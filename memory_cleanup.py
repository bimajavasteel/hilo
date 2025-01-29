import torch
import gc
import cv2
import warnings

def cleanup_memory():
    """Frees up GPU memory, releases OpenCV resources, and resets CUDA device."""
    try:
        # Suppress PyTorch FutureWarnings
        warnings.filterwarnings("ignore", category=FutureWarning)

        # Clear PyTorch CUDA memory
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

        # Reset CUDA device (removes peak memory warnings)
        torch.cuda.device(0)
        torch.cuda.reset_peak_memory_stats()  # Replaces deprecated calls

        # Force Python garbage collection
        gc.collect()

        # Release OpenCV resources if used
        cv2.destroyAllWindows()

        print("[INFO] GPU memory and resources have been cleaned up.")
    except Exception as e:
        print(f"[ERROR] Memory cleanup failed: {e}")

if __name__ == "__main__":
    cleanup_memory()
