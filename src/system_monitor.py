import psutil
import time
import threading
import logging

class SystemMonitor(threading.Thread):
    def __init__(self, interval=5, log_file="system_monitor.log"):
        super().__init__()
        self.interval = interval
        self.log_file = log_file
        self.running = True  # Stop flag

        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - CPU: %(cpu)s%%, MEM: %(mem)s%%, GPU: %(gpu)s%%, TEMP: %(temp)s°C",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def stop(self):
        """Stops the monitor loop."""
        self.running = False

    def run(self):
        try:
            while self.running:
                cpu_usage = psutil.cpu_percent()
                mem_usage = psutil.virtual_memory().percent
                gpu_usage = self.get_gpu_usage()
                gpu_temp = self.get_gpu_temperature()

                log_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - CPU: {cpu_usage}%, MEM: {mem_usage}%, GPU: {gpu_usage}%, TEMP: {gpu_temp}°C"
                print(log_entry)  # Print to terminal
                logging.info(log_entry)  # Log to file

                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n[INFO] Stopping System Monitor...")
        finally:
            print("[INFO] Monitor stopped.")

    def get_gpu_usage(self):
        """Returns GPU usage percentage (if available)."""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            usage = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            pynvml.nvmlShutdown()
            return usage
        except Exception:
            return "N/A"

    def get_gpu_temperature(self):
        """Returns GPU temperature (if available)."""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            pynvml.nvmlShutdown()
            return temp
        except Exception:
            return "N/A"

# Run system monitor
if __name__ == "__main__":
    monitor = SystemMonitor(interval=2)
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C detected. Stopping...")
        monitor.stop()
        monitor.join()
        print("[INFO] SystemMonitor stopped successfully.")
