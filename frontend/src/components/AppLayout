import React, { useState } from "react";
import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  IconActivityHeartbeat,
  IconBell,
  IconCalendarEvent,
  IconChevronRight,
  IconClipboardList,
  IconDashboard,
  IconFileAnalytics,
  IconFirstAidKit,
  IconMenu2,
  IconMedicineSyrup,
  IconStethoscope,
  IconUsers,
  IconX,
  IconBuildingHospital,
  IconLogout,
} from "@tabler/icons-react";
import { Role } from "../data/mockData";
import { Initials } from "./UI";
import { useHospital } from "../context/HospitalContext";
import { apiClient } from "../api";

const navByRole: Record<
  Role,
  { label: string; path: string; icon: React.ReactNode }[]
> = {
  admin: [
    { label: "Dashboard", path: "dashboard", icon: <IconDashboard /> },
    {
      label: "Appointments",
      path: "appointments",
      icon: <IconCalendarEvent />,
    },
    { label: "Patients", path: "patients", icon: <IconUsers /> },
    { label: "Doctors", path: "doctors", icon: <IconStethoscope /> },
    {
      label: "Operations",
      path: "operations",
      icon: <IconActivityHeartbeat />,
    },
    { label: "Medicines", path: "medicines", icon: <IconMedicineSyrup /> },
    {
      label: "Departments",
      path: "departments",
      icon: <IconBuildingHospital />,
    },
    { label: "Reports", path: "reports", icon: <IconFileAnalytics /> },
  ],
  doctor: [
    { label: "Dashboard", path: "dashboard", icon: <IconDashboard /> },
    {
      label: "Appointments",
      path: "appointments",
      icon: <IconCalendarEvent />,
    },
    { label: "My Patients", path: "patients", icon: <IconUsers /> },
    {
      label: "Surgeries & Operations",
      path: "operations",
      icon: <IconActivityHeartbeat />,
    },
    {
      label: "Room Visits",
      path: "room-visits",
      icon: <IconBuildingHospital />,
    },
    { label: "Reports", path: "reports", icon: <IconFileAnalytics /> },
  ],
  patient: [
    { label: "Dashboard", path: "dashboard", icon: <IconDashboard /> },
    {
      label: "My Appointments",
      path: "appointments",
      icon: <IconCalendarEvent />,
    },
    { label: "My Doctor", path: "doctors", icon: <IconStethoscope /> },
    { label: "Medications", path: "medications", icon: <IconMedicineSyrup /> },
    {
      label: "Reports & Documents",
      path: "reports",
      icon: <IconFileAnalytics />,
    },
    { label: "My Profile", path: "profile", icon: <IconClipboardList /> },
  ],
};

const AppLayout = () => {
  const { role: roleParam = "admin" } = useParams();
  const role = (
    ["admin", "doctor", "patient"].includes(roleParam) ? roleParam : "admin"
  ) as Role;
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const { notice, notify, user, setUser } = useHospital();
  const active =
    navByRole[role].find((item) => location.pathname.endsWith(`/${item.path}`))
      ?.label || navByRole[role][0].label;
  const title =
    active === "Dashboard"
      ? `${role === "patient" ? "Patient" : role === "doctor" ? "Doctor" : "Admin"} dashboard`
      : active;
  const person = {
    name: user?.display_name || user?.email || "Account",
    label:
      user?.role === "ADMIN"
        ? "Administrator"
        : user?.role === "DOCTOR"
          ? "Doctor"
          : "Patient",
  };
  const signOut = async () => {
    try {
      await apiClient.logout();
    } finally {
      setUser(null);
      navigate("/login", { replace: true });
    }
  };
  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <span className="brand-mark">
            <IconFirstAidKit size={25} />
          </span>
          <span className="brand-name">HSM</span>
          <button
            className="mobile-close"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation"
          >
            <IconX />
          </button>
        </div>
        <div className="profile-block">
          <Initials name={person.name} className="profile-avatar" />
          <div>
            <strong>{person.name}</strong>
            <span>{person.label}</span>
          </div>
          <span className="online-dot" />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav className="side-nav">
          {navByRole[role].map((item) => (
            <NavLink
              key={item.path}
              to={`/${role}/${item.path}`}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-active" : ""}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.label === "Appointments" && (
                <span className="nav-count">4</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button
            className="nav-item logout-item"
            onClick={() => void signOut()}
          >
            <span className="nav-icon">
              <IconLogout />
            </span>
            <span className="nav-label">Sign out</span>
          </button>
        </div>
      </aside>
      {mobileOpen && (
        <button
          className="mobile-scrim"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation overlay"
        />
      )}
      <main className="main-column">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="menu-toggle"
              onClick={() => {
                if (window.innerWidth <= 800) setMobileOpen(true);
                else setCollapsed(!collapsed);
              }}
              aria-label="Toggle sidebar"
            >
              <IconMenu2 />
            </button>
            <div className="breadcrumb">
              <span>Pages</span>
              <IconChevronRight size={14} />
              <strong>{title}</strong>
            </div>
          </div>
          <div className="topbar-right">
            <button
              className="top-icon notification-button"
              aria-label="Notifications"
              onClick={() => notify("You are all caught up on notifications.")}
            >
              <IconBell size={20} />
              <i />
            </button>
            <span className="role-switch" aria-label="Current workspace">
              {person.label}
            </span>
            <div className="top-user">
              <Initials name={person.name} />
              <span>
                <strong>{person.name}</strong>
                <small>{person.label}</small>
              </span>
            </div>
          </div>
        </header>
        <div className="page-content">
          <Outlet />
        </div>
        <footer className="app-footer">
          <span>© 2026 HSM</span>
          <span>Care, coordinated.</span>
        </footer>
      </main>
      {notice && (
        <div className="toast" role="status">
          <span>✓</span>
          {notice}
        </div>
      )}
    </div>
  );
};
export default AppLayout;
