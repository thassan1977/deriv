import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CaseDetails from "./pages/CaseDetails";

// 1. Add 'export default' here to satisfy ESLint
export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        {/* This route ensures that when you click a case in the table, it loads CaseDetails */}
        <Route path="/case/:caseId" element={<CaseDetails />} />
      </Routes>
    </Router>
  );
}