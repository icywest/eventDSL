// src/components/AstNode.jsx
/**
 * Recursive component to render a JSON AST tree.
 *
 * Expected structure (from backend model_to_dict):
 * {
 *   "__type__": "Model",
 *   "forms": [ ... ],
 *   "init": { ... },
 *   ...
 * }
 */

import React from "react";

export function AstNode({ node }) {
  // Null or undefined nodes
  if (node === null || node === undefined) {
    return <span>null</span>;
  }

  // Primitive values (string, number, boolean)
  if (typeof node !== "object") {
    return <span>{String(node)}</span>;
  }

  // Arrays are rendered as a list of child nodes
  if (Array.isArray(node)) {
    return (
      <ul
        style={{
          marginLeft: "1rem",
          borderLeft: "1px solid #555",
          paddingLeft: "0.5rem",
        }}
      >
        {node.map((child, index) => (
          <li key={index}>
            <AstNode node={child} />
          </li>
        ))}
      </ul>
    );
  }

  // Object nodes: one title with type and children as key/value pairs
  const typeName = node.__type__ || "Object";

  const entries = Object.entries(node).filter(
    ([key]) => key !== "__type__"
  );

  return (
    <div style={{ marginBottom: "0.4rem" }}>
      <div style={{ fontWeight: "bold" }}>{typeName}</div>
      {entries.length > 0 && (
        <ul
          style={{
            marginLeft: "1rem",
            borderLeft: "1px dashed #777",
            paddingLeft: "0.5rem",
          }}
        >
          {entries.map(([key, value]) => (
            <li key={key}>
              <span style={{ fontStyle: "italic" }}>{key}: </span>
              <AstNode node={value} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
