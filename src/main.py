import argparse
import time
from src.file_monitor import FileMonitor

def run_cli():
    from src.file_monitor import FileMonitor
    import time

    path = input("Enter directory or file to monitor: ").strip()
    monitor = FileMonitor(path)

    while True:
        print("\n--- File Integrity Monitor (CLI) ---")
        print("1. Create / Update Baseline")
        print("2. Check Changes Once")
        print("3. Start Monitoring")
        print("4. Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            monitor.scan()

        elif choice == "2":
            monitor.check_changes()

        elif choice == "3":
            print("Monitoring... Press Ctrl+C to stop")
            try:
                while True:
                    monitor.check_changes()
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopped monitoring.")

        elif choice == "4":
            print("Exiting...")
            break

        else:
            print("Invalid option. Try again.")


def run_gui():
    """Run the file monitor in GUI mode."""
    import tkinter as tk
    from src.gui import FileMonitorGUI

    root = tk.Tk()
    app = FileMonitorGUI(root)
    root.mainloop()

def main():
    parser = argparse.ArgumentParser(description="File Integrity Monitor")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--gui", action="store_true", help="Run in GUI mode")
    args = parser.parse_args()

    if args.gui:
        run_gui()
    elif args.cli:
        run_cli()
    else:
        print("Please specify --cli or --gui. Example:\n"
              "  python -m src.main --cli\n"
              "  python -m src.main --gui")

if __name__ == "__main__":
    main()
