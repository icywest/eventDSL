import React, { useEffect, useState } from "react";
import { fetchFormConfig, createEvent } from "../api";
import DynamicForm from "../components/DynamicForm";

export default function AddEventPage() {
  const [requesterType, setRequesterType] = useState("Students");
  const [fields, setFields] = useState([]);
  const [values, setValues] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const loadConfig = async (type) => {
    setLoadingConfig(true);
    setError("");
    setSuccessMsg("");
    try {
      const data = await fetchFormConfig(type);
      setFields(data);
      // reset values for new type
      setValues({});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingConfig(false);
    }
  };

  useEffect(() => {
    loadConfig(requesterType);
  }, [requesterType]);

  const handleChange = (fieldName, value) => {
    setValues((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccessMsg("");

    try {
      const payload = {
        requester_type: requesterType,
        name: values.event_name || "",
        campus_id: parseInt(values.campus_id || "0", 10),
        date: values.event_date || "",
        start_time: values.start_time || "",
        end_time: values.end_time || "",
        location: values.location || "",
      };

      await createEvent(payload);
      setSuccessMsg("Event created successfully ✅");
      setValues({});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "1.5rem" }}>
      <h2>Add Event</h2>

      <div style={{ marginBottom: "1rem" }}>
        <label>
          Requester type:{" "}
          <select
            value={requesterType}
            onChange={(e) => setRequesterType(e.target.value)}
          >
            <option value="Academics">Academics</option>
            <option value="Students">Students</option>
          </select>
        </label>
      </div>

      {loadingConfig && <p>Loading form config...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {successMsg && <p style={{ color: "green" }}>{successMsg}</p>}

      {!loadingConfig && fields.length > 0 && (
        <form onSubmit={handleSubmit}>
          <DynamicForm fields={fields} values={values} onChange={handleChange} />
          <button type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save Event"}
          </button>
        </form>
      )}
    </div>
  );
}
