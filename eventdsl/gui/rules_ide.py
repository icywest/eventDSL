import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

CODE_ROOT = os.path.dirname(os.path.dirname(__file__))
if CODE_ROOT not in sys.path:
    sys.path.append(CODE_ROOT)

from textx.exceptions import TextXError
from parsers.rules import parse_rules_from_text
from db import init_db, list_form_rules



class RulesIDE(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Event Rules DSL - Domain Expert")
        self.geometry("1000x600")

        self.viewer_tree = None
        self._create_widgets()
        self.refresh_rules_view()

    def _create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # ------- Tab 1: DSL Editor -------
        editor_frame = ttk.Frame(notebook)
        notebook.add(editor_frame, text="DSL Editor")

        toolbar = ttk.Frame(editor_frame)
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

        text_frame = ttk.Frame(editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(text_frame, wrap=tk.NONE, undo=True)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.text.yview
        )
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=scroll_y.set)

        # ------- Tab 2: Rules Viewer -------
        viewer_frame = ttk.Frame(notebook)
        notebook.add(viewer_frame, text="Rules Viewer")

        top_viewer = ttk.Frame(viewer_frame)
        top_viewer.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        ttk.Label(
            top_viewer,
            text="Current rules stored in the database (form_fields):",
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        ttk.Button(
            top_viewer,
            text="Refresh",
            command=self.refresh_rules_view,
        ).pack(side=tk.RIGHT, padx=5)

        tree_frame = ttk.Frame(viewer_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("requester", "field", "visible", "required", "label", "options")
        self.viewer_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
        )

        self.viewer_tree.heading("requester", text="Requester Type")
        self.viewer_tree.heading("field", text="Field Name")
        self.viewer_tree.heading("visible", text="Visible")
        self.viewer_tree.heading("required", text="Required")
        self.viewer_tree.heading("label", text="Label")
        self.viewer_tree.heading("options", text="Options")

        self.viewer_tree.column("requester", width=120, anchor="center")
        self.viewer_tree.column("field", width=120, anchor="center")
        self.viewer_tree.column("visible", width=80, anchor="center")
        self.viewer_tree.column("required", width=80, anchor="center")
        self.viewer_tree.column("label", width=200, anchor="w")
        self.viewer_tree.column("options", width=300, anchor="w")

        self.viewer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y2 = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.viewer_tree.yview
        )
        scroll_y2.pack(side=tk.RIGHT, fill=tk.Y)
        self.viewer_tree.configure(yscrollcommand=scroll_y2.set)

    # ------------ File operations (Editor) ------------ #

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

    # ------------ DSL operations ------------ #

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

        self.refresh_rules_view()

        messagebox.showinfo(
            "Success",
            f"✅ DSL parsed correctly.\n"
            f"{count} event_form rule(s) saved into the database.",
        )

    def refresh_rules_view(self):
        if self.viewer_tree is None:
            return

        for item in self.viewer_tree.get_children():
            self.viewer_tree.delete(item)

        rules = list_form_rules()

        for r in rules:
            requester_type, field_name, visible, required, label, options_json = r
            visible_str = "yes" if visible else "no"
            required_str = "yes" if required else "no"
            options_str = options_json if options_json else ""

            self.viewer_tree.insert(
                "",
                tk.END,
                values=(
                    requester_type,
                    field_name,
                    visible_str,
                    required_str,
                    label or "",
                    options_str,
                ),
            )


def run_ide():
    init_db()
    app = RulesIDE()
    app.mainloop()
