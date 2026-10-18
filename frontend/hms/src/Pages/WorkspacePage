import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import {IconActivity,IconArrowUpRight,IconCalendarPlus,IconCheck,IconClock,IconDownload,IconEye,IconFileDescription,IconHeartbeat,IconPlus,IconStethoscope,IconUsers,IconX,} from "@tabler/icons-react";
import {Appointment,Doctor,Medicine,Operation,Patient,Report,RoomVisit,} from "../data/mockData";
import { useHospital } from "../context/HospitalContext";
import { apiClient, ApiError, ScheduleSlot } from "../api";
import {Badge,Button,DataTable,Initials,Modal,PageHeader,RecordTitle,SearchBox,SectionCard,Select,StatCard,Column,} from "../Components/UI";
import { Select as MedicineSelect } from "@mantine/core";

type Model =
  | Patient
  | Doctor
  | Appointment
  | Operation
  | Medicine
  | Report
  | RoomVisit;
type Field = {
  key: string;
  label: string;
  type?: string;
  options?: string[];
  required?: boolean;
};
const patientFields: Field[] = [
  { key: "name", label: "Full name", type: "text" },
  { key: "gender", label: "Gender", options: ["Female", "Male", "Other"] },
  { key: "dateOfBirth", label: "Date of birth", type: "date" },
  { key: "phone", label: "Mobile number", type: "tel" },
  { key: "email", label: "Email", type: "email", required: false },
  { key: "doctor", label: "Assigned doctor", type: "text", required: false },
  {
    key: "bloodGroup",
    label: "Blood group",
    options: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    required: false,
  },
  { key: "address", label: "Address", type: "text", required: false },
  {
    key: "emergencyContactName",
    label: "Emergency contact name",
    type: "text",
    required: false,
  },
  {
    key: "emergencyContactPhone",
    label: "Emergency contact number",
    type: "tel",
    required: false,
  },
];
const doctorFields: Field[] = [
  { key: "name", label: "Full name", type: "text" },
  { key: "department", label: "Department", type: "text" },
  { key: "specialization", label: "Specialisation", type: "text" },
  {
    key: "availability",
    label: "Availability",
    options: ["Available", "Absent", "On Leave"],
  },
  { key: "phone", label: "Mobile number", type: "tel" },
  { key: "email", label: "Account email", type: "email" },
  {
    key: "password",
    label: "Initial password (12+ characters)",
    type: "password",
  },
  { key: "experience", label: "Years of experience", type: "number" },
  { key: "degree", label: "Qualification", type: "text" },
];
const appointmentFields: Field[] = [
  { key: "patient", label: "Patient name", type: "text" },
  { key: "department", label: "Department", type: "text" },
  { key: "date", label: "Date", type: "date" },
  { key: "time", label: "Time slot", type: "time" },
  { key: "reason", label: "Reason for visit", type: "text" },
];
const operationFields: Field[] = [
  { key: "patient", label: "Patient name", type: "text" },
  { key: "doctor", label: "Doctor", type: "text" },
  { key: "operationDate", label: "Operation date", type: "date" },
  { key: "followUp", label: "Follow-up date", type: "date" },
  { key: "disease", label: "Procedure / condition", type: "text" },
  {
    key: "status",
    label: "Status",
    options: ["Scheduled", "Completed", "Cancelled"],
  },
  { key: "report", label: "Report note", type: "text" },
];
const medicineFields: Field[] = [
  { key: "name", label: "Medicine name", type: "text" },
  { key: "category", label: "Category", type: "text" },
  { key: "stock", label: "Stock quantity", type: "number" },
  { key: "price", label: "Price ($)", type: "number" },
  { key: "expiry", label: "Expiry date", type: "date" },
  { key: "company", label: "Manufacturer", type: "text" },
];

