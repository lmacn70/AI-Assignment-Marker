import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import queue

from document_reader import read_document
from ai_marker import mark_student_submission


class AssignmentMarkerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("AI Assignment Marker")
        self.geometry("850x580")
        self.minsize(780, 540)

        self.student_folder = tk.StringVar()
        self.task_sheet = tk.StringVar()
        self.criteria_sheet = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.supported_extensions = [".docx", ".pdf", ".txt"]

        self.message_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker_thread = None
        self.is_marking = False

        self._build_layout()
        self._update_run_button_state()
        self.after(200, self._process_queue)

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        title_frame = ttk.Frame(self, padding=(20, 16, 20, 8))
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.columnconfigure(0, weight=1)

        ttk.Label(
            title_frame,
            text="AI Assignment Marker",
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_frame,
            text="Select the task sheet, criteria sheet, student submissions folder, and output folder.",
            font=("Arial", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        main_frame = ttk.Frame(self, padding=(20, 8, 20, 12))
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)

        self._add_path_selector(main_frame, 0, "Student submissions folder", self.student_folder, self._select_student_folder)
        self._add_path_selector(main_frame, 1, "Assignment task sheet", self.task_sheet, self._select_task_sheet)
        self._add_path_selector(main_frame, 2, "Criteria marking sheet", self.criteria_sheet, self._select_criteria_sheet)
        self._add_path_selector(main_frame, 3, "Output folder", self.output_folder, self._select_output_folder)

        self.file_count_label = ttk.Label(
            main_frame,
            text="No student submission folder selected.",
            font=("Arial", 10, "italic"),
        )
        self.file_count_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(16, 8))
        button_frame.columnconfigure(0, weight=1)

        self.clear_button = ttk.Button(button_frame, text="Clear Selections", command=self._clear_selections)
        self.clear_button.grid(row=0, column=0, sticky="w")

        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._cancel_marking, state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=(0, 8), sticky="e")

        self.run_button = ttk.Button(button_frame, text="Run Marking", command=self._start_marking_thread)
        self.run_button.grid(row=0, column=2, sticky="e")

        log_frame = ttk.LabelFrame(main_frame, text="Status", padding=(10, 8))
        log_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.status_text = tk.Text(
            log_frame,
            height=10,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.status_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.status_text.configure(yscrollcommand=scrollbar.set)

        bottom_frame = ttk.Frame(self, padding=(20, 0, 20, 16))
        bottom_frame.grid(row=2, column=0, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(bottom_frame, mode="determinate", maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew")

        self.progress_label = ttk.Label(bottom_frame, text="Ready")
        self.progress_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self._log("Application started. Select the required files and folders.")

    def _add_path_selector(self, parent, row, label, variable, command):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)

        ttk.Entry(parent, textvariable=variable, state="readonly").grid(
            row=row, column=1, sticky="ew", padx=(12, 8), pady=6
        )

        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, sticky="e", pady=6)

    def _select_student_folder(self):
        folder = filedialog.askdirectory(title="Select student submissions folder")
        if folder:
            self.student_folder.set(folder)
            self._log(f"Student submissions folder selected: {folder}")
            self._update_submission_count()
            self._update_run_button_state()

    def _select_task_sheet(self):
        file_path = filedialog.askopenfilename(
            title="Select assignment task sheet",
            filetypes=[
                ("Supported documents", "*.docx *.pdf *.txt"),
                ("Word documents", "*.docx"),
                ("PDF documents", "*.pdf"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.task_sheet.set(file_path)
            self._log(f"Task sheet selected: {file_path}")
            self._update_run_button_state()

    def _select_criteria_sheet(self):
        file_path = filedialog.askopenfilename(
            title="Select criteria marking sheet",
            filetypes=[
                ("Supported documents", "*.docx *.pdf *.txt"),
                ("Word documents", "*.docx"),
                ("PDF documents", "*.pdf"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.criteria_sheet.set(file_path)
            self._log(f"Criteria sheet selected: {file_path}")
            self._update_run_button_state()

    def _select_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)
            self._log(f"Output folder selected: {folder}")
            self._update_run_button_state()

    def _clear_selections(self):
        if self.is_marking:
            messagebox.showwarning("Marking running", "Cancel marking before clearing selections.")
            return

        self.student_folder.set("")
        self.task_sheet.set("")
        self.criteria_sheet.set("")
        self.output_folder.set("")
        self.file_count_label.configure(text="No student submission folder selected.")
        self.progress["value"] = 0
        self.progress_label.configure(text="Ready")
        self._log("Selections cleared.")
        self._update_run_button_state()

    def _get_supported_submission_files(self, folder):
        files = []
        for extension in self.supported_extensions:
            files.extend(folder.glob(f"*{extension}"))
        return sorted(files)

    def _update_submission_count(self):
        folder = Path(self.student_folder.get())
        if not folder.exists():
            self.file_count_label.configure(text="Student submissions folder does not exist.")
            return

        submissions = self._get_supported_submission_files(folder)
        self.file_count_label.configure(text=f"{len(submissions)} supported student submission file(s) found.")

    def _update_run_button_state(self):
        required_paths = [
            self.student_folder.get(),
            self.task_sheet.get(),
            self.criteria_sheet.get(),
            self.output_folder.get(),
        ]

        if all(required_paths) and not self.is_marking:
            self.run_button.configure(state="normal")
        else:
            self.run_button.configure(state="disabled")

    def _start_marking_thread(self):
        if self.is_marking:
            return

        self.cancel_event.clear()
        self.is_marking = True

        self.run_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.clear_button.configure(state="disabled")

        self.worker_thread = threading.Thread(target=self._run_marking_worker, daemon=True)
        self.worker_thread.start()

    def _cancel_marking(self):
        self.cancel_event.set()
        self._queue_log("Cancel requested. Waiting for the current AI call to finish...")

    def _run_marking_worker(self):
        try:
            student_folder = Path(self.student_folder.get())
            task_sheet = Path(self.task_sheet.get())
            criteria_sheet = Path(self.criteria_sheet.get())
            output_folder = Path(self.output_folder.get())

            if not student_folder.exists():
                self.message_queue.put(("error", "The student submissions folder does not exist."))
                return

            if not task_sheet.exists():
                self.message_queue.put(("error", "The assignment task sheet does not exist."))
                return

            if not criteria_sheet.exists():
                self.message_queue.put(("error", "The criteria marking sheet does not exist."))
                return

            if not output_folder.exists():
                self.message_queue.put(("error", "The output folder does not exist."))
                return

            submissions = self._get_supported_submission_files(student_folder)

            if not submissions:
                self.message_queue.put(("error", "No supported student submissions were found."))
                return

            self._queue_log("Starting marking process...")

            self._queue_log("Reading criteria sheet...")
            criteria_text = read_document(criteria_sheet)
            self._queue_log(f"Criteria sheet read successfully: {len(criteria_text)} characters")

            self._queue_log(f"Found {len(submissions)} student submission(s).")

            # Testing mode: only process the first student.
            submissions_to_process = submissions[:1]

            for index, submission in enumerate(submissions_to_process, start=1):
                if self.cancel_event.is_set():
                    self._queue_log("Marking cancelled before next student.")
                    break

                self._queue_log(f"Processing {index}/{len(submissions_to_process)}: {submission.name}")

                student_name = submission.stem

                self._queue_log(f"Sending {student_name} to AI marker...")

                marking_result = mark_student_submission(
                    task_file_path=task_sheet,
                    criteria_text=criteria_text,
                    student_file_path=submission,
                    student_name=student_name,
                )

                self._queue_log(f"AI marking complete for {student_name}")
                self._queue_log(f"Overall grade: {marking_result.get('overall_grade', 'No grade returned')}")
                self._queue_log(f"Overall feedback: {marking_result.get('overall_feedback', 'No feedback returned')}")

                progress_value = int((index / len(submissions_to_process)) * 100)
                self.message_queue.put(("progress", progress_value, f"Processed {index} of {len(submissions_to_process)} submissions"))

            if self.cancel_event.is_set():
                self._queue_log("Marking cancelled.")
            else:
                self._queue_log("AI marking test complete.")

        except Exception as error:
            self.message_queue.put(("error", str(error)))

        finally:
            self.message_queue.put(("finished",))

    def _queue_log(self, message):
        self.message_queue.put(("log", message))

    def _process_queue(self):
        try:
            while True:
                message = self.message_queue.get_nowait()

                if message[0] == "log":
                    self._log(message[1])

                elif message[0] == "progress":
                    _, value, label = message
                    self.progress["value"] = value
                    self.progress_label.configure(text=label)

                elif message[0] == "error":
                    self._log(f"ERROR: {message[1]}")
                    messagebox.showerror("Error", message[1])

                elif message[0] == "finished":
                    self.is_marking = False
                    self.cancel_button.configure(state="disabled")
                    self.clear_button.configure(state="normal")
                    self.progress_label.configure(text="Complete")
                    self._update_run_button_state()

        except queue.Empty:
            pass

        self.after(200, self._process_queue)

    def _log(self, message):
        self.status_text.configure(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")


if __name__ == "__main__":
    app = AssignmentMarkerApp()
    app.mainloop()

    