import json
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from db import (
    init_db,
    get_form_rules_for_requester,
    save_event,
)

from validators.scheduling import (
    validate_event_scheduling,
    SchedulingValidationError,
)

# Opcional: calendario
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


class TimePicker(ttk.Frame):
    """
    Selector de hora HH:MM con Combobox para horas y minutos.
    """

    def __init__(self, parent, default_hour: str = "08", default_minute: str = "00"):
        super().__init__(parent)

        self.hour_var = tk.StringVar(value=default_hour)
        self.min_var = tk.StringVar(value=default_minute)

        hours = [f"{h:02d}" for h in range(0, 24)]
        minutes = [f"{m:02d}" for m in range(0, 60, 15)]  # cada 15 minutos

        self.hour_cb = ttk.Combobox(
            self,
            textvariable=self.hour_var,
            values=hours,
            width=3,
            state="readonly",
        )
        self.hour_cb.grid(row=0, column=0, padx=(0, 2))

        self.min_cb = ttk.Combobox(
            self,
            textvariable=self.min_var,
            values=minutes,
            width=3,
            state="readonly",
        )
        self.min_cb.grid(row=0, column=1)

    def get(self) -> str:
        h = self.hour_var.get().strip()
        m = self.min_var.get().strip()
        if not h or not m:
            return ""
        return f"{h}:{m}"

    def reset(self):
        self.hour_var.set("")
        self.min_var.set("")


class AddEventApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Add Event (End User)")
        self.geometry("600x500")

        self.current_fields = {}   # field_name -> widget
        self.current_rules = []    # cache de reglas

        self._create_widgets()

    def _create_widgets(self):
        # ----- Top: requester type -----
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="Requester type:").pack(side=tk.LEFT)

        self.requester_var = tk.StringVar(value="Students")
        requester_combo = ttk.Combobox(
            top_frame,
            textvariable=self.requester_var,
            values=["Academics", "Students"],
            state="readonly",
            width=20,
        )
        requester_combo.pack(side=tk.LEFT, padx=5)
        requester_combo.bind("<<ComboboxSelected>>", self.on_requester_change)

        load_btn = ttk.Button(
            top_frame,
            text="Load Form",
            command=self.load_form_for_current_requester,
        )
        load_btn.pack(side=tk.LEFT, padx=5)

        # ----- Middle: form -----
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ----- Bottom: submit -----
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        submit_btn = ttk.Button(
            bottom_frame,
            text="Add Event",
            command=self.on_submit,
        )
        submit_btn.pack(side=tk.RIGHT)

        # Cargar Students por defecto
        self.load_form_for_current_requester()

    # ---------------- Helpers formulario ---------------- #

    def clear_form(self):
        for child in self.form_frame.winfo_children():
            child.destroy()
        self.current_fields.clear()
        self.current_rules.clear()

    def load_form_for_current_requester(self):
        self.clear_form()

        requester_type = self.requester_var.get()
        rules = get_form_rules_for_requester(requester_type)

        if not rules:
            ttk.Label(
                self.form_frame,
                text="No form rules found for this requester type.\n"
                     "Ask the admin to configure the DSL rules.",
                foreground="red",
            ).pack(pady=20)
            return

        self.current_rules = rules

        row_index = 0
        for (field_name, visible, required, label, options_json) in rules:
            if not visible:
                continue

            field_label = label if label else field_name

            lbl = ttk.Label(
                self.form_frame,
                text=field_label + (":" if not field_label.endswith(":") else ""),
            )
            lbl.grid(row=row_index, column=0, sticky="w", padx=5, pady=5)

            widget = self._create_widget_for_field(
                field_name=field_name,
                options_json=options_json,
            )
            widget.grid(row=row_index, column=1, sticky="ew", padx=5, pady=5)

            self.current_fields[field_name] = widget
            row_index += 1

        self.form_frame.columnconfigure(1, weight=1)

    def _create_widget_for_field(self, field_name: str, options_json: Optional[str]):
        options = None
        if options_json:
            try:
                options = json.loads(options_json)
            except Exception:
                options = None

        if options:
            combo_var = tk.StringVar()
            combo = ttk.Combobox(
                self.form_frame,
                textvariable=combo_var,
                values=options,
                state="readonly",
            )
            return combo

        if field_name == "event_date":
            if DateEntry is not None:
                return DateEntry(self.form_frame, date_pattern="yyyy-mm-dd")
            else:
                entry = ttk.Entry(self.form_frame)
                entry.insert(0, "YYYY-MM-DD")
                return entry

        elif field_name in ("start_time", "end_time"):
            return TimePicker(self.form_frame)

        else:
            return ttk.Entry(self.form_frame)

    # ---------------- Submit ---------------- #

    def on_requester_change(self, event):
        self.load_form_for_current_requester()

    def on_submit(self):
        requester_type = self.requester_var.get()

        # Recoger valores de campos visibles
        values = {}
        for field_name, widget in self.current_fields.items():
            val = self._get_widget_value(widget)
            values[field_name] = val

        # Campos required visibles
        required_visible_fields = set()
        for (field_name, visible, required, _label, _options_json) in self.current_rules:
            if visible and required and field_name in self.current_fields:
                required_visible_fields.add(field_name)

        # Validación de requeridos al enviar
        missing = [
            f
            for f in required_visible_fields
            if f not in values or not str(values[f]).strip()
        ]

        if missing:
            messagebox.showerror(
                "Missing data",
                "Please fill all required fields:\n- " + "\n- ".join(missing),
            )
            return

        # Mapear a columnas de events
        try:
            name = values.get("event_name", "").strip()
            campus_id_raw = values.get("campus_id", "").strip()
            event_date = values.get("event_date", "").strip()
            start_time = values.get("start_time", "").strip()
            end_time = values.get("end_time", "").strip()
            location = values.get("location", "").strip()

            if not name:
                raise ValueError("event_name is required in the DSL for this form.")

            if not campus_id_raw:
                raise ValueError("campus_id is required in the DSL for this form.")
            campus_id = int(campus_id_raw)

        except ValueError as e:
            messagebox.showerror("Validation error", str(e))
            return

        # Validación de scheduling
        try:
            validate_event_scheduling(
                name=name,
                requester_type=requester_type,
                campus_id=campus_id,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
            )
        except SchedulingValidationError as e:
            messagebox.showerror("Scheduling conflict", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected scheduling error:\n{e}")
            return

        # Guardar en BD
        try:
            save_event(
                name=name,
                requester_type=requester_type,
                campus_id=campus_id,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                location=location,
            )
        except Exception as e:
            messagebox.showerror("Database error", f"Could not save event:\n{e}")
            return

        messagebox.showinfo("Success", "✅ Event added successfully.")

        # Limpiar widgets visibles
        for widget in self.current_fields.values():
            self._reset_widget(widget)

    def _get_widget_value(self, widget):
        if hasattr(widget, "get"):
            return widget.get()
        return ""

    def _reset_widget(self, widget):
        if hasattr(widget, "reset"):
            widget.reset()
        elif isinstance(widget, ttk.Combobox):
            widget.set("")
        elif hasattr(widget, "delete"):
            widget.delete(0, tk.END)


def run_add_event_app():
    init_db()
    app = AddEventApp()
    app.mainloop()
