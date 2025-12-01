// src/pages/EventsAstViewer.jsx
/**
 * Page to visualize the AST for the EVENTS DSL (event_dsl.tx).
 *
 * Uses the backend endpoint:
 *   POST http://localhost:8000/events-ast
 * with payload:
 *   { "code": "<events DSL text>" }
 */

import React, { useState } from "react";
import { AstNode } from "../components/AstNode";

export default function EventsAstViewer() {
  // Example events DSL snippet used as initial content
  const [code, setCode] = useState(`# Example events file

event "Advisory Board Meeting" {
    requester_type = Academics
    date          = 2025-11-13
    start         = 09:00
    end           = 12:00
    location      = "Pellas Room"
}

event "React + Git Workshop" {
    requester_type = Students
    date          = 2025-11-25
    start         = 14:00
    end           = 17:00
    location      = "SB116"
}
`);

  const [ast, setAst] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Send the DSL text to the backend and request the AST.
   */
  const handleShowAst = async () => {
    setError("");
    setAst(null);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/events-ast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        const message = data.detail || "DSL parsing error";
        throw new Error(message);
      }

      setAst(data.ast);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        height: "100vh",
      }}
    >
      {/* Left side: DSL input */}
      <div style={{ padding: "1rem", borderRight: "1px solid #333" }}>
        <h2>EVENTS DSL – AST Viewer</h2>
        <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
          Paste or edit your <strong>event_dsl</strong> code and click{" "}
          <em>Show AST</em>.
        </p>

        <textarea
          style={{
            width: "100%",
            height: "70vh",
            background: "#111",
            color: "#eee",
            padding: "0.75rem",
            fontFamily: "monospace",
            fontSize: "0.9rem",
            borderRadius: "8px",
            border: "1px solid #444",
            resize: "vertical",
          }}
          value={code}
          onChange={(e) => setCode(e.target.value)}
        />

        <button
          onClick={handleShowAst}
          disabled={loading}
          style={{
            marginTop: "0.75rem",
            padding: "0.5rem 1.2rem",
            borderRadius: "999px",
            border: "none",
            cursor: loading ? "default" : "pointer",
            fontWeight: 500,
          }}
        >
          {loading ? "Parsing..." : "Show AST"}
        </button>

        {error && (
          <div style={{ marginTop: "0.75rem", color: "#ff6b6b" }}>
            <strong>Parsing error:</strong> {error}
          </div>
        )}
      </div>

      {/* Right side: AST tree */}
      <div style={{ padding: "1rem", overflowY: "auto" }}>
        <h2>AST</h2>

        {!ast && !error && !loading && (
          <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
            No AST to display yet. Submit some events DSL on the left.
          </p>
        )}

        {loading && (
          <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>Parsing...</p>
        )}

        {ast && <AstNode node={ast} />}
      </div>
    </div>
  );
}