const WorkspacePage = () => {
  const location = useLocation();
  const {
    patients,
    doctors,
    appointments,
    operations,
    medicines,
    reports,
    visits,
    departments,
    departmentLookup,
    medications,
    createRecord,
    updateRecord,
    deleteRecord,
    notify,
    loadError,
    loading,
    refresh,
  } = useHospital();
  const path =
    location.pathname.split("/").filter(Boolean).slice(1).join("/") ||
    "dashboard";
  const role = location.pathname.split("/")[1] || "admin";
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All statuses");
  const [modal, setModal] = useState<{ kind: string; record?: Model } | null>(
    null,
  );
  const [dateFilter, setDateFilter] = useState("");
  const [details, setDetails] = useState<Model | null>(null);
  const [tab, setTab] = useState<"Upcoming" | "Past">("Upcoming");
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [reportModal, setReportModal] = useState(false);
  const [prescribeFor, setPrescribeFor] = useState<Appointment | null>(null);
  const visibleAppointments = appointments;
  const filteredAppointments = useMemo(
    () =>
      visibleAppointments.filter(
        (item) =>
          `${item.patient} ${item.doctor} ${item.disease}`
            .toLowerCase()
            .includes(query.toLowerCase()) &&
          (filter === "All statuses" || item.status === filter) &&
          (!dateFilter ||
            new Date(item.date).toISOString().slice(0, 10) === dateFilter),
      ),
    [visibleAppointments, query, filter, dateFilter],
  );
  const closeModal = () => setModal(null);
  const save = async (
    event: FormEvent<HTMLFormElement>,
    fallback?: { kind: string; record?: Model },
  ) => {
    event.preventDefault();
    const activeModal = modal || fallback;
    if (!activeModal) return;
    const form = new FormData(event.currentTarget);
    const data = Object.fromEntries(form.entries()) as Record<string, string>;
    if (activeModal.kind === "appointment" && role === "patient") {
      data.patient = patients[0].name;
      data.gender = patients[0].gender;
      data.disease = data.reason;
    }
    const fields = fieldsFor(activeModal.kind).filter(
      (field) =>
        !(
          activeModal.kind === "doctor" &&
          activeModal.record &&
          ["email", "password"].includes(field.key)
        ) &&
        !(
          activeModal.kind === "patient" &&
          role === "patient" &&
          ["email", "doctor", "bloodGroup"].includes(field.key)
        ),
    );
    if (
      fields.some(
        (field) => field.required !== false && !data[field.key]?.trim(),
      )
    ) {
      notify("Please complete the required fields.");
      return;
    }
    if (
      activeModal.kind === "appointment" &&
      data.date < new Date().toISOString().slice(0, 10)
    ) {
      notify("Choose a date in the future.");
      return;
    }
    const current = activeModal.record as Record<string, unknown> | undefined;
    const numericId = (value: unknown) =>
      Number(String(value || "").match(/\d+/)?.[0] || 0);
    const doctorId = (name: string) =>
      numericId(doctors.find((item) => item.name === name)?.id);
    const patientId = (name: string) =>
      numericId(patients.find((item) => item.name === name)?.id);
    const fullName = (text: string) => {
      const [first_name, ...rest] = text
        .trim()
        .replace(/^Dr\.\s*/i, "")
        .split(/\s+/);
      return { first_name, last_name: rest.join(" ") };
    };
    let resource = "";
    let payload: Record<string, unknown> = {};
    if (activeModal.kind === "patient") {
      resource = "patients";
      const name = fullName(data.name);
      payload = {
        ...name,
        gender: data.gender,
        date_of_birth: data.dateOfBirth || null,
        phone: data.phone || null,
        address: data.address || null,
        emergency_contact_name: data.emergencyContactName || null,
        emergency_contact_phone: data.emergencyContactPhone || null,
      };
      if (role !== "patient") {
        const doc = data.doctor ? doctorId(data.doctor) : 0;
        payload = {
          ...payload,
          email: data.email || null,
          primary_doctor_id: doc || null,
          blood_group: data.bloodGroup || null,
        };
      }
    }
    if (activeModal.kind === "doctor") {
      resource = "doctors";
      const name = fullName(data.name);
      const department_id = departmentLookup.find(
        (item) => item.name === data.department,
      )?.id;
      if (!department_id) {
        notify("Select a valid department.");
        return;
      }
      payload = {
        ...name,
        department_id,
        specialization: data.specialization,
        availability: data.availability,
        phone: data.phone || null,
        years_experience: Number(data.experience) || null,
        degree: data.degree || null,
      };
    }
    if (activeModal.kind === "appointment") {
      resource = "appointments";
      const department_id = departmentLookup.find(
        (item) => item.name === data.department,
      )?.id;
      if (!department_id) {
        notify("Select a department.");
        return;
      }
      payload = {
        department_id,
        scheduled_at: `${data.date}T${data.time || "09:00"}:00`,
        reason: data.reason || data.disease,
        notes: null,
      };
      if (role !== "patient") payload.patient_id = patientId(data.patient);
    }
    if (activeModal.kind === "operation") {
      resource = "operations";
      payload = {
        patient_id: patientId(data.patient),
        lead_doctor_id: doctorId(data.doctor),
        operation_at: data.operationDate
          ? `${data.operationDate}T00:00:00`
          : null,
        follow_up_at: data.followUp ? `${data.followUp}T00:00:00` : null,
        procedure_name: data.disease,
        status: data.status.toLowerCase().replaceAll(" ", "_"),
        report_summary: data.report || null,
      };
    }
    if (activeModal.kind === "medicine") {
      resource = "medicines";
      payload = {
        name: data.name,
        category: data.category || null,
        stock_quantity: Number(data.stock) || 0,
        unit_price: Number(data.price) || 0,
        expiry_date: data.expiry || null,
        manufacturer: data.company || null,
      };
    }
    try {
      if (current) await updateRecord(resource, String(current.id), payload);
      else if (activeModal.kind === "doctor") {
        await apiClient.createDoctorAccount({
          ...payload,
          email: data.email,
          password: data.password,
        });
        await refresh();
      } else await createRecord(resource, payload);
      closeModal();
      notify(
        `${activeModal.record ? "Changes saved" : "Record added"} successfully.`,
      );
    } catch (error) {
      notify(
        error instanceof Error ? error.message : "Could not save this record.",
      );
    }
  };
  const changeAppointmentStatus = async (
    appointment: Appointment,
    status: string,
  ) => {
    try {
      await updateRecord("appointments", appointment.id, { status });
      notify("Appointment status updated.");
    } catch (error) {
      notify(
        error instanceof Error
          ? error.message
          : "Could not update appointment status.",
      );
    }
  };
  const cancelAppointment = async (appointment: Appointment) => {
    if (!window.confirm("Cancel this upcoming appointment?")) return;
    try {
      await updateRecord("appointments", appointment.id, {
        status: "cancelled",
      });
      notify("Appointment cancelled.");
    } catch (error) {
      notify(
        error instanceof Error
          ? error.message
          : "Could not cancel appointment.",
      );
    }
  };
  const changeOperationStatus = async (
    operation: Operation,
    status: string,
  ) => {
    try {
      await updateRecord("operations", operation.id, { status });
      notify("Operation status updated.");
    } catch (error) {
      notify(
        error instanceof Error
          ? error.message
          : "Could not update operation status.",
      );
    }
  };
  const overlays = (
    <>
      {modal?.kind === "appointment" && !modal.record ? (
        <AppointmentBookModal role={role} onClose={closeModal} />
      ) : modal ? (
        <RecordModal
          kind={modal.kind}
          record={modal.record}
          doctors={doctors}
          patients={patients}
          departments={departments}
          patientBooking={role === "patient"}
          onClose={closeModal}
          onSubmit={save}
        />
      ) : null}{" "}
      {showProfileEdit && patients[0] && (
        <RecordModal
          kind="patient"
          record={patients[0]}
          doctors={doctors}
          patients={patients}
          departments={departments}
          patientProfileEdit
          onClose={() => setShowProfileEdit(false)}
          onSubmit={async (event) => {
            await save(event, { kind: "patient", record: patients[0] });
            setShowProfileEdit(false);
          }}
        />
      )}{" "}
      {reportModal && (
        <ReportUploadModal role={role} onClose={() => setReportModal(false)} />
      )}{" "}
      {details && (
        <DetailsModal record={details} onClose={() => setDetails(null)} />
      )}{" "}
      {prescribeFor && (
        <PrescribeModal
          appointment={prescribeFor}
          onClose={() => setPrescribeFor(null)}
        />
      )}
    </>
  );
  const withOverlays = (content: React.ReactNode) => (
    <>
      {content}
      {overlays}
    </>
  );
  const remove = (kind: string, record: Model) => {
    if (!window.confirm(`Delete this ${kind}? This cannot be undone.`)) return;
    const id = (record as { id: string }).id;
    const resource = kind === "room visit" ? "room-visits" : `${kind}s`;
    void deleteRecord(resource, id)
      .then(() => notify("Record removed."))
      .catch((error) =>
        notify(
          error instanceof Error ? error.message : "Could not remove record.",
        ),
      );
  };
  const openBook = () => setModal({ kind: "appointment" });

  if (loading)
    return <div className="app-loading">Loading hospital records…</div>;
  if (loadError)
    return (
      <>
        <PageHeader
          title="Unable to load records"
          subtitle={loadError}
          action={<Button onClick={() => void refresh()}>Retry</Button>}
        />
      </>
    );
  if (path === "dashboard") {
    if (role === "patient")
      return withOverlays(
        <PatientDashboard
          appointments={visibleAppointments}
          reports={reports}
          onBook={openBook}
          onEdit={() => setShowProfileEdit(true)}
          onDetails={setDetails}
          onCancel={cancelAppointment}
        />,
      );
    if (role === "doctor")
      return withOverlays(
            <DoctorDashboard
          appointments={visibleAppointments}
          onDetails={setDetails}
          onStatusChange={changeAppointmentStatus}
          onOperationStatusChange={changeOperationStatus}
          onPrescribe={setPrescribeFor}
        />,
      );
    return withOverlays(
      <AdminDashboard
        appointments={filteredAppointments}
        doctors={doctors}
        operations={operations}
        query={query}
        setQuery={setQuery}
        filter={filter}
        setFilter={setFilter}
        onDetails={setDetails}
        onAdd={() => setModal({ kind: "operation" })}
        onBook={openBook}
      />,
    );
  }
  if (path === "appointments") {
    if (role === "patient")
      return withOverlays(
        <PatientAppointments
          appointments={visibleAppointments}
          tab={tab}
          setTab={setTab}
          onBook={openBook}
          onDetails={setDetails}
          onCancel={cancelAppointment}
        />,
      );
    const title = role === "doctor" ? "My appointments" : "Appointments";
    return withOverlays(
      <>
        <PageHeader
          title={title}
          subtitle="Review and manage scheduled patient visits."
          action={
            role === "doctor" ? undefined : (
              <Button onClick={openBook}>
                <IconPlus size={17} /> New appointment
              </Button>
            )
          }
        />
        <SectionCard
          title="All appointments"
          description={`${filteredAppointments.length} appointments in your view`}
        >
          <TableTools
            query={query}
            setQuery={setQuery}
            filter={filter}
            setFilter={setFilter}
            statuses={["Scheduled", "Due", "Completed", "Cancelled"]}
            dateFilter={dateFilter}
            setDateFilter={setDateFilter}
          />
          <AppointmentsTable
            rows={filteredAppointments}
            onDetails={setDetails}
            onRemove={
              role === "admin" ? (row) => remove("appointment", row) : undefined
            }
            onStatusChange={
              role === "doctor" ? changeAppointmentStatus : undefined
            }
            onPrescribe={
              role === "doctor" ? (row) => setPrescribeFor(row) : undefined
            }
          />
        </SectionCard>
      </>,
    );
  }
  if (path === "patients" || path === "profile") {
    if (role === "patient")
      return withOverlays(
        <PatientProfile onEdit={() => setShowProfileEdit(true)} />,
      );
    const rows = patients;
    const found = rows.filter((row) =>
      `${row.name} ${row.doctor} ${row.concern}`
        .toLowerCase()
        .includes(query.toLowerCase()),
    );
    return withOverlays(
      <>
        <PageHeader
          title={role === "doctor" ? "My patients" : "Patients"}
          subtitle="Patient records, care teams and upcoming visits."
          action={
            role === "admin" ? (
              <Button onClick={() => setModal({ kind: "patient" })}>
                <IconPlus size={17} /> Add patient
              </Button>
            ) : undefined
          }
        />
        <SectionCard
          title="Patient directory"
          description={`${found.length} patient records`}
        >
          <SearchBox
            value={query}
            onChange={setQuery}
            placeholder="Search patients or conditions"
          />
          <PatientsTable
            rows={found}
            onDetails={setDetails}
            onEdit={
              role === "admin"
                ? (row) => setModal({ kind: "patient", record: row })
                : undefined
            }
            onRemove={
              role === "admin" ? (row) => remove("patient", row) : undefined
            }
          />
        </SectionCard>
      </>,
    );
  }
  if (path === "doctors") {
    if (role === "patient")
      return withOverlays(<PatientDoctor doctors={doctors} />);
    const found = doctors.filter(
      (row) =>
        `${row.name} ${row.department} ${row.specialization}`
          .toLowerCase()
          .includes(query.toLowerCase()) &&
        (filter === "All statuses" || row.availability === filter),
    );
    return withOverlays(
      <>
        <PageHeader
          title="Doctors"
          subtitle="Care teams and availability across the hospital."
          action={
            role === "admin" ? (
              <Button onClick={() => setModal({ kind: "doctor" })}>
                <IconPlus size={17} /> Add doctor
              </Button>
            ) : undefined
          }
        />
        <SectionCard
          title="Doctor directory"
          description={`${found.length} doctors`}
        >
          <TableTools
            query={query}
            setQuery={setQuery}
            filter={filter}
            setFilter={setFilter}
            statuses={["Available", "Absent", "On Leave"]}
          />
          <DataTable
            columns={doctorColumns(
              (row) => setDetails(row),
              role === "admin"
                ? (row) => setModal({ kind: "doctor", record: row })
                : undefined,
              role === "admin" ? (row) => remove("doctor", row) : undefined,
            )}
            rows={found}
          />
        </SectionCard>
      </>,
    );
  }
  if (path === "operations") {
    const found = operations.filter(
      (row) =>
        `${row.patient} ${row.doctor} ${row.disease}`
          .toLowerCase()
          .includes(query.toLowerCase()) &&
        (filter === "All statuses" || row.status === filter),
    );
    return withOverlays(
      <>
        <PageHeader
          title={role === "doctor" ? "Surgeries & operations" : "Operations"}
          subtitle="Track scheduled procedures, post-operative reports and follow-up care."
          action={
            role === "admin" ? (
              <Button onClick={() => setModal({ kind: "operation" })}>
                <IconPlus size={17} /> Add operation
              </Button>
            ) : undefined
          }
        />
        <SectionCard
          title="Operation schedule"
          description={`${found.length} procedures`}
        >
          <TableTools
            query={query}
            setQuery={setQuery}
            filter={filter}
            setFilter={setFilter}
            statuses={["Scheduled", "In Progress", "Completed", "Cancelled"]}
          />
          <OperationsTable
            rows={found}
            onDetails={setDetails}
            onRemove={
              role === "admin" ? (row) => remove("operation", row) : undefined
            }
            onStatusChange={
              role === "doctor" ? changeOperationStatus : undefined
            }
          />
        </SectionCard>
      </>,
    );
  }
  if (path === "room-visits")
    return withOverlays(
      <>
        <PageHeader
          title="Room visits"
          subtitle="Upcoming bedside visits and completed rounds."
        />
        <SectionCard title="Visit schedule">
          <DataTable
            columns={visitColumns((row) => setDetails(row))}
            rows={visits}
          />
        </SectionCard>
      </>,
    );
  if (path === "medicines" || path === "medications") {
    if (role === "patient")
      return withOverlays(<MedicationPage medications={medications} />);
    const found = medicines.filter((row) =>
      `${row.name} ${row.company} ${row.category}`
        .toLowerCase()
        .includes(query.toLowerCase()),
    );
    return withOverlays(
      <>
        <PageHeader
          title="Medicines"
          subtitle="Inventory stays separate from prescriptions written by doctors."
          action={
            role === "admin" ? (
              <Button onClick={() => setModal({ kind: "medicine" })}>
                <IconPlus size={17} /> Add medicine
              </Button>
            ) : undefined
          }
        />
        <SectionCard
          title="Medicine inventory"
          description={`${found.length} medicines tracked`}
        >
          <SearchBox
            value={query}
            onChange={setQuery}
            placeholder="Search medicine or company"
          />
          <MedicinesTable
            rows={found}
            onEdit={
              role === "admin"
                ? (row) => setModal({ kind: "medicine", record: row })
                : undefined
            }
            onRemove={
              role === "admin" ? (row) => remove("medicine", row) : undefined
            }
          />
        </SectionCard>
        {role === "admin" && <PrescriptionsReceived />}
      </>,
    );
  }
  if (path === "reports") {
    const rows = reports;
    return withOverlays(
      <>
        <PageHeader
          title={role === "patient" ? "Reports & documents" : "Reports"}
          subtitle="Securely stored clinical documents and visit summaries."
          action={
            <Button variant="secondary" onClick={() => setReportModal(true)}>
              <IconPlus size={17} /> Upload document
            </Button>
          }
        />
        <SectionCard
          title="Documents"
          description={`${rows.length} files available`}
        >
          <SearchBox
            value={query}
            onChange={setQuery}
            placeholder="Search documents"
          />
          <DataTable
            columns={reportColumns(
              (row) => setDetails(row),
              (row) =>
                void apiClient
                  .downloadReport(row.id, row.name)
                  .catch((error) =>
                    notify(
                      error instanceof Error
                        ? error.message
                        : "Could not download report.",
                    ),
                  ),
            )}
            rows={rows.filter((row) =>
              `${row.name} ${row.patient} ${row.type}`
                .toLowerCase()
                .includes(query.toLowerCase()),
            )}
            empty="Documents will appear here when uploaded to a patient record."
          />
        </SectionCard>
      </>,
    );
  }
  if (path === "departments")
    return withOverlays(<DepartmentPage departments={departments} />);
  return withOverlays(
    <>
      <PageHeader
        title="Dashboard"
        subtitle="A clear view of today's care activity."
      />
      <div className="section-card">
        <p>Choose a section from the navigation to continue.</p>
      </div>
    </>,
  );
};
export default WorkspacePage;

