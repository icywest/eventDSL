import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import AddEventPage from "./pages/AddEventPage";
import EventsListPage from "./pages/EventsListPage";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="main-nav">
        <Link to="/">Add Event</Link>
        <Link to="/events">View Events</Link>
      </nav>

      <Routes>
        <Route path="/" element={<AddEventPage />} />
        <Route path="/events" element={<EventsListPage />} />
      </Routes>
    </BrowserRouter>
  );
}