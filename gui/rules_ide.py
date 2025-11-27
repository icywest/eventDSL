# event_dsl/gui/rules_ide.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from textx.exceptions import TextXError
from parsers.rules import parse_rules_from_text, debug_print_rules
from db import init_db


DEFAULT_DSL_TEMPLATE = """initialize_runtime = yes

event_form Academics {
    event_name {
        visible  = yes
        required = yes
        label    = "Event Title"
    }

    campus_id {
        visible  = yes
        required = yes
        label    = "Campus"
    }

    event_date {
        visible  = yes
        required = yes
        label    = "Date of the Event"
    }

    location {
        visible  = yes
        required = yes
        options  = [PellasRoom, NewAuditorium, SB116, LibraryRoom, REC, Other]
    }

    submit_button {
        text = "Request Academic Event"
    }
}

event_form Students {
    event_name {
        visible  = yes
        required = yes
        label    = "Event Name"
    }

    campus_id {
        visible  = yes
        required = yes
    }

    event_date {
        visible  = yes
        required = yes
    }

    location {
        visible  = yes
        required = yes
        options  = [REC, LibraryRoom, Other]
    }

    submit_button {
        text = "Request Student Event"
    }
}
"""


class RulesIDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Event Rules DSL IDE")
        self.geometry("900x600")
        self._create_widgets()

    def _create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Open .evrules", command=self.open_file).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        ttk.Button(toolbar, text="Save .evrules", command=self.save_file).pack(
            side=tk.LEFT, padx=5, pady=5
        )
        ttk.Button(
            toolbar, text="Validate & Save to DB", command=self.validate_and_save
        ).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(
            toolbar, text="Print Rules (Console)", command=debug_print_rules
        ).pack(side=tk.LEFT, padx=5, pady=5)

        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(text_frame, wrap=tk.NONE, undo=True)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.text.yview
        )
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=scroll_y.set)

        self.text.insert("1.0", DEFAULT_DSL_TEMPLATE)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Event Rules DSL", "*.evrules"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".evrules",
            filetypes=[("Event Rules DSL", "*.evrules"), ("All Files", "*.*")],
        )
        if not file_path:
            return
        try:
            content = self.text.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Rules saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

    def validate_and_save(self):
        dsl_text = self.text.get("1.0", tk.END)
        try:
            count = parse_rules_from_text(dsl_text)
        except TextXError as e:
            messagebox.showerror("DSL Error", f"Syntax/semantic error:\n{e}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{e}")
            return

        messagebox.showinfo(
            "Success",
            f"✅ DSL parsed correctly.\n"
            f"{count} event_form rule(s) saved into the database.",
        )


def run_ide():
    init_db()
    app = RulesIDE()
    app.mainloop()
