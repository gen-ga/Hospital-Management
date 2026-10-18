import React from 'react';
import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom';
import LoginPage from '../Pages/LoginPage';
import RegisterPage from '../Pages/RegisterPage';
import AppLayout from '../Components/AppLayout';
import WorkspacePage from '../Pages/WorkspacePage';
import { useHospital } from '../context/HospitalContext';

const roleHome = (role: string) => `/${role.toLowerCase()}/dashboard`;
const RequireAuth = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useHospital(); const { role } = useParams();
  if (loading) return <div className="app-loading">Loading your secure workspace…</div>;
  if (!user) return <Navigate to="/login" replace />;
  const actualRole = user.role.toLowerCase();
  if (role !== actualRole) return <Navigate to={roleHome(actualRole)} replace />;
  return <>{children}</>;
};
const Entry = () => { const { user, loading } = useHospital(); return loading ? <div className="app-loading">Loading your secure workspace…</div> : <Navigate to={user ? roleHome(user.role) : '/login'} replace />; };

const AppRoutes = () => <BrowserRouter><Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />
  <Route path="/" element={<Entry />} />
  <Route path="/:role" element={<RequireAuth><AppLayout /></RequireAuth>}><Route path="*" element={<WorkspacePage />} /></Route>
  <Route path="*" element={<Entry />} />
</Routes></BrowserRouter>;
export default AppRoutes;
