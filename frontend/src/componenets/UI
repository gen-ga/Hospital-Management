import React, { useEffect, useState } from "react";
import {
  IconSearch,
  IconX,
  IconFileDescription,
  IconChevronDown,
  IconChevronLeft,
  IconChevronRight,
} from "@tabler/icons-react";

export interface Column<T> {
  key: keyof T | string;
  label: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}
export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">HSM</p>
        <h1>{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {action && <div className="page-actions">{action}</div>}
    </div>
  );
}
export function Button({
  children,
  onClick,
  variant = "primary",
  type = "button",
  disabled = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "quiet" | "danger";
  type?: "button" | "submit";
  disabled?: boolean;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`button button-${variant}`}
    >
      {children}
    </button>
  );
}
export function Badge({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  const label = String(children);
  const variant =
    tone ||
    (["Due", "Scheduled", "On Leave", "Low stock"].includes(label)
      ? "warning"
      : ["Completed", "Available", "Upcoming"].includes(label)
        ? "success"
        : ["Cancelled", "Absent"].includes(label)
          ? "danger"
          : "neutral");
  return (
    <span className={`badge badge-${variant}`}>
      <i />
      {children}
    </span>
  );
}
export function DataTable<T extends object>({
  columns,
  rows,
  empty = "No records found.",
  onRowClick,
}: {
  columns: Column<T>[];
  rows: T[];
  empty?: string;
  onRowClick?: (row: T) => void;
}) {
  const [page, setPage] = useState(0);
  const pageSize = 5;
  useEffect(() => setPage(0), [rows.length]);
  if (!rows.length)
    return (
      <div className="empty-state">
        <span className="empty-icon">
          <IconFileDescription size={22} />
        </span>
        <strong>No records yet</strong>
        <p>{empty}</p>
      </div>
    );
  const pageCount = Math.ceil(rows.length / pageSize);
  const visible = rows.slice(page * pageSize, (page + 1) * pageSize);
  return (
    <>
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={String(col.key)} className={col.className}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((row, index) => (
              <tr
                key={String((row as { id?: string }).id || index)}
                onClick={() => onRowClick?.(row)}
                className={onRowClick ? "clickable-row" : ""}
              >
                {columns.map((col) => (
                  <td key={String(col.key)} className={col.className}>
                    {col.render
                      ? col.render(row)
                      : String(
                          (row as Record<string, unknown>)[String(col.key)] ??
                            "—",
                        )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > pageSize && (
        <div className="table-pagination">
          <span>
            Showing{" "}
            <strong>
              {page * pageSize + 1}–
              {Math.min(rows.length, (page + 1) * pageSize)}
            </strong>{" "}
            of {rows.length} records
          </span>
          <div>
            <button
              disabled={page === 0}
              onClick={() => setPage((value) => value - 1)}
              aria-label="Previous page"
            >
              <IconChevronLeft size={15} />
            </button>
            <span>
              Page {page + 1} of {pageCount}
            </span>
            <button
              disabled={page + 1 >= pageCount}
              onClick={() => setPage((value) => value + 1)}
              aria-label="Next page"
            >
              <IconChevronRight size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
export function SearchBox({
  value,
  onChange,
  placeholder = "Search records",
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="search-box">
      <IconSearch size={18} />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          aria-label="Clear search"
        >
          <IconX size={15} />
        </button>
      )}
    </label>
  );
}
export function Select({
  value,
  onChange,
  children,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
  label: string;
}) {
  return (
    <label className="filter-select">
      <span className="sr-only">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {children}
      </select>
      <IconChevronDown size={15} />
    </label>
  );
}
export function Modal({
  title,
  children,
  onClose,
  footer,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  footer?: React.ReactNode;
}) {
  React.useEffect(() => {
    const closeOnEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header className="modal-header">
          <h2>{title}</h2>
          <button
            className="icon-button"
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <IconX size={20} />
          </button>
        </header>
        <div className="modal-body">{children}</div>
        {footer && <footer className="modal-footer">{footer}</footer>}
      </section>
    </div>
  );
}
export function StatCard({
  label,
  value,
  note,
  icon,
  tone = "blue",
}: {
  label: string;
  value: string | number;
  note: string;
  icon: React.ReactNode;
  tone?: string;
}) {
  return (
    <article className="stat-card">
      <span className={`stat-icon stat-${tone}`}>{icon}</span>
      <div className="stat-copy">
        <span className="stat-label">{label}</span>
        <strong>{value}</strong>
        <span className="stat-note">{note}</span>
      </div>
    </article>
  );
}
export function SectionCard({
  title,
  description,
  action,
  children,
  className = "",
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`section-card ${className}`}>
      <header className="section-header">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        {action && <div>{action}</div>}
      </header>
      {children}
    </section>
  );
}
export function Initials({
  name,
  className = "",
}: {
  name: string;
  className?: string;
}) {
  const initials = name
    .split(" ")
    .filter(Boolean)
    .slice(-2)
    .map((part) => part.replace(/[^A-Za-z]/g, "")[0] || "")
    .join("")
    .toUpperCase();
  return <span className={`initials ${className}`}>{initials}</span>;
}
export function RecordTitle({
  name,
  detail,
}: {
  name: string;
  detail?: string;
}) {
  return (
    <div className="record-title">
      <Initials name={name} />
      <span>
        <strong>{name}</strong>
        {detail && <small>{detail}</small>}
      </span>
    </div>
  );
}
