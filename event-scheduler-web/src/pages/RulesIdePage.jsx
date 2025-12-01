// src/pages/RulesIdePage.jsx
/**
 * Domain Expert IDE for EVENT RULES DSL.
 *
 * Layout:
 * - Left side: DSL editor used by the domain expert to define rules.
 * - Right side: Tabbed view with:
 *    1) AST: visualization of the parsed model (via /rules-ast).
 *    2) Grammar: reference of what constructs the DSL supports.
 *    3) Manual: narrative explanation of how and why to use the DSL.
 */

import React, { useState } from "react";
import { AstNode } from "../components/AstNode";

const TAB_AST = "AST";
const TAB_GRAMMAR = "GRAMMAR";
const TAB_MANUAL = "MANUAL";

export default function RulesIdePage() {
  /**
   * Initial sample rules DSL code.
   * This can be replaced later with content loaded from file or DB.
   */
  const [code, setCode] = useState(`
    Write rules here!
`);

  const [ast, setAst] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(TAB_AST);

  /**
   * Send the DSL text to the backend and request the AST.
   * Uses:
   *   POST http://localhost:8000/rules-ast
   * Body:
   *   { "code": "<dsl text>" }
   */
  const handleShowAst = async () => {
    setError("");
    setAst(null);
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/rules-ast", {
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

  /**
   * Tab header component for the right side panel.
   */
  const TabHeader = ({ tabId, label }) => (
    <button
      onClick={() => setActiveTab(tabId)}
      style={{
        padding: "0.4rem 0.8rem",
        border: "none",
        borderBottom:
          activeTab === tabId ? "2px solid #4a90e2" : "2px solid transparent",
        background: "transparent",
        color: activeTab === tabId ? "#fff" : "#bbb",
        cursor: "pointer",
        fontSize: "0.9rem",
        fontWeight: activeTab === tabId ? 600 : 400,
      }}
    >
      {label}
    </button>
  );

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.1fr 1fr",
        height: "100vh",
      }}
    >
      {/* Left side: Domain Expert Rules Editor */}
      <div style={{ padding: "1rem", borderRight: "1px solid #333" }}>
        <h2>Domain Expert IDE – EVENT RULES DSL</h2>
        <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
          Use this editor to define <strong>form rules</strong> for different
          requester types (e.g., Academics and Students). The rules control
          which fields appear in the event request form and how they behave.
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

        <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
          <button
            onClick={handleShowAst}
            disabled={loading}
            style={{
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
            <span style={{ color: "#ff6b6b", fontSize: "0.85rem" }}>
              Parsing error: {error}
            </span>
          )}
        </div>
      </div>

      {/* Right side: Tabs (AST / Grammar / Manual) */}
      <div style={{ padding: "1rem", overflowY: "auto" }}>
        {/* Tab headers */}
        <div
          style={{
            display: "flex",
            gap: "0.75rem",
            borderBottom: "1px solid #444",
            marginBottom: "0.75rem",
          }}
        >
          <TabHeader tabId={TAB_AST} label="AST" />
          <TabHeader tabId={TAB_GRAMMAR} label="Grammar" />
          <TabHeader tabId={TAB_MANUAL} label="Manual" />
        </div>

        {/* Tab content */}
        {activeTab === TAB_AST && (
          <div>
            <h3>AST – Abstract Syntax Tree</h3>
            <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
              The AST shows how the DSL code is interpreted by textX. Each node
              corresponds to a grammar element (Model, Initialization,
              EventForm, Field, etc.).
            </p>

            {!ast && !loading && !error && (
              <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
                There is no AST to display yet. Click <em>Show AST</em> after
                entering valid rules in the editor.
              </p>
            )}

            {loading && (
              <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>Parsing…</p>
            )}

            {ast && <AstNode node={ast} />}
          </div>
        )}

        {activeTab === TAB_GRAMMAR && <GrammarTabContent />}

        {activeTab === TAB_MANUAL && <ManualTabContent />}
      </div>
    </div>
  );
}

/**
 * GrammarTabContent displays a concise reference of the EVENT RULES DSL grammar.
 * This is intended as a "what is possible" view for the domain expert.
 */
function GrammarTabContent() {
  return (
    <div>
      <h3>EVENT RULES DSL – Grammar Reference</h3>
      <p style={{ fontSize: "0.9rem", opacity: 0.8 }}>
        This grammar describes <strong>what</strong> can be written in the
        EVENT RULES DSL. It abstracts away implementation details and focuses
        on the valid constructs.
      </p>

      <pre
        style={{
          background: "#111",
          color: "#eee",
          padding: "0.75rem",
          borderRadius: "8px",
          fontSize: "0.85rem",
          overflowX: "auto",
        }}
      >
{`Model:
    init=Initialization
    forms+=EventForm
;

Initialization:
    'initialize_runtime' '=' status=YesNo
;

YesNo:
    'yes' | 'no'
;

EventForm:
    'event_form' requester_type=RequesterType '{'
        fields+=FieldDecl
    '}'
;

RequesterType:
    'Academics' | 'Students'
;

FieldDecl:
    'field' field_name=ID
        'visible' '=' visible=YesNo
        'required' '=' required=YesNo
        ('label' '=' label=STRING)?
        ('options' '=' '[' options+=STRING[','] ']')?
;

Comment:
    /#.*$/   // optional, depending on implementation
;`}
      </pre>

      <p style={{ fontSize: "0.85rem", opacity: 0.8, marginTop: "0.75rem" }}>
        Note: This is a documentation-oriented view of the grammar. The exact
        <code>.tx</code> file in the implementation should be kept as the
        source of truth and synchronized with this reference when changes are
        made.
      </p>
    </div>
  );
}

