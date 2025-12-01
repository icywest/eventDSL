import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import AddEventPage from "./pages/AddEventPage";
import EventsListPage from "./pages/EventsListPage";
import RulesAstViewer from "./pages/RulesAstViewer";
import EventsAstViewer from "./pages/EventsAstViewer";
import RulesIdePage from "./pages/RulesIdePage";

import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="main-nav">
        <Link to="/">Add Event</Link>
        <Link to="/events">View Events</Link>
        <Link to="/rules-ide">Domain Expert View</Link>
      </nav>

      <Routes>
        <Route path="/" element={<AddEventPage />} />
        <Route path="/events" element={<EventsListPage />} />
        <Route path="/rules-ast" element={<RulesAstViewer />} />
        <Route path="/events-ast" element={<EventsAstViewer />} />
        <Route path="/rules-ide" element={<RulesIdePage />} />
      </Routes>
    </BrowserRouter>
  );
}