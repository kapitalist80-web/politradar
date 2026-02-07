import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import AddBusiness from "./pages/AddBusiness";
import Alerts from "./pages/Alerts";
import BusinessDetail from "./pages/BusinessDetail";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Monitoring from "./pages/Monitoring";
import Parliamentarians from "./pages/Parliamentarians";
import ParliamentarianProfile from "./pages/ParliamentarianProfile";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import Votes from "./pages/Votes";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/add" element={<AddBusiness />} />
                <Route path="/business/:id" element={<BusinessDetail />} />
                <Route path="/parliamentarians" element={<Parliamentarians />} />
                <Route path="/parliamentarian/:personNumber" element={<ParliamentarianProfile />} />
                <Route path="/votes" element={<Votes />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
