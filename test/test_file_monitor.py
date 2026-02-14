import unittest
import os
import shutil
from pathlib import Path
from src.file_monitor import FileMonitor


class TestFileMonitor(unittest.TestCase):

    def setUp(self):
        """Set up test environment before each test"""
        self.test_dir = "test_folder"
        os.makedirs(self.test_dir, exist_ok=True)

        # Create initial file
        with open(os.path.join(self.test_dir, "test.txt"), "w") as f:
            f.write("hello")

        # Initialize monitor
        self.monitor = FileMonitor(self.test_dir)
        self.monitor.scan()  # create baseline

    def tearDown(self):
        """Clean up test environment after each test"""
        shutil.rmtree(self.test_dir)

    def test_hash_consistency(self):
        """Test that same file generates same hash"""
        file_path = Path(os.path.join(self.test_dir, "test.txt"))
        hash1 = self.monitor.calculate_hash(file_path)
        hash2 = self.monitor.calculate_hash(file_path)

        self.assertEqual(hash1, hash2)

    def test_file_creation(self):
        """Test detection of newly created file"""
        with open(os.path.join(self.test_dir, "new.txt"), "w") as f:
            f.write("new file")

        self.monitor.check_changes()

        self.assertTrue("new.txt" in self.monitor.file_hashes)

    def test_file_modification(self):
        """Test detection of modified file"""
        file_path = os.path.join(self.test_dir, "test.txt")

        old_hash = self.monitor.file_hashes["test.txt"]

        with open(file_path, "w") as f:
            f.write("modified content")

        self.monitor.check_changes()
        new_hash = self.monitor.file_hashes["test.txt"]

        self.assertNotEqual(old_hash, new_hash)

    def test_baseline_file_created(self):
        """Test that baseline file exists after scan"""
        baseline_path = os.path.join(self.test_dir, ".baseline.txt")
        self.assertTrue(os.path.exists(baseline_path))


    def test_file_deletion(self):
        """Test detection of deleted file"""
        os.remove(os.path.join(self.test_dir, "test.txt"))

        self.monitor.check_changes()

        self.assertTrue("test.txt" not in self.monitor.file_hashes)


if __name__ == "__main__":
    unittest.main()
