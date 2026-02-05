#!/usr/bin/env python3
import os
import sys
import time
import hashlib
import argparse
from pathlib import Path

class FileMonitor:
    """Monitors a directory or a single file for creation, deletion, and modification."""

    def __init__(self, path: str, baseline_file: str = None):
        self.path = Path(path).resolve()

        # Detect if path is a file or directory
        if self.path.is_file():
            self.directory = self.path.parent
            self.single_file = True
            self.single_file_name = self.path.name
        else:
            self.directory = self.path
            self.single_file = False
            self.single_file_name = None

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
            print(f"Error hashing {filepath}: {e}")
            return ""

    def load_baseline(self):
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "|" in line:
                            filepath, filehash = line.split("|", 1)
                            self.file_hashes[filepath] = filehash
            except Exception as e:
                print(f"Error loading baseline: {e}")
                self.file_hashes = {}

    def save_baseline(self):
        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.baseline_file, "w") as f:
                for filepath, filehash in self.file_hashes.items():
                    f.write(f"{filepath}|{filehash}\n")
        except Exception as e:
            print(f"Error saving baseline: {e}")

    def _get_files_to_scan(self):
        if self.single_file:
            return [self.path]
        else:
            return [f for f in self.directory.iterdir() if f.is_file() and f != self.baseline_file]

    def _get_relative_path(self, f: Path) -> str:
        try:
            return str(f.relative_to(self.directory))
        except ValueError:
            return str(f)

    def scan(self):
        files_to_scan = self._get_files_to_scan()
        current_hashes = {}
        for f in files_to_scan:
            rel_path = self._get_relative_path(f)
            current_hashes[rel_path] = self.calculate_hash(f)
        self.file_hashes = current_hashes
        self.save_baseline()
        print(f"Baseline created/updated with {len(self.file_hashes)} file(s).")

    def check_changes(self):
        files_to_scan = self._get_files_to_scan()
        current_hashes = {}
        for f in files_to_scan:
            rel_path = self._get_relative_path(f)
            current_hashes[rel_path] = self.calculate_hash(f)

        old_files = set(self.file_hashes.keys())
        new_files = set(current_hashes.keys())

        added = new_files - old_files
        deleted = old_files - new_files
        modified = {f for f in new_files & old_files if current_hashes[f] != self.file_hashes[f]}

        for f in added:
            print(f"A new file has been CREATED: {self.directory / f}")
        for f in deleted:
            print(f"A file has been DELETED: {self.directory / f}")
        for f in modified:
            print(f"A file has been MODIFIED: {self.directory / f}")

        self.file_hashes = current_hashes
        self.save_baseline()

def main():
    parser = argparse.ArgumentParser(description="File Integrity Monitor")
    parser.add_argument("--dir", default=os.getcwd(), help="Directory or file to monitor (default: current directory)")
    parser.add_argument("--baseline", default=None, help="Path to baseline file (default: same folder as monitored path)")
    parser.add_argument("--scan", action="store_true", help="Create/update baseline for current files")
    parser.add_argument("--check", action="store_true", help="Check for changes against baseline")
    parser.add_argument("--watch", action="store_true", help="Continuously watch for changes")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds (default: 1.0)")
    args = parser.parse_args()

    monitor = FileMonitor(args.dir, args.baseline)

    # Interactive fallback if no flags
    if not args.scan and not args.check and not args.watch:
        ans = input("Would you like to:\n1) Create a new baseline\n2) Proceed with existing baseline\nEnter 1 or 2: ")
        if ans == "1":
            monitor.scan()
        else:
            print(f"Monitoring {args.dir} using existing baseline...")
        print("Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(args.interval)
                monitor.check_changes()
        except KeyboardInterrupt:
            print("\nExiting monitor.")
        return

    # Run scan/check/watch based on flags
    if args.scan:
        monitor.scan()
    if args.check and not args.watch:
        monitor.check_changes()
    if args.watch:
        print(f"Watching {args.dir} for changes. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(args.interval)
                monitor.check_changes()
        except KeyboardInterrupt:
            print("\nExiting monitor.")

if __name__ == "__main__":
    main()
