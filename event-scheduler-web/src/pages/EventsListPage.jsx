import React, { useEffect, useState } from "react";
import { fetchEvents } from "../api";

export default function EventsListPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchEvents();
      setEvents(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div style={{ padding: "1.5rem" }}>
      <h2>Scheduled Events</h2>
      {loading && <p>Loading events...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && events.length === 0 && <p>No events yet.</p>}

      {events.length > 0 && (
        <table border="1" cellPadding={6} style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Date</th>
              <th>Time</th>
              <th>Name</th>
              <th>Requester</th>
              <th>Campus</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.id}>
                <td>{ev.id}</td>
                <td>{ev.date}</td>
                <td>
                  {ev.start_time}–{ev.end_time}
                </td>
                <td>{ev.name}</td>
                <td>{ev.requester_type}</td>
                <td>{ev.campus_id}</td>
                <td>{ev.location}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
