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

COLORS = {
    "background": "#F4F7FB",
    "surface": "#FFFFFF",
    "border": "#DCE4F0",
    "heading": "#152B4F",
    "text": "#34435C",
    "muted": "#66758D",
    "accent": "#2563EB",
    "accent_active": "#1D4ED8",
    "header": "#17355F",
    "header_text": "#F8FAFC",
    "header_muted": "#C9D7E9",
}

FONT = "Segoe UI"


class AutoLogApp(tk.Tk):
    """A small, extensible menu for the project scripts."""

    def __init__(self):
        super().__init__()
        self.title("TRIO Tools")
        self.geometry("760x560")
        self.minsize(700, 520)
        self.resizable(True, True)
        self.configure(bg=COLORS["background"])

        self.status = tk.StringVar(value="by Christian J :)")
        self._build_menu()

    def _build_menu(self):
        self.menu_frame = tk.Frame(self, bg=COLORS["background"])
        self.menu_frame.pack(fill="both", expand=True)

        self._build_header(self.menu_frame)

        content = tk.Frame(self.menu_frame, bg=COLORS["background"], padx=30, pady=24)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text="What would you like to do?",
            bg=COLORS["background"],
            fg=COLORS["heading"],
            font=(FONT, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            content,
            text="Choose a workflow to begin. Your student IDs are managed in one place.",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=(FONT, 10),
        ).pack(anchor="w", pady=(3, 16))

        self._add_action(
            content,
            "Update logs from scratch",
            "Read each student in input.txt and write their appointments to the log.",
            self.run_log_update,
            "Start update",
        )
        self._add_action(
            content,
            "Add a new school-year tab",
            "Create and prepare a new year tab for every student log.",
            self.add_school_year,
            "Add year tab",
        )
        self._add_action(
            content,
            "Update student IDs",
            "View, add, remove, or reorder the IDs saved in input.txt.",
            self.show_input_editor,
            "Manage IDs",
        )

        status_bar = tk.Frame(content, bg=COLORS["background"], pady=8)
        status_bar.pack(fill="x", pady=(10, 0))
        tk.Label(
            status_bar,
            textvariable=self.status,
            anchor="w",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=(FONT, 9),
        ).pack(fill="x")

    def _build_header(self, parent):
        header = tk.Frame(parent, bg=COLORS["header"], padx=30, pady=22)
        header.pack(fill="x")
        tk.Label(
            header,
            text="TRIO Tools",
            bg=COLORS["header"],
            fg=COLORS["header_text"],
            font=(FONT, 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Student log workflows, all in one place",
            bg=COLORS["header"],
            fg=COLORS["header_muted"],
            font=(FONT, 10),
        ).pack(anchor="w", pady=(3, 0))

    def _add_action(self, parent, title, description, command, button_label):
        card = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=18,
            pady=15,
        )
        card.pack(fill="x", pady=5)

        text_area = tk.Frame(card, bg=COLORS["surface"])
        text_area.pack(side="left", fill="both", expand=True)

        tk.Label(
            text_area,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["heading"],
            font=(FONT, 11, "bold"),
        ).pack(anchor="w")
        tk.Label(
            text_area,
            text=description,
            justify="left",
            wraplength=430,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=(FONT, 9),
        ).pack(anchor="w", pady=(4, 0))
        self._button(card, button_label, command).pack(side="right", padx=(18, 0), pady=4)

    def _button(self, parent, text, command, secondary=False):
        if secondary:
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=COLORS["surface"],
                fg=COLORS["heading"],
                activebackground="#E8EEF7",
                activeforeground=COLORS["heading"],
                highlightthickness=0,
                bd=0,
                padx=14,
                pady=8,
                font=(FONT, 9, "bold"),
                cursor="hand2",
            )
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=COLORS["accent"],
            fg="white",
            activebackground=COLORS["accent_active"],
            activeforeground="white",
            highlightthickness=0,
            bd=0,
            padx=14,
            pady=8,
            font=(FONT, 9, "bold"),
            cursor="hand2",
        )

    def run_log_update(self):
        ready = messagebox.askokcancel(
            "Start log update?",
            "Before continuing, make sure the appointment site is in browser tab 1 "
            "and the student-log sheet is in browser tab 2.\n\n"
            "The script will use the IDs currently saved in input.txt.",
        )
        if ready:
            self._launch([sys.executable, "log.py"], "Log update started in a separate window.")

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
        self.editor_frame = tk.Frame(self, bg=COLORS["background"])
        self.editor_frame.pack(fill="both", expand=True)

        self._build_header(self.editor_frame)
        content = tk.Frame(self.editor_frame, bg=COLORS["background"], padx=30, pady=24)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text="Student IDs",
            bg=COLORS["background"],
            fg=COLORS["heading"],
            font=(FONT, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            content,
            text="Enter one student ID per line. These are the IDs used by both workflows.",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=(FONT, 10),
        ).pack(anchor="w", pady=(3, 14))

        self.input_text = tk.Text(
            content,
            height=15,
            wrap="none",
            undo=True,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["heading"],
            relief="flat",
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
            highlightthickness=1,
            padx=12,
            pady=10,
            font=("Consolas", 10),
        )
        self.input_text.pack(fill="both", expand=True)
        self.input_text.insert("1.0", self._read_input_file())

        controls = tk.Frame(content, bg=COLORS["background"], pady=14)
        controls.pack(fill="x")
        self._button(controls, "Back", self.show_menu, secondary=True).pack(side="left")
        self._button(controls, "Save student IDs", self.save_input_file).pack(side="right")

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