function TableTools({
  query,
  setQuery,
  filter,
  setFilter,
  statuses,
  dateFilter,
  setDateFilter,
}: {
  query: string;
  setQuery: (value: string) => void;
  filter: string;
  setFilter: (value: string) => void;
  statuses: string[];
  dateFilter?: string;
  setDateFilter?: (value: string) => void;
}) {
  return (
    <div className="table-tools">
      <SearchBox
        value={query}
        onChange={setQuery}
        placeholder="Search by patient, doctor or condition"
      />
      <div className="table-filter-group">
        <Select value={filter} onChange={setFilter} label="Filter by status">
          <option>All statuses</option>
          {statuses.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </Select>
        {setDateFilter && (
          <label className="date-filter">
            <span>Date</span>
            <input
              type="date"
              value={dateFilter}
              onChange={(event) => setDateFilter(event.target.value)}
              aria-label="Filter by date"
            />
          </label>
        )}
      </div>
    </div>
  );
}
function AppointmentsTable({
  rows,
  onDetails,
  onRemove,
  onStatusChange,
  onCancel,
  onPrescribe,
}: {
  rows: Appointment[];
  onDetails: (row: Appointment) => void;
  onRemove?: (row: Appointment) => void;
  onStatusChange?: (row: Appointment, status: string) => void;
  onCancel?: (row: Appointment) => void;
  onPrescribe?: (row: Appointment) => void;
}) {
  const columns: Column<Appointment>[] = [
    {
      key: "patient",
      label: "Patient",
      render: (r) => <RecordTitle name={r.patient} />,
    },
    { key: "doctor", label: "Assigned doctor" },
    { key: "department", label: "Department" },
    {
      key: "date",
      label: "Date & time",
      render: (r) => (
        <span className="date-cell">
          <strong>{r.date}</strong>
          <small>{r.time}</small>
        </span>
      ),
    },
    { key: "disease", label: "Health concern" },
    {
      key: "status",
      label: "Status",
      render: (r) => <Badge>{r.status}</Badge>,
    },
    {
      key: "actions",
      label: "",
      className: "actions-cell",
      render: (r) => (
        <div className="row-actions">
          {onStatusChange && r.status !== "Cancelled" && (
            <select
              aria-label={`Change status for ${r.patient}`}
              value={r.rawStatus || "scheduled"}
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => onStatusChange(r, e.target.value)}
            >
              <option value="scheduled">Scheduled</option>
              <option value="requested">Due</option>
              <option value="completed">Completed</option>
            </select>
          )}
          {onPrescribe && r.status !== "Cancelled" && (
            <button
              className="text-action"
              onClick={(e) => {
                e.stopPropagation();
                onPrescribe(r);
              }}
            >
              Prescribe
            </button>
          )}
          {onCancel && ["Due", "Scheduled"].includes(r.status) && (
            <button
              className="text-action"
              onClick={(e) => {
                e.stopPropagation();
                onCancel(r);
              }}
            >
              Cancel
            </button>
          )}
          <button
            className="text-action"
            onClick={(e) => {
              e.stopPropagation();
              onDetails(r);
            }}
          >
            Details
          </button>
          {onRemove && (
            <button
              className="icon-button danger-icon"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(r);
              }}
              aria-label="Delete appointment"
            >
              <IconX size={16} />
            </button>
          )}
        </div>
      ),
    },
  ];
  return (
    <DataTable
      columns={columns}
      rows={rows}
      empty="Try changing your search or status filter."
    />
  );
}
function PatientsTable({
  rows,
  onDetails,
  onEdit,
  onRemove,
}: {
  rows: Patient[];
  onDetails: (row: Patient) => void;
  onEdit?: (row: Patient) => void;
  onRemove?: (row: Patient) => void;
}) {
  const columns: Column<Patient>[] = [
    {
      key: "name",
      label: "Patient",
      render: (r) => <RecordTitle name={r.name} detail={`${r.age} years`} />,
    },
    {
      key: "gender",
      label: "Gender",
      render: (r) => <Badge tone="purple">{r.gender}</Badge>,
    },
    { key: "doctor", label: "Assigned doctor" },
    { key: "concern", label: "Health concern" },
    { key: "nextAppointment", label: "Next visit" },
    {
      key: "actions",
      label: "",
      className: "actions-cell",
      render: (r) => (
        <div className="row-actions">
          <button
            className="text-action"
            onClick={(e) => {
              e.stopPropagation();
              onDetails(r);
            }}
          >
            View
          </button>
          {onEdit && (
            <button
              className="text-action"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(r);
              }}
            >
              Edit
            </button>
          )}
          {onRemove && (
            <button
              className="icon-button danger-icon"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(r);
              }}
              aria-label="Delete patient"
            >
              <IconX size={16} />
            </button>
          )}
        </div>
      ),
    },
  ];
  return (
    <DataTable
      columns={columns}
      rows={rows}
      empty="No patients match your search."
    />
  );
}
function doctorColumns(
  onDetails: (row: Doctor) => void,
  onEdit?: (row: Doctor) => void,
  onRemove?: (row: Doctor) => void,
): Column<Doctor>[] {
  return [
    {
      key: "name",
      label: "Doctor",
      render: (r) => <RecordTitle name={r.name} />,
    },
    { key: "department", label: "Department" },
    { key: "specialization", label: "Specialisation" },
    {
      key: "availability",
      label: "Availability",
      render: (r) => <Badge>{r.availability}</Badge>,
    },
    {
      key: "experience",
      label: "Experience",
      render: (r) => `${r.experience} yrs`,
    },
    {
      key: "actions",
      label: "",
      className: "actions-cell",
      render: (r) => (
        <div className="row-actions">
          <button
            className="text-action"
            onClick={(e) => {
              e.stopPropagation();
              onDetails(r);
            }}
          >
            View
          </button>
          {onEdit && (
            <button
              className="text-action"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(r);
              }}
            >
              Edit
            </button>
          )}
          {onRemove && (
            <button
              className="icon-button danger-icon"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(r);
              }}
              aria-label="Delete doctor"
            >
              <IconX size={16} />
            </button>
          )}
        </div>
      ),
    },
  ];
}
function OperationsTable({
  rows,
  onDetails,
  onRemove,
  onStatusChange,
}: {
  rows: Operation[];
  onDetails: (row: Operation) => void;
  onRemove?: (row: Operation) => void;
  onStatusChange?: (row: Operation, status: string) => void;
}) {
  const columns: Column<Operation>[] = [
    {
      key: "patient",
      label: "Patient",
      render: (r) => <RecordTitle name={r.patient} />,
    },
    { key: "doctor", label: "Doctor" },
    { key: "operationDate", label: "Operation date" },
    { key: "followUp", label: "Follow-up" },
    {
      key: "report",
      label: "Report",
      render: (r) => (
        <button
          className="text-action"
          onClick={(e) => {
            e.stopPropagation();
            onDetails(r);
          }}
        >
          View report
        </button>
      ),
    },
    { key: "disease", label: "Procedure" },
    {
      key: "status",
      label: "Status",
      render: (r) => <Badge>{r.status}</Badge>,
    },
    {
      key: "actions",
      label: "",
      className: "actions-cell",
      render: (r) => (
        <div className="row-actions">
          {onStatusChange && (
            <select
              aria-label={`Change status for ${r.disease}`}
              value={r.rawStatus || "scheduled"}
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => onStatusChange(r, e.target.value)}
            >
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          )}
          <button
            className="text-action"
            onClick={(e) => {
              e.stopPropagation();
              onDetails(r);
            }}
          >
            Details
          </button>
          {onRemove && (
            <button
              className="icon-button danger-icon"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(r);
              }}
              aria-label="Delete operation"
            >
              <IconX size={16} />
            </button>
          )}
        </div>
      ),
    },
  ];
  return (
    <DataTable
      columns={columns}
      rows={rows}
      empty="No operations match your search."
    />
  );
}
function MedicinesTable({
  rows,
  onEdit,
  onRemove,
}: {
  rows: Medicine[];
  onEdit?: (row: Medicine) => void;
  onRemove?: (row: Medicine) => void;
}) {
  const columns: Column<Medicine>[] = [
    {
      key: "name",
      label: "Medicine",
      render: (r) => <RecordTitle name={r.name} />,
    },
    { key: "category", label: "Category" },
    { key: "company", label: "Manufacturer" },
    { key: "price", label: "Price", render: (r) => `$${r.price.toFixed(2)}` },
    {
      key: "stock",
      label: "Stock",
      render: (r) => (
        <span className="stock-value">
          {r.stock} {r.stock < 35 && <Badge>Low stock</Badge>}
        </span>
      ),
    },
    { key: "expiry", label: "Expiry date" },
    {
      key: "actions",
      label: "",
      className: "actions-cell",
      render: (r) => (
        <div className="row-actions">
          {onEdit && (
            <button className="text-action" onClick={() => onEdit(r)}>
              Edit
            </button>
          )}
          {onRemove && (
            <button
              className="icon-button danger-icon"
              onClick={() => onRemove(r)}
              aria-label="Delete medicine"
            >
              <IconX size={16} />
            </button>
          )}
        </div>
      ),
    },
  ];
  return (
    <DataTable
      columns={columns}
      rows={rows}
      empty="No medicine records match your search."
    />
  );
}
function visitColumns(
  onDetails: (row: RoomVisit) => void,
): Column<RoomVisit>[] {
  return [
    {
      key: "patient",
      label: "Patient",
      render: (r) => <RecordTitle name={r.patient} />,
    },
    { key: "room", label: "Room" },
    { key: "date", label: "Visit date" },
    { key: "time", label: "Time" },
    {
      key: "status",
      label: "Status",
      render: (r) => <Badge>{r.status}</Badge>,
    },
    {
      key: "actions",
      label: "",
      render: (r) => (
        <button className="text-action" onClick={() => onDetails(r)}>
          Details
        </button>
      ),
    },
  ];
}
function reportColumns(
  onDetails: (row: Report) => void,
  onDownload: (row: Report) => void,
): Column<Report>[] {
  return [
    {
      key: "name",
      label: "Document",
      render: (r) => (
        <div className="document-title">
          <span>
            <IconFileDescription size={19} />
          </span>
          <button className="text-action" onClick={() => onDetails(r)}>
            {r.name}
          </button>
        </div>
      ),
    },
    {
      key: "type",
      label: "Type",
      render: (r) => <Badge tone="blue">{r.type}</Badge>,
    },
    { key: "patient", label: "Patient" },
    { key: "date", label: "Date" },
    { key: "uploadedBy", label: "Uploaded by" },
    {
      key: "actions",
      label: "",
      render: (r) => (
        <button
          className="icon-button"
          aria-label={`Download ${r.name}`}
          title="Download report"
          onClick={() => onDownload(r)}
        >
          <IconDownload size={18} />
        </button>
      ),
    },
  ];
}

