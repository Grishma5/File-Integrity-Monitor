import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
from datetime import datetime
from src.file_monitor import FileMonitor

class FileMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Integrity Monitor")

        self.monitor = None
        self.watching = False

        tk.Label(root, text="File Integrity Monitor", font=("Arial", 16)).pack(pady=10)

        tk.Button(root, text="Select Directory / File", command=self.select_path).pack(pady=5)
        tk.Button(root, text="Create Baseline", command=self.create_baseline).pack(pady=5)
        tk.Button(root, text="Check Changes", command=self.check_changes).pack(pady=5)
        tk.Button(root, text="Start Watching", command=self.start_watch).pack(pady=5)
        tk.Button(root, text="Stop Watching", command=self.stop_watch).pack(pady=5)

        self.text_area = tk.Text(root, height=12, width=70)
        self.text_area.pack(pady=10)
        self.text_area.config(state='disabled')

    def log(self, message: str):
        """Thread-safe logging with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.root.after(0, lambda: self._append_text(full_message))

    def _append_text(self, message: str):
        self.text_area.config(state='normal')

        # Color-code based on type
        if "[CREATED]" in message:
            tag = "green"
        elif "[DELETED]" in message:
            tag = "red"
        elif "[MODIFIED]" in message:
            tag = "orange"
        else:
            tag = "black"

        self.text_area.insert(tk.END, message + "\n", tag)
        self.text_area.tag_config("green", foreground="green")
        self.text_area.tag_config("red", foreground="red")
        self.text_area.tag_config("orange", foreground="orange")
        self.text_area.tag_config("black", foreground="black")

        self.text_area.see(tk.END)
        self.text_area.config(state='disabled')

    def select_path(self):
        path = filedialog.askdirectory()
        if path:
            self.monitor = FileMonitor(path, logger=self.log)
            self.log(f"Monitoring path: {path}")

    def create_baseline(self):
        if not self.monitor:
            messagebox.showerror("Error", "Select a directory or file first")
            return
        self.monitor.scan()
        self.log("Baseline processed successfully")

    def check_changes(self):
        if not self.monitor:
            messagebox.showerror("Error", "Select a directory or file first")
            return
        self.monitor.check_changes()
        self.log("Checked for changes")

    def watch_loop(self):
        while self.watching:
            self.monitor.check_changes()
            time.sleep(1)

    def start_watch(self):
        if not self.monitor:
            messagebox.showerror("Error", "Select a directory or file first")
            return
        if not self.watching:
            self.watching = True
            threading.Thread(target=self.watch_loop, daemon=True).start()
            self.log("Started monitoring...")

    def stop_watch(self):
        self.watching = False
        self.log("Stopped monitoring")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileMonitorGUI(root)
    root.mainloop()
