import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";               // <-- NOTE: relative path
import "./styles.css";
import { RepoProvider } from "./context/RepoContext";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <RepoProvider>
        <App />
      </RepoProvider>
    </BrowserRouter>
  </React.StrictMode>
);