function AdminDashboard({
  appointments,
  doctors,
  operations,
  query,
  setQuery,
  filter,
  setFilter,
  onDetails,
  onAdd,
  onBook,
}: {
  appointments: Appointment[];
  doctors: Doctor[];
  operations: Operation[];
  query: string;
  setQuery: (value: string) => void;
  filter: string;
  setFilter: (value: string) => void;
  onDetails: (record: Model) => void;
  onAdd: () => void;
  onBook?: () => void;
}) {
  const { patients, user, departments } = useHospital();
  return (
    <>
      <PageHeader
        title={`Welcome, ${user?.display_name || "Administrator"}`}
        subtitle="Hospital activity from your connected records."
        action={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {onBook && (
              <Button onClick={onBook}>
                <IconPlus size={17} /> New appointment
              </Button>
            )}
            <Button variant="secondary" onClick={() => window.print()}>
              Export overview
            </Button>
          </div>
        }
      />
      <div className="stats-grid">
        <StatCard
          label="Appointments"
          value={appointments.length}
          note="Records in your current view"
          icon={<IconCalendarPlus size={20} />}
          tone="blue"
        />
        <StatCard
          label="Operations"
          value={operations.length}
          note="Recorded procedures"
          icon={<IconActivity size={20} />}
          tone="teal"
        />
        <StatCard
          label="Patients"
          value={patients.length}
          note="Registered patient records"
          icon={<IconUsers size={20} />}
          tone="green"
        />
        <StatCard
          label="Doctors"
          value={doctors.length}
          note="Registered doctor profiles"
          icon={<IconStethoscope size={20} />}
          tone="purple"
        />
      </div>
      <div className="dashboard-grid">
        <SectionCard
          title="Appointments"
          description="The next visits on the schedule"
          action={
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
              {onBook && (
                <Button onClick={onBook}>
                  <IconPlus size={15} /> Book appointment
                </Button>
              )}
              <a className="section-link" href="/admin/appointments">
                View all <IconArrowUpRight size={15} />
              </a>
            </div>
          }
          className="appointments-panel"
        >
          <div className="table-tools">
            <SearchBox
              value={query}
              onChange={setQuery}
              placeholder="Search patient or doctor"
            />
            <Select
              value={filter}
              onChange={setFilter}
              label="Appointment status"
            >
              <option>All statuses</option>
              <option>Scheduled</option>
              <option>Due</option>
              <option>Completed</option>
              <option>Cancelled</option>
            </Select>
          </div>
          <AppointmentsTable
            rows={appointments.slice(0, 5)}
            onDetails={onDetails}
          />
        </SectionCard>
        <SectionCard
          title="Doctor status"
          description="Availability across care teams"
          action={
            <a className="section-link" href="/admin/doctors">
              All doctors <IconArrowUpRight size={15} />
            </a>
          }
        >
          <div className="doctor-status-list">
            {doctors.slice(0, 5).map((doctor) => (
              <div className="doctor-status-row" key={doctor.id}>
                <RecordTitle name={doctor.name} detail={doctor.department} />
                <Badge>{doctor.availability}</Badge>
              </div>
            ))}
          </div>
          <div className="status-footnote">
            <span className="availability-dot" /> Availability is updated by
            each care team
          </div>
        </SectionCard>
      </div>
      <SectionCard
        title="Operations"
        description="Scheduled procedures and post-operative care"
        action={
          <Button variant="secondary" onClick={onAdd}>
            <IconPlus size={16} /> Add operation
          </Button>
        }
      >
        <OperationsTable rows={operations} onDetails={onDetails} />
      </SectionCard>
      <div className="dashboard-bottom">
        <SectionCard
          title="Department overview"
          description="Departments currently in the database"
        >
          <div className="department-bars">
            {departments.map((label) => {
              const count = doctors.filter(
                (doctor) => doctor.department === label,
              ).length;
              return (
                <div className="department-bar" key={label}>
                  <div>
                    <span>{label}</span>
                    <strong>{count} clinicians</strong>
                  </div>
                  <span className="bar-track">
                    <i
                      style={{
                        width: `${doctors.length ? Math.max(5, (count / doctors.length) * 100) : 0}%`,
                      }}
                    />
                  </span>
                </div>
              );
            })}
          </div>
        </SectionCard>
        <SectionCard
          title="Patient snapshot"
          description="Registered patient records"
        >
          <div className="patient-snapshot">
            <strong>{patients.length}</strong>
            <span>patient records</span>
            <a href="/admin/patients" className="section-link">
              Open directory <IconArrowUpRight size={15} />
            </a>
          </div>
          <div className="snapshot-note">
            <IconHeartbeat size={19} /> Counts reflect the hospital database.
          </div>
        </SectionCard>
      </div>
    </>
  );
}
function DoctorDashboard({
  appointments,
  onDetails,
  onStatusChange,
  onOperationStatusChange,
  onPrescribe,
}: {
  appointments: Appointment[];
  onDetails: (record: Model) => void;
  onStatusChange: (row: Appointment, status: string) => void;
  onOperationStatusChange: (row: Operation, status: string) => void;
  onPrescribe: (row: Appointment) => void;
}) {
  const { patients, operations, visits, doctors, user } = useHospital();
  const rows = appointments.filter((item) => item.status !== "Cancelled");
  const myDoctor =
    doctors.find(
      (doctor) =>
        (user?.user_id && doctor.userId === user.user_id) ||
        doctor.name.replace(/^Dr\.\s*/i, "").toLowerCase() ===
          (user?.display_name || "").replace(/^Dr\.\s*/i, "").toLowerCase(),
    ) || doctors[0];
  const displayName = user?.display_name || "Doctor";
  return (
    <>
      <PageHeader
        title={`Welcome, ${displayName}`}
        subtitle="Your appointments and patient records."
      />
      <div className="doctor-intro">
        <div className="doctor-avatar-large">
          <Initials name={displayName} />
        </div>
        <div className="doctor-intro-copy">
          <p className="eyebrow">{myDoctor?.department || "CARE TEAM"}</p>
          <h2>{displayName}</h2>
          <p>
            {myDoctor?.specialization || "Doctor"}
            {myDoctor?.experience
              ? ` · ${myDoctor.experience} years of experience`
              : ""}
          </p>
        </div>
        <div className="doctor-intro-status">
          <Badge>{myDoctor?.availability || "Profile not linked"}</Badge>
          <small>Availability from your profile</small>
        </div>
      </div>
      <div className="stats-grid stats-grid-four">
        <StatCard
          label="Appointments"
          value={rows.length}
          note="In your schedule"
          icon={<IconCalendarPlus size={20} />}
          tone="blue"
        />
        <StatCard
          label="Operations"
          value={operations.length}
          note="Under your care"
          icon={<IconActivity size={20} />}
          tone="teal"
        />
        <StatCard
          label="Room visits"
          value={visits.length}
          note="Scheduled and completed"
          icon={<IconBuildingHospitalFallback />}
          tone="green"
        />
        <StatCard
          label="My patients"
          value={patients.length}
          note="Assigned patient profiles"
          icon={<IconUsers size={20} />}
          tone="purple"
        />
      </div>
      <div className="dashboard-grid">
        <SectionCard
          title="Appointments"
          description="Update the status of each visit"
          action={
            <a className="section-link" href="/doctor/appointments">
              View all <IconArrowUpRight size={15} />
            </a>
          }
        >
          <AppointmentsTable
            rows={rows.slice(0, 4)}
            onDetails={onDetails}
            onStatusChange={onStatusChange}
            onPrescribe={onPrescribe}
          />
        </SectionCard>
        <SectionCard
          title="My patients"
          description="Patients under your care"
          action={
            <a className="section-link" href="/doctor/patients">
              View patients <IconArrowUpRight size={15} />
            </a>
          }
        >
          <PatientsTable rows={patients.slice(0, 4)} onDetails={onDetails} />
        </SectionCard>
      </div>
      <SectionCard
        title="Operations & procedures"
        description="Update the status of procedures under your care"
      >
        <OperationsTable
          rows={operations.slice(0, 5)}
          onDetails={onDetails}
          onStatusChange={onOperationStatusChange}
        />
      </SectionCard>
    </>
  );
}
function IconBuildingHospitalFallback() {
  return <IconActivity size={20} />;
}
function PatientDashboard({
  appointments,
  reports,
  onBook,
  onEdit,
  onDetails,
  onCancel,
}: {
  appointments: Appointment[];
  reports: Report[];
  onBook: () => void;
  onEdit: () => void;
  onDetails: (record: Model) => void;
  onCancel: (row: Appointment) => void;
}) {
  const { patients } = useHospital();
  const patient = patients[0];
  if (!patient)
    return (
      <>
        <PageHeader
          title="Patient profile not linked"
          subtitle="Contact the hospital team to link your account to a patient record."
        />
      </>
    );
  const upcoming = appointments
    .filter((item) => ["Due", "Scheduled"].includes(item.status))
    .slice(0, 2);
  return (
    <>
      <PageHeader
        title={`Welcome back, ${patient.name}`}
        subtitle="Here’s your care plan at a glance."
        action={
          <Button onClick={onBook}>
            <IconCalendarPlus size={17} /> Book appointment
          </Button>
        }
      />
      <div className="patient-overview">
        <div className="patient-overview-main">
          <div className="patient-overview-avatar">
            <Initials name={patient.name} />
          </div>
          <div>
            <span className="eyebrow">YOUR HEALTH PROFILE</span>
            <h2>{patient.name}</h2>
            <p>
              {patient.age} years <span>·</span> {patient.gender} <span>·</span>{" "}
              Blood group {patient.bloodGroup}
            </p>
          </div>
          <Button variant="secondary" onClick={onEdit}>
            Edit profile
          </Button>
        </div>
        <div className="patient-overview-meta">
          <div>
            <small>Assigned doctor</small>
            <strong>{patient.doctor}</strong>
            <span>Cardiology</span>
          </div>
          <div>
            <small>Next appointment</small>
            <strong>{upcoming[0]?.date || "No upcoming visit"}</strong>
            <span>
              {upcoming[0]?.time || "Book a visit when you are ready"}
            </span>
          </div>
          <div>
            <small>Health concern</small>
            <strong>{patient.concern}</strong>
            <span>Last visit {patient.lastVisit}</span>
          </div>
        </div>
      </div>
      <div className="dashboard-grid patient-grid">
        <SectionCard
          title="Upcoming appointments"
          description="Your next visits"
          action={
            <a className="section-link" href="/patient/appointments">
              All appointments <IconArrowUpRight size={15} />
            </a>
          }
        >
          <div className="patient-appointment-list">
            {upcoming.length ? (
              upcoming.map((row) => (
                <article className="patient-appointment" key={row.id}>
                  <span className="calendar-tile">
                    <strong>{row.date.slice(4, 6)}</strong>
                    <small>{row.date.slice(0, 3)}</small>
                  </span>
                  <div>
                    <strong>{row.doctor}</strong>
                    <p>{row.disease}</p>
                    <small>
                      <IconClock size={14} /> {row.time}
                    </small>
                  </div>
                  <Badge>{row.status}</Badge>
                  <button
                    className="text-action"
                    onClick={() => onDetails(row)}
                  >
                    Details
                  </button>
                  <button
                    className="text-action danger-text"
                    onClick={() => onCancel(row)}
                  >
                    Cancel
                  </button>
                </article>
              ))
            ) : (
              <div className="empty-state">
                <strong>No upcoming visits</strong>
                <p>Book an appointment with your care team.</p>
              </div>
            )}
          </div>
        </SectionCard>
        <SectionCard
          title="Recent documents"
          description="Your latest reports and notes"
          action={
            <a className="section-link" href="/patient/reports">
              View all <IconArrowUpRight size={15} />
            </a>
          }
        >
          <div className="document-list">
            {reports.slice(0, 3).map((doc) => (
              <div className="document-list-row" key={doc.id}>
                <span className="document-icon">
                  <IconFileDescription size={18} />
                </span>
                <span>
                  <strong>{doc.name}</strong>
                  <small>
                    {doc.type} · {doc.date}
                  </small>
                </span>
                <button
                  className="icon-button"
                  title="Open report details"
                  onClick={() => onDetails(doc)}
                  aria-label={`View ${doc.name}`}
                >
                  <IconEye size={17} />
                </button>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
      <PatientProfile onEdit={onEdit} compact />
    </>
  );
}
function PatientAppointments({
  appointments,
  tab,
  setTab,
  onBook,
  onDetails,
  onCancel,
}: {
  appointments: Appointment[];
  tab: "Upcoming" | "Past";
  setTab: (tab: "Upcoming" | "Past") => void;
  onBook: () => void;
  onDetails: (record: Model) => void;
  onCancel: (row: Appointment) => void;
}) {
  const rows = appointments.filter((item) =>
    tab === "Upcoming"
      ? ["Due", "Scheduled"].includes(item.status)
      : !["Due", "Scheduled"].includes(item.status),
  );
  return (
    <>
      <PageHeader
        title="My appointments"
        subtitle="Keep track of upcoming visits and your care history."
        action={
          <Button onClick={onBook}>
            <IconCalendarPlus size={17} /> Book appointment
          </Button>
        }
      />
      <SectionCard title="Appointments" description="Your visit schedule">
        <div className="tab-row">
          <button
            className={tab === "Upcoming" ? "tab-active" : ""}
            onClick={() => setTab("Upcoming")}
          >
            Upcoming appointments{" "}
            <span>
              {
                appointments.filter((a) =>
                  ["Due", "Scheduled"].includes(a.status),
                ).length
              }
            </span>
          </button>
          <button
            className={tab === "Past" ? "tab-active" : ""}
            onClick={() => setTab("Past")}
          >
            Past appointments
          </button>
        </div>
        <AppointmentsTable
          rows={rows}
          onDetails={onDetails}
          onCancel={tab === "Upcoming" ? onCancel : undefined}
        />
      </SectionCard>
    </>
  );
}
function PatientProfile({
  onEdit,
  compact = false,
}: {
  onEdit: () => void;
  compact?: boolean;
}) {
  const { patients } = useHospital();
  const patient = patients[0];
  if (!patient)
    return (
      <SectionCard
        title="Health details"
        description="No patient profile is linked to this account."
      >
        <p>
          Contact the hospital team to link your account to a patient profile.
        </p>
      </SectionCard>
    );
  return (
    <SectionCard
      title="Health details"
      description="Personal information shared with your care team"
      action={
        <Button variant="secondary" onClick={onEdit}>
          Edit profile
        </Button>
      }
      className={compact ? "profile-compact" : ""}
    >
      <div className="health-details-grid">
        <Info label="Full name" value={patient.name} />
        <Info label="Gender" value={patient.gender} />
        <Info
          label="Date of birth"
          value={
            patient.dateOfBirth
              ? `${patient.dateOfBirth} · ${patient.age} years`
              : "Not provided"
          }
        />
        <Info
          label="Blood group"
          value={patient.bloodGroup || "Not provided"}
        />
        <Info
          label="Assigned doctor"
          value={patient.doctor || "Not assigned"}
        />
        <Info
          label="Emergency contact"
          value={patient.emergencyContact || "Not provided"}
        />
        <Info label="Address" value={patient.address || "Not provided"} />
        <Info label="Health details" value={patient.concern || "No notes"} />
      </div>
    </SectionCard>
  );
}
function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-field">
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}
function PatientDoctor({ doctors }: { doctors: Doctor[] }) {
  const { patients } = useHospital();
  const assignedName = patients[0]?.doctor;
  const doctor = doctors.find((item) => item.name === assignedName);
  return (
    <>
      <PageHeader
        title="My doctor"
        subtitle="Your primary care contact and clinic details."
      />
      {doctor ? (
        <section className="doctor-profile-card">
          <div className="doctor-profile-banner">
            <div className="doctor-avatar-large">
              <Initials name={doctor.name} />
            </div>
            <div>
              <span className="eyebrow">YOUR PRIMARY DOCTOR</span>
              <h2>{doctor.name}</h2>
              <p>{doctor.specialization}</p>
            </div>
            <Badge>{doctor.availability}</Badge>
          </div>
          <div className="health-details-grid">
            <Info label="Department" value={doctor.department} />
            <Info
              label="Experience"
              value={`${doctor.experience || "—"} years`}
            />
            <Info
              label="Qualification"
              value={doctor.degree || "Not provided"}
            />
            <Info label="Contact" value={doctor.phone || "Not provided"} />
            <Info label="Email" value={doctor.email || "Not provided"} />
          </div>
        </section>
      ) : (
        <SectionCard
          title="No doctor assigned"
          description="Your assigned clinician will appear here."
        >
          <p>
            Your assigned clinician will appear here when a doctor is linked to
            your patient record.
          </p>
        </SectionCard>
      )}
    </>
  );
}
function MedicationPage({
  medications,
}: {
  medications: {
    medicine: string;
    dosage: string;
    frequency: string;
    instructions: string;
    start: string;
    end: string;
  }[];
}) {
  const columns: Column<(typeof medications)[number]>[] = [
    { key: "medicine", label: "Medicine" },
    { key: "dosage", label: "Dosage" },
    { key: "frequency", label: "Frequency" },
    { key: "instructions", label: "Instructions" },
    { key: "start", label: "Start date" },
    { key: "end", label: "End date" },
  ];
  return (
    <>
      <PageHeader
        title="Medications"
        subtitle="Prescriptions from your care team."
      />
      <SectionCard
        title="Current medications"
        description="Follow the instructions provided by your clinician"
      >
        <DataTable
          columns={columns}
          rows={medications}
          empty="No medication orders are recorded for your profile."
        />
      </SectionCard>
    </>
  );
}
function DepartmentPage({ departments }: { departments: string[] }) {
  const [name, setName] = useState("");
  const { notify, createRecord, deleteRecord, departmentLookup, doctors } =
    useHospital();
  return (
    <>
      <PageHeader
        title="Departments"
        subtitle="Clinical departments and service lines."
        action={
          <form
            className="inline-add"
            onSubmit={async (e) => {
              e.preventDefault();
              if (name.trim()) {
                try {
                  await createRecord("departments", { name: name.trim() });
                  setName("");
                  notify("Department added.");
                } catch (error) {
                  notify(
                    error instanceof Error
                      ? error.message
                      : "Could not add department.",
                  );
                }
              }
            }}
          >
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="New department"
            />
            <Button type="submit">
              <IconPlus size={16} /> Add
            </Button>
          </form>
        }
      />
      <div className="department-grid">
        {departments.map((item) => (
          <article key={item} className="department-card">
            <span className="department-icon">
              <IconStethoscope size={19} />
            </span>
            <div>
              <h3>{item}</h3>
              <p>
                {doctors.filter((doctor) => doctor.department === item).length}{" "}
                clinicians · Patient care
              </p>
            </div>
            <button
              className="icon-button"
              onClick={() => {
                const id = departmentLookup.find(
                  (department) => department.name === item,
                )?.id;
                if (
                  id &&
                  window.confirm(
                    `Remove ${item}? Linked doctor profiles may prevent deletion.`,
                  )
                )
                  void deleteRecord("departments", String(id))
                    .then(() => notify("Department removed."))
                    .catch((error) =>
                      notify(
                        error instanceof Error
                          ? error.message
                          : "Could not remove department.",
                      ),
                    );
              }}
              aria-label={`Remove ${item}`}
            >
              <IconX size={16} />
            </button>
          </article>
        ))}
      </div>
    </>
  );
}
function fieldsFor(kind: string): Field[] {
  return kind === "patient"
    ? patientFields
    : kind === "doctor"
      ? doctorFields
      : kind === "appointment"
        ? appointmentFields
        : kind === "operation"
          ? operationFields
          : medicineFields;
}
function inputValue(value: unknown, type?: string): string {
  const text = String(value ?? "");
  if (type === "date" && text) {
    const parsed = new Date(text);
    if (!Number.isNaN(parsed.getTime()))
      return `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, "0")}-${String(parsed.getDate()).padStart(2, "0")}`;
  }
  if (type === "time" && text)
    return text
      .replace(/\s?(AM|PM)$/i, "")
      .split(":")
      .map((part, index) => (index ? part.slice(0, 2) : part.padStart(2, "0")))
      .join(":")
      .slice(0, 5);
  return text;
}
function RecordModal({
  kind,
  record,
  doctors,
  patients,
  departments,
  patientBooking = false,
  patientProfileEdit = false,
  onClose,
  onSubmit,
}: {
  kind: string;
  record?: Model;
  doctors: Doctor[];
  patients: Patient[];
  departments: string[];
  patientBooking?: boolean;
  patientProfileEdit?: boolean;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void | Promise<void>;
}) {
  const fields = fieldsFor(kind).filter(
    (field) =>
      (!patientBooking ||
        !["patient", "gender", "disease"].includes(field.key)) &&
      !(
        kind === "doctor" &&
        record &&
        ["email", "password"].includes(field.key)
      ) &&
      !(
        patientProfileEdit &&
        ["email", "doctor", "bloodGroup"].includes(field.key)
      ),
  );
  const title = `${record ? "Edit" : kind === "appointment" ? "Book" : "Add"} ${kind}`;
  return (
    <Modal title={title} onClose={onClose}>
      <form className="record-form" onSubmit={onSubmit}>
        {fields.map((field) => {
          let options = field.options;
          if (field.key === "doctor") options = doctors.map((doc) => doc.name);
          if (
            field.key === "patient" &&
            ["appointment", "operation"].includes(kind)
          )
            options = patients.map((patient) => patient.name);
          if (field.key === "department") options = departments;
          if (
            field.key === "patient" &&
            ["appointment", "operation"].includes(kind)
          )
            options = patients.map((patient) => patient.name);
          const value = (
            record as unknown as Record<string, unknown> | undefined
          )?.[field.key];
          const today = new Date().toISOString().slice(0, 10);
          return (
            <label className="form-field" key={field.key}>
              <span>
                {field.label}
                {field.required !== false && <i>*</i>}
              </span>
              {options ? (
                <select
                  name={field.key}
                  required={field.required !== false}
                  defaultValue={String(value ?? "")}
                >
                  <option value="" disabled>
                    Select {field.label.toLowerCase()}
                  </option>
                  {options.map((option) => (
                    <option key={option}>{option}</option>
                  ))}
                </select>
              ) : (
                <input
                  name={field.key}
                  type={field.type || "text"}
                  min={
                    field.type === "date" && kind === "appointment"
                      ? today
                      : undefined
                  }
                  minLength={field.key === "password" ? 12 : undefined}
                  required={field.required !== false}
                  defaultValue={inputValue(value, field.type)}
                  autoComplete={
                    field.key === "password" ? "new-password" : undefined
                  }
                />
              )}
            </label>
          );
        })}
        <div className="form-footer">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit">
            <IconCheck size={16} />{" "}
            {record
              ? "Save changes"
              : kind === "appointment"
                ? "Request appointment"
                : `Add ${kind}`}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function AppointmentBookModal({
  role,
  onClose,
}: {
  role: string;
  onClose: () => void;
}) {
  const {
    patients,
    departments,
    departmentLookup,
    createRecord,
    notify,
  } = useHospital();
  const today = new Date().toISOString().slice(0, 10);
  const [selectedPatientId, setSelectedPatientId] = useState(patients[0]?.id || "");
  const [department, setDepartment] = useState(departments[0] || "");
  const [dateValue, setDateValue] = useState(today);
  const [timeValue, setTimeValue] = useState("");
  const [reason, setReason] = useState("");
  const [slots, setSlots] = useState<ScheduleSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [alternatives, setAlternatives] = useState<string[]>([]);
  const departmentId = departmentLookup.find((item) => item.name === department)?.id;

  useEffect(() => {
    if (!selectedPatientId && patients.length > 0) {
      setSelectedPatientId(patients[0].id);
    }
  }, [selectedPatientId, patients]);

  useEffect(() => {
    if (!department && departments.length > 0) {
      setDepartment(departments[0]);
    }
  }, [department, departments]);

  useEffect(() => {
    if (!departmentId || !dateValue) {
      setSlots([]);
      return;
    }
    let active = true;
    setLoadingSlots(true);
    setError("");
    apiClient
      .scheduleSlots(departmentId, dateValue)
      .then((response) => {
        if (!active) return;
        setSlots(response.slots || []);
        const firstOpen = (response.slots || []).find((slot) => slot.available);
        setTimeValue((current) =>
          response.slots?.some((slot) => slot.time === current && slot.available)
            ? current
            : firstOpen?.time || "",
        );
      })
      .catch((item) => {
        if (!active) return;
        setSlots([]);
        setError(item instanceof Error ? item.message : "Could not load available slots.");
      })
      .finally(() => {
        if (active) setLoadingSlots(false);
      });
    return () => {
      active = false;
    };
  }, [departmentId, dateValue]);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setAlternatives([]);
    if (!departmentId || !dateValue || !timeValue) {
      setError("Select a department, date, and available time slot.");
      return;
    }
    setBusy(true);
    try {
      const payload: Record<string, unknown> = {
        department_id: departmentId,
        scheduled_at: `${dateValue}T${timeValue}:00`,
        reason: reason || null,
      };
      if (role !== "patient") {
        if (!selectedPatientId) {
          setError("Select a patient with a valid patient record.");
          setBusy(false);
          return;
        }
        payload.patient_id = Number(selectedPatientId);
      }
      await createRecord("appointments", payload);
      notify("Appointment booked successfully.");
      onClose();
    } catch (item) {
      const alternativesList = item instanceof ApiError ? item.alternatives : [];
      setAlternatives(alternativesList);
      setError(
        item instanceof Error ? item.message : "Could not book this appointment.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal title="Book appointment" onClose={onClose}>
      <form className="record-form" onSubmit={submit}>
        {role !== "patient" && (
          <label className="form-field">
            <span>
              Patient<i>*</i>
            </span>
            <select
              required
              value={selectedPatientId}
              onChange={(event) => setSelectedPatientId(event.target.value)}
            >
              <option value="" disabled>
                Select patient
              </option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.name} (ID: {patient.id})
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="form-field">
          <span>
            Department<i>*</i>
          </span>
          <select
            required
            value={department}
            onChange={(event) => setDepartment(event.target.value)}
          >
            <option value="" disabled>
              Select department
            </option>
            {departments.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="form-field">
          <span>
            Date<i>*</i>
          </span>
          <input
            type="date"
            required
            min={today}
            value={dateValue}
            onChange={(event) => setDateValue(event.target.value)}
          />
        </label>
        <label className="form-field">
          <span>
            Time slot<i>*</i>
          </span>
          <select
            required
            value={timeValue}
            onChange={(event) => setTimeValue(event.target.value)}
            disabled={loadingSlots}
          >
            <option value="" disabled>
              {loadingSlots
                ? "Loading slots…"
                : slots.length === 0
                  ? "No slots available on this date"
                  : "Select a time slot"}
            </option>
            {slots.map((slot) => (
              <option key={slot.time} value={slot.time} disabled={!slot.available}>
                {slot.time}
                {slot.available
                  ? ` · ${slot.remaining} opening${slot.remaining === 1 ? "" : "s"}`
                  : " · full"}
              </option>
            ))}
          </select>
        </label>
        <label className="form-field">
          <span>Reason for visit</span>
          <input
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Optional"
          />
        </label>
        {error && (
          <p role="alert" className="demo-note">
            {error}
            {alternatives.length
              ? ` Available slots: ${alternatives.join(", ")}.`
              : ""}
          </p>
        )}
        {alternatives.length > 0 && (
          <div style={{ marginTop: "0.25rem", display: "flex", flexWrap: "wrap", gap: "0.4rem", alignItems: "center" }}>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted, #64748b)" }}>Suggested slots:</span>
            {alternatives.map((slotTime) => (
              <button
                key={slotTime}
                type="button"
                className="text-action"
                style={{ padding: "0.2rem 0.5rem", border: "1px solid currentColor", borderRadius: "4px" }}
                onClick={() => setTimeValue(slotTime)}
              >
                {slotTime}
              </button>
            ))}
          </div>
        )}
        <div className="form-footer">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy || loadingSlots}>
            {busy ? "Booking…" : "Book appointment"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function PrescribeModal({
  appointment,
  onClose,
}: {
  appointment: Appointment;
  onClose: () => void;
}) {
  const { medicines, createRecord, notify } = useHospital();

  type MedRow = { medicineId: string; dosage: string; frequency: string; duration: string };
  const emptyRow = (): MedRow => ({ medicineId: "", dosage: "", frequency: "", duration: "" });

  const [rows, setRows] = useState<MedRow[]>([emptyRow()]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const medicineOptions = medicines.map((m) => ({ value: m.id, label: m.name }));

  const updateRow = (index: number, patch: Partial<MedRow>) => {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);

  const removeRow = (index: number) => {
    setRows((prev) => (prev.length === 1 ? [emptyRow()] : prev.filter((_, i) => i !== index)));
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    const filledRows = rows.filter((r) => r.medicineId);
    if (filledRows.length === 0) {
      setError("Add at least one medicine before saving.");
      return;
    }
    if (filledRows.some((r) => !r.dosage.trim() || !r.frequency.trim())) {
      setError("Please fill in dosage and frequency for every medicine.");
      return;
    }
    const ids = filledRows.map((r) => r.medicineId);
    if (new Set(ids).size !== ids.length) {
      setError("The same medicine cannot be added more than once.");
      return;
    }

    const items = filledRows.map((r) => ({
      medicine_id: Number(r.medicineId),
      dosage: r.dosage.trim(),
      frequency: r.frequency.trim(),
      duration: r.duration.trim(),
      start_date: new Date().toISOString().slice(0, 10),
    }));

    setBusy(true);
    try {
      await createRecord("prescriptions", {
        appointment_id: Number(appointment.id),
        items,
      });
      notify("Prescription saved.");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save this prescription.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title={`Prescribe medicine · ${appointment.patient}`} onClose={onClose}>
      <form className="record-form" onSubmit={submit}>
        {medicines.length === 0 ? (
          <p className="demo-note">No medicines are available in inventory.</p>
        ) : (
          <>
            {rows.map((row, index) => (
              <div
                key={index}
                style={{
                  border: "1px solid #e2e8f0",
                  borderRadius: 8,
                  padding: "12px 14px",
                  marginBottom: 12,
                  background: "#f8fafc",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: 8,
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: 13, color: "#475569" }}>
                    Medicine {index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeRow(index)}
                    title="Remove"
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      color: "#94a3b8",
                      fontSize: 18,
                      lineHeight: 1,
                      padding: "0 4px",
                    }}
                  >
                    ×
                  </button>
                </div>

                {/* Searchable medicine dropdown */}
                <div className="form-field">
                  <span>Medicine name</span>
                  <MedicineSelect
                    data={medicineOptions}
                    searchable
                    clearable
                    placeholder="Search or select a medicine…"
                    value={row.medicineId || null}
                    onChange={(val) => updateRow(index, { medicineId: val ?? "" })}
                    styles={{
                      input: { fontSize: 13 },
                    }}
                  />
                </div>

                <div
                  className="health-details-grid"
                  style={{
                    marginTop: 8,
                    display: "grid",
                    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                    gap: 12,
                    width: "100%",
                    alignItems: "start",
                  }}
                >
                  {(
                    [
                    {
                      label: "Frequency*",
                      key: "frequency",
                      placeholder: "",
                      type: "text",
                    },
                    {
                      label: "Duration (days)",
                      key: "duration",
                      placeholder: "",
                      type: "number",
                    },
                    {
                      label: "Dosage*",
                      key: "dosage",
                      placeholder: "",
                      type: "text",
                    },
                    ] satisfies Array<{
                      label: string;
                      key: "frequency" | "duration" | "dosage";
                      placeholder: string;
                      type: "text" | "number";
                    }>
                  ).map((field) => (
                    <div key={field.key} style={{ minWidth: 0 }}>
                      <span
                        style={{
                          fontSize: 12,
                          color: "#64748b",
                          display: "flex",
                          alignItems: "center",
                          height: 36,
                          marginBottom: 6,
                        }}
                      >
                        {field.label}
                      </span>

                      <input
                        type={field.type}
                        min={field.type === "number" ? 1 : undefined}
                        placeholder={field.placeholder}
                        value={row[field.key]}
                        onChange={(e) =>
                          updateRow(index, { [field.key]: e.target.value })
                        }
                        style={{
                          display: "block",
                          width: "100%",
                          height: 44,
                          boxSizing: "border-box",
                          padding: "0 12px",
                          border: "1px solid #dbe2ea",
                          borderRadius: 8,
                          fontSize: 14,
                          outline: "none",
                          backgroundColor: "#fff",
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div style={{ marginBottom: 12 }}>
              <Button
                type="button"
                variant="secondary"
                onClick={addRow}
              >
                + Add another medicine
              </Button>
            </div>
          </>
        )}

        {error && (
          <p role="alert" className="demo-note">
            {error}
          </p>
        )}

        <div className="form-footer">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy || medicines.length === 0}>
            {busy ? "Saving…" : "Save prescription"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function PrescriptionsReceived() {
  const { prescriptions } = useHospital();
  const columns: Column<(typeof prescriptions)[number]>[] = [
    { key: "patient", label: "Patient" },
    { key: "doctor", label: "Doctor" },
    { key: "appointment", label: "Appointment" },
    { key: "medicine", label: "Medicine" },
    { key: "dosage", label: "Dosage" },
    { key: "frequency", label: "Frequency" },
    { key: "duration", label: "Duration" },
    { key: "prescribedAt", label: "Prescribed" },
  ];
  return (
    <SectionCard
      title="Prescriptions received"
      description="Medicines prescribed by doctors. This list does not change inventory stock."
    >
      <DataTable
        columns={columns}
        rows={prescriptions}
        empty="No prescriptions have been written yet."
      />
    </SectionCard>
  );
}

function DetailsModal({
  record,
  onClose,
}: {
  record: Model;
  onClose: () => void;
}) {
  const entries = Object.entries(
    record as unknown as Record<string, unknown>,
  ).filter(([key]) => key !== "id");
  const name = String(
    (record as unknown as Record<string, unknown>).name ||
      (record as unknown as Record<string, unknown>).patient ||
      (record as unknown as Record<string, unknown>).medicine ||
      (record as unknown as Record<string, unknown>).doctor ||
      "Record details",
  );
  return (
    <Modal
      title="Record details"
      onClose={onClose}
      footer={<Button onClick={onClose}>Done</Button>}
    >
      <div className="details-title">
        <Initials name={name} />
        <span>
          <strong>{name}</strong>
        </span>
      </div>
      <div className="health-details-grid detail-grid">
        {entries.map(([key, value]) => (
          <Info
            key={key}
            label={key
              .replace(/([A-Z])/g, " $1")
              .replace(/^./, (s) => s.toUpperCase())}
            value={String(value || "—")}
          />
        ))}
      </div>
    </Modal>
  );
}

// Report upload

function ReportUploadModal({
  role,
  onClose,
}: {
  role: string;
  onClose: () => void;
}) {
  const { patients, refresh, notify } = useHospital();
  const [patientId, setPatientId] = useState(patients[0]?.id || "");
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("Medical report");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    if (!file || !patientId) {
      setError("Choose a patient and a PDF, JPEG, or PNG file.");
      return;
    }
    setBusy(true);
    try {
      await apiClient.uploadReport(file, {
        patient_id: Number(patientId),
        document_name: file.name,
        document_type: documentType,
        report_date: date,
      });
      await refresh();
      onClose();
      notify("Report uploaded securely.");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not upload this report.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal title="Upload report" onClose={onClose}>
      <form className="record-form" onSubmit={submit}>
        {patients.length === 0 ? (
          <p className="demo-note">
            No patient records are available in your account.
          </p>
        ) : (
          <>
            {role !== "patient" && (
              <label className="form-field">
                <span>
                  Patient<i>*</i>
                </span>
                <select
                  required
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                >
                  {patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="form-field">
              <span>
                Document type<i>*</i>
              </span>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
              >
                <option>Medical report</option>
                <option>Lab report</option>
                <option>Imaging</option>
                <option>Discharge summary</option>
                <option>Other</option>
              </select>
            </label>
            <label className="form-field">
              <span>
                Report date<i>*</i>
              </span>
              <input
                type="date"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </label>
            <label className="form-field">
              <span>
                File (PDF, JPEG, PNG; max 10 MB)<i>*</i>
              </span>
              <input
                type="file"
                accept="application/pdf,image/jpeg,image/png"
                required
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>
          </>
        )}
        {error && (
          <p role="alert" className="demo-note">
            {error}
          </p>
        )}
        <div className="form-footer">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy || patients.length === 0}>
            {busy ? "Uploading…" : "Upload report"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
