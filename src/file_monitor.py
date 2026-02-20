from pathlib import Path
import hashlib
import time
from datetime import datetime
from cryptography.fernet import Fernet
import logging

# Files to ignore during monitoring
IGNORE_FILES = [".baseline.txt", ".DS_Store", "Thumbs.db", ".key.key", "monitor.log"]


class FileMonitor:
    """Monitors a directory or a single file for creation, deletion, and modification."""

    def __init__(self, path: str, baseline_file: str = None, logger=print):
        self.path = Path(path).resolve()
        self.logger = logger
        self.file_hashes = {}

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

        # 🔐 Encryption Key Handling
        self.key_file = self.directory / ".key.key"

        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as kf:
                kf.write(key)
        else:
            with open(self.key_file, "rb") as kf:
                key = kf.read()

        self.cipher = Fernet(key)

        # 📁 Logging setup (forensic log)
        logging.basicConfig(
            filename=self.directory / "monitor.log",
            level=logging.INFO,
            format="%(asctime)s - %(message)s"
        )

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
            logging.error(f"Hashing failed for {filepath}: {e}")
            return ""

    # 🔐 Encrypted baseline loading
    def load_baseline(self):
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "rb") as f:
                    encrypted_data = f.read()

                decrypted_data = self.cipher.decrypt(encrypted_data).decode()

                for line in decrypted_data.splitlines():
                    path, filehash = line.strip().split("|", 1)
                    self.file_hashes[path] = filehash

            except Exception as e:
                self.logger(f"[ERROR] Loading baseline failed: {e}")
                logging.error(f"Loading baseline failed: {e}")

    # 🔐 Encrypted baseline saving
    def save_baseline(self):
        try:
            data = "\n".join(
                f"{path}|{filehash}"
                for path, filehash in self.file_hashes.items()
            )

            encrypted_data = self.cipher.encrypt(data.encode())

            with open(self.baseline_file, "wb") as f:
                f.write(encrypted_data)

        except Exception as e:
            self.logger(f"[ERROR] Saving baseline failed: {e}")
            logging.error(f"Saving baseline failed: {e}")

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

        self.file_hashes = {
            str(f.relative_to(self.directory)): self.calculate_hash(f)
            for f in files
        }

        baseline_exists = self.baseline_file.exists()
        self.save_baseline()

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if baseline_exists:
            message = f"[{ts}] [INFO] Baseline updated for {len(files)} file(s)"
        else:
            message = f"[{ts}] [INFO] Baseline created for {len(files)} file(s)"

        self.logger(message)
        logging.info(message)

        save_msg = f"[{ts}] [INFO] Baseline saved at: {self.baseline_file}"
        self.logger(save_msg)
        logging.info(save_msg)

    def check_changes(self):
        """Check for created, deleted, or modified files."""

        current = {
            str(f.relative_to(self.directory)): self.calculate_hash(f)
            for f in self._get_files()
        }

        old = set(self.file_hashes)
        new = set(current)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Created
        for f in new - old:
            message = f"[{ts}] [CREATED] {f}"
            self.logger(message)
            logging.info(message)

        # Deleted
        for f in old - new:
            message = f"[{ts}] [DELETED] {f}"
            self.logger(message)
            logging.info(message)

        # Modified
        for f in old & new:
            if self.file_hashes[f] != current[f]:
                message = f"[{ts}] [MODIFIED] {f}"
                self.logger(message)
                logging.info(message)

        self.file_hashes = current
        self.save_baseline()