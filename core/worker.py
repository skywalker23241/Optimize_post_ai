import os
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal

from core.processor import SEOProcessor


class WorkerThread(QThread):
    progress_updated = pyqtSignal(int, int)       # current, total
    file_processed = pyqtSignal(str, bool, str)    # filename, success, message
    log_message = pyqtSignal(str)                   # log text
    finished_all = pyqtSignal(int, int, int)        # total, success, failed

    def __init__(self, processor: SEOProcessor, input_dir: str, output_dir: str):
        super().__init__()
        self.processor = processor
        self.input_dir = input_dir
        self.output_dir = output_dir
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{timestamp}] {msg}")

    def run(self):
        html_files = []
        for root, _dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.lower().endswith(".html"):
                    html_files.append(os.path.join(root, file))

        total = len(html_files)
        if total == 0:
            self._log("No HTML files found in the input folder.")
            self.finished_all.emit(0, 0, 0)
            return

        self._log(f"Found {total} HTML file(s) to process")
        self._log(f"Input:  {self.input_dir}")
        self._log(f"Output: {self.output_dir}")
        self._log("-" * 50)

        os.makedirs(self.output_dir, exist_ok=True)

        success_count = 0
        fail_count = 0

        for i, file_path in enumerate(html_files):
            if self._cancelled:
                self._log("Processing cancelled by user.")
                break

            filename = os.path.basename(file_path)
            self._log(f"Processing: {filename}")
            self.progress_updated.emit(i, total)

            result = self.processor.process_file(file_path)

            if result.success:
                rel_path = os.path.relpath(file_path, self.input_dir)
                base, ext = os.path.splitext(rel_path)
                output_path = os.path.join(self.output_dir, f"{base}_optimized{ext}")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result.optimized_html)

                self._log(f"  OK — saved to {os.path.basename(output_path)}")
                self.file_processed.emit(filename, True, "Success")
                success_count += 1
            else:
                self._log(f"  FAILED — {result.message}")
                if result.original_counts:
                    self._log(f"  Original counts: {result.original_counts}")
                if result.optimized_counts:
                    self._log(f"  Optimized counts: {result.optimized_counts}")
                self.file_processed.emit(filename, False, result.message)
                fail_count += 1

        self.progress_updated.emit(total, total)
        self._log("-" * 50)
        self._log(f"Done — {success_count} succeeded, {fail_count} failed, {total} total")
        self.finished_all.emit(total, success_count, fail_count)
