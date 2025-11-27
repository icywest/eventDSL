# event_dsl/gui/add_event_view.py

import json
import tkinter as tk
from tkinter import ttk, messagebox

from db import (
    init_db,
    get_form_rules_for_requester,
    save_event,
)

# Opcional: soporte de calendario con tkcalendar
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


class AddEventApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Add Event (End User)")
        self.geometry("600x500")

        self.current_fields = {}   # field_name -> widget
        self.current_rules = []    # cache de reglas usadas

        self._create_widgets()

    def _create_widgets(self):
        # ----- Top: requester type selector -----
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

        # ----- Middle: dynamic form area -----
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ----- Bottom: submit button -----
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        submit_btn = ttk.Button(
            bottom_frame,
            text="Add Event",
            command=self.on_submit,
        )
        submit_btn.pack(side=tk.RIGHT)

        # Cargamos por defecto Students
        self.load_form_for_current_requester()

    # --------------------------------------------------------
    # Helpers para construir el formulario según las reglas
    # --------------------------------------------------------

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

        # Construir una fila por cada campo visible
        for row_index, (field_name, visible, required, label, options_json) in enumerate(
            rules
        ):
            if not visible:
                continue  # solo usamos campos visibles

            field_label = label if label else field_name

            # Etiqueta
            lbl = ttk.Label(self.form_frame, text=field_label + (":" if not field_label.endswith(":") else ""))
            lbl.grid(row=row_index, column=0, sticky="w", padx=5, pady=5)

            # Widget
            widget = self._create_widget_for_field(
                field_name=field_name,
                options_json=options_json,
            )
            widget.grid(row=row_index, column=1, sticky="ew", padx=5, pady=5)

            self.current_fields[field_name] = widget

        # Hacer que la columna 1 se expanda
        self.form_frame.columnconfigure(1, weight=1)

    def _create_widget_for_field(self, field_name: str, options_json: str | None):
        """
        Crea un widget apropiado según el nombre del campo y si tiene options.
        """
        # Si hay opciones, usamos un Combobox
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

        # Si no hay opciones, elegimos según el campo:
        if field_name == "event_date":
            if DateEntry is not None:
                return DateEntry(self.form_frame, date_pattern="yyyy-mm-dd")
            else:
                entry = ttk.Entry(self.form_frame)
                entry.insert(0, "YYYY-MM-DD")
                return entry

        elif field_name in ("start_time", "end_time"):
            entry = ttk.Entry(self.form_frame)
            entry.insert(0, "HH:MM")
            return entry

        else:
            # Campo genérico texto / número
            return ttk.Entry(self.form_frame)

    # --------------------------------------------------------
    # Submit: validar requeridos, mapear a save_event
    # --------------------------------------------------------

    def on_requester_change(self, event):
        self.load_form_for_current_requester()

    def on_submit(self):
        requester_type = self.requester_var.get()

        # Convertir reglas en diccionario rápido de "required"
        required_map = {
            field_name: bool(required)
            for (field_name, _visible, required, _label, _options_json)
            in self.current_rules
        }

        # Recoger valores
        values = {}
        for field_name, widget in self.current_fields.items():
            val = self._get_widget_value(widget)
            values[field_name] = val

        # Validar campos requeridos
        missing = [
            f
            for f, is_required in required_map.items()
            if is_required and (f not in values or not str(values[f]).strip())
        ]

        if missing:
            messagebox.showerror(
                "Missing data",
                "Please fill all required fields:\n- " + "\n- ".join(missing),
            )
            return

        # Mapear a columnas de events:
        # name, requester_type, campus_id, date, start_time, end_time, location
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
            campus_id = int(campus_id_raw)  # puede lanzar ValueError

        except ValueError as e:
            messagebox.showerror("Validation error", str(e))
            return

        # Guardar en DB
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

        # Limpiar campos (solo los básicos, opcional)
        for widget in self.current_fields.values():
            self._reset_widget(widget)

    def _get_widget_value(self, widget):
        # DateEntry and Entry have .get(); Combobox also
        if hasattr(widget, "get"):
            return widget.get()
        return ""

    def _reset_widget(self, widget):
        if isinstance(widget, ttk.Combobox):
            widget.set("")
        elif hasattr(widget, "delete"):
            widget.delete(0, tk.END)


def run_add_event_app():
    init_db()
    app = AddEventApp()
    app.mainloop()