/**
 * ManualTabContent provides a descriptive "how and why" guide for the DSL.
 * It explains the intent behind the constructs and shows practical examples.
 */
function ManualTabContent() {
  return (
    <div>
      <h3>EVENT RULES DSL – Manual (How and Why)</h3>

      <p style={{ fontSize: "0.9rem" }}>
        The EVENT RULES DSL allows a domain expert to configure the{" "}
        <strong>event request form</strong> without changing the application
        code. By editing the rules, the expert can decide:
      </p>
      <ul style={{ fontSize: "0.9rem" }}>
        <li>Which fields appear in the form for each requester type.</li>
        <li>Which fields are mandatory or optional.</li>
        <li>What labels are shown to the end user.</li>
        <li>Which predefined options are available (for locations, units, etc.).</li>
      </ul>

      <h4>1. Initialization</h4>
      <p style={{ fontSize: "0.9rem" }}>
        The first line must explicitly enable the runtime configuration:
      </p>
      <pre
        style={{
          background: "#111",
          color: "#eee",
          padding: "0.75rem",
          borderRadius: "8px",
          fontSize: "0.85rem",
          overflowX: "auto",
        }}
      >
{`initialize_runtime = yes`}
      </pre>
      <p style={{ fontSize: "0.9rem" }}>
        If this flag is not set to <code>yes</code>, the rules are considered
        disabled and the system will reject the configuration. This acts as a
        safety switch so incomplete drafts do not affect the live form.
      </p>

      <h4>2. Defining an event_form</h4>
      <p style={{ fontSize: "0.9rem" }}>
        Each <code>event_form</code> block defines the form configuration for a
        single <code>requester_type</code>. Currently, the valid requester types
        are <strong>Academics</strong> and <strong>Students</strong>.
      </p>

      <pre
        style={{
          background: "#111",
          color: "#eee",
          padding: "0.75rem",
          borderRadius: "8px",
          fontSize: "0.85rem",
          overflowX: "auto",
        }}
      >
{`event_form Academics {
    ...
}

event_form Students {
    ...
}`}
      </pre>

      <p style={{ fontSize: "0.9rem" }}>
        The system requires exactly one form for each requester type. Defining
        two forms for the same type or missing one of them will cause a
        validation error when parsing the rules.
      </p>

      <h4>3. Defining fields</h4>
      <p style={{ fontSize: "0.9rem" }}>
        Inside each <code>event_form</code>, fields are declared using the{" "}
        <code>field</code> keyword:
      </p>

      <pre
        style={{
          background: "#111",
          color: "#eee",
          padding: "0.75rem",
          borderRadius: "8px",
          fontSize: "0.85rem",
          overflowX: "auto",
        }}
      >
{`field event_name     visible = yes required = yes label = "Event name"
field event_date     visible = yes required = yes
field start_time     visible = yes required = yes
field end_time       visible = yes required = yes
field location       visible = yes required = yes options = ["Pellas Room", "Library"]
field requester_unit visible = yes required = no  options = ["SE Program", "MIS Program"]`}
      </pre>

      <p style={{ fontSize: "0.9rem" }}>
        Each field specifies:
      </p>
      <ul style={{ fontSize: "0.9rem" }}>
        <li>
          <strong>field_name</strong>: internal identifier used by the system
          (e.g., <code>event_name</code>, <code>location</code>).
        </li>
        <li>
          <strong>visible</strong>: whether the field appears in the form (
          <code>yes</code> or <code>no</code>).
        </li>
        <li>
          <strong>required</strong>: whether the user must fill the field (
          <code>yes</code> or <code>no</code>).
        </li>
        <li>
          <strong>label</strong> (optional): custom text shown to the user.
          When omitted, the system falls back to the field name.
        </li>
        <li>
          <strong>options</strong> (optional): predefined choices for that
          field (only allowed for specific fields like{" "}
          <code>location</code> and <code>requester_unit</code>).
        </li>
      </ul>

      <h4>4. Mandatory fields and constraints</h4>
      <p style={{ fontSize: "0.9rem" }}>
        For every <code>event_form</code>, some fields are mandatory and must
        always be present and required:
      </p>
      <ul style={{ fontSize: "0.9rem" }}>
        <li><code>event_name</code></li>
        <li><code>event_date</code></li>
        <li><code>start_time</code></li>
        <li><code>end_time</code></li>
        <li><code>location</code></li>
      </ul>
      <p style={{ fontSize: "0.9rem" }}>
        These fields must be declared with <code>visible = yes</code> and{" "}
        <code>required = yes</code>. If any are missing, or if they are not
        required, the rules file will be rejected during validation.
      </p>

      <h4>5. Typical workflow for the domain expert</h4>
      <ol style={{ fontSize: "0.9rem" }}>
        <li>
          Enable the configuration with{" "}
          <code>initialize_runtime = yes</code>.
        </li>
        <li>
          Define or update <code>event_form Academics</code> and{" "}
          <code>event_form Students</code> according to current policy.
        </li>
        <li>
          For each form, add or remove fields, adjust visibility and required
          status, and update labels and options as needed.
        </li>
        <li>
          Use the AST tab to inspect how the rules are interpreted and verify
          that the structure matches expectations.
        </li>
        <li>
          Save and deploy the rules so that the event request web form uses the
          updated configuration automatically.
        </li>
      </ol>

      <p style={{ fontSize: "0.9rem", marginTop: "0.75rem" }}>
        This manual is intended to give a high-level understanding of{" "}
        <strong>how</strong> to write rules and <strong>why</strong> the DSL
        enforces certain constraints. The grammar tab provides the detailed
        technical specification of what constructs are available.
      </p>
    </div>
  );
}
