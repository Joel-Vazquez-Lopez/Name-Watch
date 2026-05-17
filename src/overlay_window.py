import queue
import tkinter as tk
from tkinter import ttk
from typing import Dict


class NameWatchOverlay:
    MODES = [
        "Meeting / Lecture",
        "Interview",
        "Video",
    ]

    def __init__(self):
        self.alert_queue = queue.Queue()
        self.current_mode = "Meeting / Lecture"
        self.user_name = ""
        self.do_not_save = False

        self.root = tk.Tk()
        self.root.title("NameWatch Live")
        self.root.geometry("500x390+900+80")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#111111")

        self.title_label = tk.Label(
            self.root,
            text="NameWatch Live",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#111111",
        )
        self.title_label.pack(anchor="w", padx=14, pady=(12, 4))

        controls_frame = tk.Frame(self.root, bg="#111111")
        controls_frame.pack(fill="x", padx=14, pady=(0, 6))

        tk.Label(
            controls_frame,
            text="Mode:",
            font=("Arial", 10),
            fg="#D1D5DB",
            bg="#111111",
        ).pack(side="left")

        self.mode_var = tk.StringVar(value=self.current_mode)
        self.mode_dropdown = ttk.Combobox(
            controls_frame,
            textvariable=self.mode_var,
            values=self.MODES,
            state="readonly",
            width=18,
        )
        self.mode_dropdown.pack(side="left", padx=(6, 10))
        self.mode_dropdown.bind("<<ComboboxSelected>>", self._on_mode_change)

        name_frame = tk.Frame(self.root, bg="#111111")
        name_frame.pack(fill="x", padx=14, pady=(0, 8))

        tk.Label(
            name_frame,
            text="Name:",
            font=("Arial", 10),
            fg="#D1D5DB",
            bg="#111111",
        ).pack(side="left")

        self.name_var = tk.StringVar(value="")
        self.name_entry = tk.Entry(
            name_frame,
            textvariable=self.name_var,
            width=24,
            font=("Arial", 10),
            fg="white",
            bg="#1F2937",
            insertbackground="white",
            relief="flat",
        )
        self.name_entry.pack(side="left", padx=(8, 0))
        self.name_entry.bind("<KeyRelease>", self._on_name_change)

        privacy_frame = tk.Frame(self.root, bg="#111111")
        privacy_frame.pack(fill="x", padx=14, pady=(0, 8))

        self.do_not_save_var = tk.BooleanVar(value=False)
        self.do_not_save_checkbox = tk.Checkbutton(
            privacy_frame,
            text="Do not save notes/memory",
            variable=self.do_not_save_var,
            command=self._on_do_not_save_toggle,
            fg="#D1D5DB",
            bg="#111111",
            selectcolor="#111111",
            activebackground="#111111",
            activeforeground="#FFFFFF",
            font=("Arial", 10),
        )
        self.do_not_save_checkbox.pack(side="left")

        self.status_label = tk.Label(
            self.root,
            text=self._status_text(),
            font=("Arial", 11),
            fg="#9CA3AF",
            bg="#111111",
        )
        self.status_label.pack(anchor="w", padx=14, pady=(0, 10))

        self.alert_label = tk.Label(
            self.root,
            text="Listening. No important moment yet.",
            font=("Arial", 12),
            fg="white",
            bg="#1F2937",
            wraplength=450,
            justify="left",
            padx=12,
            pady=12,
        )
        self.alert_label.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.privacy_label = tk.Label(
            self.root,
            text="Raw audio not stored · full transcript not saved",
            font=("Arial", 9),
            fg="#9CA3AF",
            bg="#111111",
        )
        self.privacy_label.pack(anchor="w", padx=14, pady=(0, 10))

        self.root.after(300, self._poll_alerts)

    def _status_text(self) -> str:
        name_status = f"name: {self.user_name}" if self.user_name else "name off"
        save_status = "not saving" if self.do_not_save else "saving compact notes"
        return f"Status: listening · {self.current_mode} · privacy on · {name_status} · {save_status}"

    def _on_mode_change(self, _event=None):
        self.current_mode = self.mode_var.get()
        self.status_label.config(text=self._status_text())

    def _on_name_change(self, _event=None):
        self.user_name = self.name_var.get().strip()
        self.status_label.config(text=self._status_text())


    def _on_do_not_save_toggle(self):
        self.do_not_save = bool(self.do_not_save_var.get())
        self.status_label.config(text=self._status_text())

    def get_context_mode(self) -> str:
        return self.current_mode

    def get_user_name(self) -> str:
        return self.user_name


    def should_save_outputs(self) -> bool:
        return not self.do_not_save

    def push_alert(self, event: Dict) -> None:
        self.alert_queue.put(event)

    def _poll_alerts(self):
        while not self.alert_queue.empty():
            self._show_event(self.alert_queue.get())
        self.root.after(300, self._poll_alerts)

    def _show_event(self, event: Dict) -> None:
        title = event.get("type", "Important moment")
        summary = event.get("summary", "")
        suggested_answer = event.get("suggested_answer", "")
        action_item = event.get("action_item", "")
        extra = event.get("extra", "")

        text = f"{title}\n\n{summary}"

        if suggested_answer:
            text += f"\n\nSuggested answer:\n{suggested_answer}"

        if action_item:
            text += f"\n\nAction item:\n{action_item}"

        if extra:
            text += f"\n\n{extra}"

        self.alert_label.config(text=text)

    def run(self):
        self.root.mainloop()
