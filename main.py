"""Simple desktop launcher for the auto-log workflows."""

import os
import re
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog


PROJECT_DIR = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_DIR / "input.txt"
YEAR_PATTERN = re.compile(r"^\d{4}-\d{4}$")


class AutoLogApp(tk.Tk):
    """A small, extensible menu for the project scripts."""

    def __init__(self):
        super().__init__()
        self.title("TRIO Tools")
        self.minsize(680, 475)
        self.resizable(True, True)

        self.status = tk.StringVar(value="by Christian J :)")
        self._build_menu()

    def _build_menu(self):
        self.menu_frame = tk.Frame(self, padx=28, pady=24)
        self.menu_frame.pack(fill="both", expand=True)

        tk.Label(
            self.menu_frame,
            text="TRIO tools",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            self.menu_frame,
            text="Choose the task you want to run.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 18))

        self._add_action(
            "Update logs from scratch",
            "Read each student in input.txt and write their appointments to the log.",
            self.run_log_update,
        )
        self._add_action(
            "Add a new school-year tab",
            "Create and prepare a new year tab for every student log.",
            self.add_school_year,
        )
        self._add_action(
            "Update student IDs",
            "View, add, remove, or reorder the IDs saved in input.txt.",
            self.show_input_editor,
        )

        tk.Label(
            self.menu_frame,
            textvariable=self.status,
            anchor="w",
            fg="#555555",
        ).pack(fill="x", pady=(16, 0))

    def _add_action(self, title, description, command):
        card = tk.Frame(self.menu_frame, bd=1, relief="solid", padx=16, pady=12)
        card.pack(fill="x", pady=5)

        tk.Label(card, text=title, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(card, text=description, justify="left", wraplength=570).pack(
            anchor="w", pady=(3, 9)
        )
        tk.Button(card, text=title, command=command, padx=12).pack(anchor="e")

    def run_log_update(self):
        ready = messagebox.askokcancel(
            "Start log update?",
            "Before continuing, make sure the appointment site is in browser tab 1 "
            "and the student-log sheet is in browser tab 2.\n\n"
            "The script will use the IDs currently saved in input.txt.",
        )
        if ready:
            self._launch([sys.executable, "main.py"], "Log update started in a separate window.")

    def add_school_year(self):
        year = simpledialog.askstring(
            "New school year",
            "Enter the school year (for example, 2027-2028):",
            parent=self,
        )
        if year is None:
            return
        year = year.strip()
        if not YEAR_PATTERN.fullmatch(year):
            messagebox.showerror(
                "Invalid school year",
                "Use the format YYYY-YYYY, for example 2027-2028.",
                parent=self,
            )
            return

        ready = messagebox.askokcancel(
            "Add school-year tabs?",
            "Make sure the required browser tabs and sheet are open before continuing.",
            parent=self,
        )
        if ready:
            self._launch(
                [sys.executable, "-m", "addTab", year],
                f"Creating {year} tabs in a separate window.",
            )

    def show_input_editor(self):
        self.menu_frame.pack_forget()
        self.editor_frame = tk.Frame(self, padx=28, pady=24)
        self.editor_frame.pack(fill="both", expand=True)

        tk.Label(
            self.editor_frame,
            text="Student IDs",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            self.editor_frame,
            text="Enter one student ID per line. These are the IDs used by both workflows.",
        ).pack(anchor="w", pady=(2, 12))

        self.input_text = tk.Text(self.editor_frame, height=15, wrap="none", undo=True)
        self.input_text.pack(fill="both", expand=True)
        self.input_text.insert("1.0", self._read_input_file())

        controls = tk.Frame(self.editor_frame, pady=12)
        controls.pack(fill="x")
        tk.Button(controls, text="Back", command=self.show_menu).pack(side="left")
        tk.Button(controls, text="Save student IDs", command=self.save_input_file, padx=12).pack(
            side="right"
        )

    def show_menu(self):
        self.editor_frame.destroy()
        self.menu_frame.pack(fill="both", expand=True)

    def _read_input_file(self):
        try:
            return INPUT_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def save_input_file(self):
        # Normalize blank lines while retaining the one-ID-per-line file format.
        student_ids = [line.strip() for line in self.input_text.get("1.0", "end-1c").splitlines()]
        content = "\n".join(student_id for student_id in student_ids if student_id)
        if content:
            content += "\n"

        INPUT_FILE.write_text(content, encoding="utf-8")
        self.status.set(f"Saved {len(content.splitlines())} student IDs to input.txt.")
        messagebox.showinfo("Saved", "input.txt has been updated.", parent=self)

    def _launch(self, command, message):
        options = {"cwd": PROJECT_DIR}
        if os.name == "nt":
            # addTab.py may prompt for a year when run outside this launcher;
            # a separate console keeps any script messages visible.
            options["creationflags"] = subprocess.CREATE_NEW_CONSOLE

        try:
            subprocess.Popen(command, **options)
        except OSError as error:
            messagebox.showerror("Could not start workflow", str(error), parent=self)
            return

        self.status.set(message)


if __name__ == "__main__":
    AutoLogApp().mainloop()
