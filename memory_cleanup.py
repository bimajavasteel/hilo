import os
import psutil
import torch

def cleanup_gpu():
    """Cleans up GPU memory usage."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        torch.cuda.reset_peak_memory_stats()
    print("[INFO] GPU memory and resources have been cleaned up.")

def cleanup_ffmpeg():
    """Terminates any running FFmpeg processes."""
    for process in psutil.process_iter(attrs=['pid', 'name']):
        try:
            if "ffmpeg" in process.info['name'].lower():
                print(f"[INFO] Terminating FFmpeg process: PID {process.info['pid']}")
                process.terminate()  # Graceful shutdown
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # Process may have already been killed

def cleanup_all():
    """Performs full system cleanup."""
    cleanup_gpu()
    cleanup_ffmpeg()
    print("[INFO] Full system cleanup completed.")

if __name__ == "__main__":
    cleanup_all()
