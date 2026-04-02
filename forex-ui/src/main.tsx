import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./layout/Layout";
import Dashboard from "./pages/Dashboard";
import Macro from "./pages/Macro";
import News from "./pages/News";
import Calendar from "./pages/Calendar";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/macro" element={<Macro />} />
        <Route path="/news" element={<News />} />
        <Route path="/calendar" element={<Calendar />} />
      </Routes>
    </Layout>
  </BrowserRouter>
);