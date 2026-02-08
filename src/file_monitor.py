from pathlib import Path
import hashlib

class FileMonitor:
    """Monitors a directory or a single file for creation, deletion, and modification."""

    def __init__(self, path: str, baseline_file: str = None, logger=print):
        self.path = Path(path).resolve()
        self.logger = logger  # Can be print() or GUI callback

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
        return [f for f in self.directory.iterdir() if f.is_file() and f != self.baseline_file]

    def scan(self):
        """Create or update baseline for the folder."""
        files = self._get_files()
        for f in files:
            self.file_hashes[f.name] = self.calculate_hash(f)

        baseline_exists = self.baseline_file.exists()
        self.save_baseline()

        if baseline_exists:
            self.logger(f"[INFO] Baseline updated for {len(files)} file(s)")
        else:
            self.logger(f"[INFO] Baseline created for {len(files)} file(s)")
        self.logger(f"[INFO] Baseline saved at: {self.baseline_file}")

    def check_changes(self):
        """Check for created, deleted, or modified files."""
        current = {f.name: self.calculate_hash(f) for f in self._get_files()}

        old_files = set(self.file_hashes)
        new_files = set(current)

        for f in new_files - old_files:
            self.logger(f"[CREATED] {f}")

        for f in old_files - new_files:
            self.logger(f"[DELETED] {f}")

        for f in old_files & new_files:
            if self.file_hashes[f] != current[f]:
                self.logger(f"[MODIFIED] {f}")

        self.file_hashes = current
        self.save_baseline()
