import React from "react";

export default function DynamicForm({ fields, values, onChange }) {
  const handleChange = (fieldName) => (e) => {
    onChange(fieldName, e.target.value);
  };

  const renderInput = (field) => {
    const { field_name, required, options } = field;
    const value = values[field_name] || "";

    // Con opciones -> select (ej. location)
    if (options && options.length > 0) {
      return (
        <select
          value={value}
          onChange={handleChange(field_name)}
          required={required}
        >
          <option value="">Select...</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );
    }

    // Campos especiales
    if (field_name === "event_date") {
      return (
        <input
          type="date"
          value={value}
          onChange={handleChange(field_name)}
          required={required}
        />
      );
    }

    if (field_name === "start_time" || field_name === "end_time") {
      return (
        <input
          type="time"
          value={value}
          onChange={handleChange(field_name)}
          required={required}
        />
      );
    }

    if (field_name === "description") {
      return (
        <textarea
          value={value}
          onChange={handleChange(field_name)}
          required={required}
          rows={3}
        />
      );
    }

    // Default: texto
    return (
      <input
        type="text"
        value={value}
        onChange={handleChange(field_name)}
        required={required}
      />
    );
  };

  return (
    <div className="dynamic-form">
      {fields.map((field) => (
        <div key={field.field_name} className="form-row">
          <label>
            {field.label}
            {field.required && " *"}
          </label>
          {renderInput(field)}
        </div>
      ))}
    </div>
  );
}
