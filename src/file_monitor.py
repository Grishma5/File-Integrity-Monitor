from pathlib import Path
import hashlib
import time
from datetime import datetime

# Files to ignore during monitoring
IGNORE_FILES = [".baseline.txt", ".DS_Store", "Thumbs.db"]

class FileMonitor:
    """Monitors a directory or a single file for creation, deletion, and modification."""

    def __init__(self, path: str, baseline_file: str = None, logger=print):
        self.path = Path(path).resolve()
        self.logger = logger

        # Detect if path is a file or directory
        if self.path.is_file():
            self.directory = self.path.parent
            self.single_file = True
        else:
            self.directory = self.path
            self.single_file = False

        # Baseline file location
        if baseline_file:
            self.baseline_file = Path(baseline_file).resolve()
        else:
            self.baseline_file = self.directory / ".baseline.txt"

        self.file_hashes = {}
        self.load_baseline()

    def calculate_hash(self, filepath: Path) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.logger(f"[ERROR] Hashing failed for {filepath}: {e}")
            return ""

    def load_baseline(self):
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    for line in f:
                        path, filehash = line.strip().split("|", 1)
                        self.file_hashes[path] = filehash
            except Exception as e:
                self.logger(f"[ERROR] Loading baseline failed: {e}")

    def save_baseline(self):
        try:
            with open(self.baseline_file, "w") as f:
                for path, filehash in self.file_hashes.items():
                    f.write(f"{path}|{filehash}\n")
        except Exception as e:
            self.logger(f"[ERROR] Saving baseline failed: {e}")

    def _get_files(self):
        if self.single_file:
            return [self.path]
        return [
            f for f in self.directory.rglob("*")
            if f.is_file() and f.name not in IGNORE_FILES
        ]

    def scan(self):
        """Create or update baseline with all current files."""
        files = self._get_files()
        self.file_hashes = {f.name: self.calculate_hash(f) for f in files}

        baseline_exists = self.baseline_file.exists()
        self.save_baseline()

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if baseline_exists:
            self.logger(f"[{ts}] [INFO] Baseline updated for {len(files)} file(s)")
        else:
            self.logger(f"[{ts}] [INFO] Baseline created for {len(files)} file(s)")
        self.logger(f"[{ts}] [INFO] Baseline saved at: {self.baseline_file}")

    def check_changes(self):
        """Check for created, deleted, or modified files."""
        current = {f.name: self.calculate_hash(f) for f in self._get_files()}

        old = set(self.file_hashes)
        new = set(current)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for f in new - old:
            self.logger(f"[{ts}] [CREATED] {f}")

        for f in old - new:
            self.logger(f"[{ts}] [DELETED] {f}")

        for f in old & new:
            if self.file_hashes[f] != current[f]:
                self.logger(f"[{ts}] [MODIFIED] {f}")

        self.file_hashes = current
        self.save_baseline()
