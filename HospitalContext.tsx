import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { apiClient, ApiUser } from "../api";
import {
  Appointment,
  Doctor,
  Medicine,
  Operation,
  Patient,
  Report,
  RoomVisit,
} from "../data/mockData";

interface DataState {
  patients: Patient[];
  doctors: Doctor[];
  appointments: Appointment[];
  operations: Operation[];
  medicines: Medicine[];
  reports: Report[];
  visits: RoomVisit[];
  departments: string[];
  departmentLookup: { id: number; name: string }[];
}
interface Medication {
  medicine: string;
  dosage: string;
  frequency: string;
  instructions: string;
  start: string;
  end: string;
}
export interface ReceivedPrescription {
  id: string;
  patient: string;
  doctor: string;
  appointment: string;
  prescribedAt: string;
  medicine: string;
  dosage: string;
  frequency: string;
  duration: string;
}
interface HospitalContextValue extends DataState {
  user: ApiUser | null;
  loading: boolean;
  loadError: string;
  refresh: () => Promise<void>;
  createRecord: (
    resource: string,
    payload: Record<string, unknown>,
  ) => Promise<void>;
  updateRecord: (
    resource: string,
    id: string,
    payload: Record<string, unknown>,
  ) => Promise<void>;
  deleteRecord: (resource: string, id: string) => Promise<void>;
  medications: Medication[];
  prescriptions: ReceivedPrescription[];
  setUser: (user: ApiUser | null) => void;
  notify: (message: string) => void;
  notice: string;
}
const empty: DataState = {
  patients: [],
  doctors: [],
  appointments: [],
  operations: [],
  medicines: [],
  reports: [],
  visits: [],
  departments: [],
  departmentLookup: [],
};
const HospitalContext = createContext<HospitalContextValue | null>(null);
export const useHospital = () => {
  const value = useContext(HospitalContext);
  if (!value)
    throw new Error("useHospital must be used inside HospitalProvider");
  return value;
};

const niceDate = (value?: string | null) =>
  value
    ? new Date(value).toLocaleDateString("en-US", {
        month: "short",
        day: "2-digit",
        year: "numeric",
      })
    : "";
const niceTime = (value?: string | null) =>
  value
    ? new Date(value).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

export const HospitalProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [data, setData] = useState<DataState>(empty);
  const [user, setUser] = useState<ApiUser | null>(null);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [prescriptions, setPrescriptions] = useState<ReceivedPrescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [notice, setNotice] = useState("");
  const notify = useCallback((message: string) => {
    setNotice(message);
    window.setTimeout(() => setNotice(""), 3200);
  }, []);

  const refresh = useCallback(async () => {
    if (!user) {
      setData(empty);
      setMedications([]);
      setPrescriptions([]);
      return;
    }
    setLoadError("");
    try {
      const resources = [
        "departments",
        "doctors",
        "patients",
        "appointments",
        "operations",
        "medicines",
        "reports",
        "room-visits",
        "prescriptions",
        "prescription-items",
      ];
      const [
        departments,
        doctors,
        patients,
        appointments,
        operations,
        medicines,
        reports,
        visits,
        prescriptionRecords,
        prescriptionItems,
      ] = await Promise.all(
        resources.map((r) => apiClient.list<Record<string, any>>(r)),
      );
      const doctorNames = new Map(doctors.map((d) => [d.doctor_id,`${d.first_name} ${d.last_name}`.trim(),]),);
      const patientNames = new Map(patients.map((p) => [p.patient_id,`${p.first_name} ${p.last_name}`.trim(),]),);
      const patientGenders = new Map(patients.map((p) => [p.patient_id, p.gender || ""]),);
      const medicineNames = new Map(medicines.map((m) => [m.medicine_id, m.name]),);
      setMedications(
        prescriptionItems.map((item) => ({
          medicine:
            medicineNames.get(item.medicine_id) ||
            `Medicine ${item.medicine_id}`,
          dosage: item.dosage,
          frequency: item.frequency,
          instructions: item.instructions || "",
          start: niceDate(item.start_date),
          end: niceDate(item.end_date),
        })),
      );
      const prescriptionLookup = new Map(
        prescriptionRecords.map((row) => [row.prescription_id, row]),
      );
      setPrescriptions(
        prescriptionItems.map((item) => {
          const parent = prescriptionLookup.get(item.prescription_id) || {};
          return {
            id: String(item.item_id),
            patient:
              patientNames.get(parent.patient_id) ||
              `Patient ${parent.patient_id || ""}`,
            doctor:
              doctorNames.get(parent.doctor_id) ||
              `Doctor ${parent.doctor_id || ""}`,
            appointment: parent.appointment_id
              ? `Appointment ${parent.appointment_id}`
              : "Not linked",
            prescribedAt: niceDate(parent.prescribed_at),
            medicine:
              medicineNames.get(item.medicine_id) ||
              `Medicine ${item.medicine_id}`,
            dosage: item.dosage,
            frequency: item.frequency,
            duration:
              item.start_date || item.end_date
                ? `${niceDate(item.start_date) || "—"} – ${niceDate(item.end_date) || "—"}`
                : item.instructions || "—",
          };
        }),
      );
      setData({
        departments: departments.map((d) => d.name),
        departmentLookup: departments.map((d) => ({
          id: d.department_id,
          name: d.name,
        })),
        doctors: doctors.map((d) => ({
          id: String(d.doctor_id),
          userId: d.user_id ? Number(d.user_id) : undefined,
          name: doctorNames.get(d.doctor_id) || "Doctor",
          department:
            departments.find((x) => x.department_id === d.department_id)
              ?.name || "",
          specialization: d.specialization,
          availability: d.availability as Doctor["availability"],
          phone: d.phone || "",
          email: d.email || "",
          experience: d.years_experience || 0,
          degree: d.degree || "",
        })),
        patients: patients.map((p) => {
          const visits = appointments
            .filter((a) => a.patient_id === p.patient_id)
            .sort(
              (a, b) =>
                new Date(b.scheduled_at).getTime() -
                new Date(a.scheduled_at).getTime(),
            );
          const next = visits.find(
            (a) =>
              new Date(a.scheduled_at).getTime() >= Date.now() &&
              ["scheduled", "requested"].includes(a.status),
          );
          const last = visits.find((a) => a.status === "completed");
          return {
            id: String(p.patient_id),
            name: `${p.first_name} ${p.last_name}`.trim(),
            gender: p.gender || "",
            age: p.date_of_birth
              ? Math.max(
                  0,
                  new Date().getFullYear() -
                    new Date(p.date_of_birth).getFullYear(),
                )
              : 0,
            dateOfBirth: p.date_of_birth || "",
            phone: p.phone || "",
            email: p.email || "",
            doctor: doctorNames.get(p.primary_doctor_id) || "",
            concern: visits[0]?.reason || "",
            lastVisit: niceDate(last?.scheduled_at),
            nextAppointment: niceDate(next?.scheduled_at),
            bloodGroup: p.blood_group || "",
            emergencyContact: [
              p.emergency_contact_name,
              p.emergency_contact_phone,
            ]
              .filter(Boolean)
              .join(" · "),
            emergencyContactName: p.emergency_contact_name || "",
            emergencyContactPhone: p.emergency_contact_phone || "",
            address: p.address || "",
          };
        }),
        appointments: appointments.map((a) => {
          const doctor = doctors.find((item) => item.doctor_id === a.doctor_id);
          const labels: Record<string, Appointment["status"]> = {
            scheduled: "Scheduled",
            requested: "Due",
            completed: "Completed",
            cancelled: "Cancelled",
          };
          return {
            id: String(a.appointment_id),
            patient: patientNames.get(a.patient_id) || `Patient ${a.patient_id}`,
            doctor: doctorNames.get(a.doctor_id) || `Doctor ${a.doctor_id}`,
            department:
              departments.find((item) => item.department_id === doctor?.department_id)
                ?.name || "",
            gender: patientGenders.get(a.patient_id) || "",
            date: niceDate(a.scheduled_at),
            time: niceTime(a.scheduled_at),
            disease: a.reason || "",
            reason: a.reason || "",
            rawStatus: a.status,
            status: labels[a.status] || a.status,
          };
        }),
        operations: operations.map((o) => ({
          id: String(o.operation_id),
          patient: patientNames.get(o.patient_id) || `Patient ${o.patient_id}`,
          doctor:
            doctorNames.get(o.lead_doctor_id) || `Doctor ${o.lead_doctor_id}`,
          operationDate: niceDate(o.operation_at),
          followUp: niceDate(o.follow_up_at),
          disease: o.procedure_name,
          rawStatus: o.status,
          status: o.status
            .replaceAll("_", " ")
            .replace(/^./, (letter: string) => letter.toUpperCase()),
          report: o.report_summary || "",
        })),
        medicines: medicines.map((m) => ({
          id: String(m.medicine_id),
          name: m.name,
          category: m.category || "",
          stock: m.stock_quantity,
          price: Number(m.unit_price),
          expiry: niceDate(m.expiry_date),
          company: m.manufacturer || "",
        })),
        reports: reports.map((r) => ({
          id: String(r.report_id),
          name: r.document_name,
          type: r.document_type,
          date: niceDate(r.report_date),
          uploadedBy: `User ${r.uploaded_by_user_id}`,
          patient: patientNames.get(r.patient_id) || `Patient ${r.patient_id}`,
        })),
        visits: visits.map((v) => ({
          id: String(v.visit_id),
          patient: patientNames.get(v.patient_id) || `Patient ${v.patient_id}`,
          doctor: doctorNames.get(v.doctor_id) || `Doctor ${v.doctor_id}`,
          room: v.room_id ? `Room ${v.room_id}` : "Unassigned",
          date: niceDate(v.scheduled_at),
          time: niceTime(v.scheduled_at),
          status: v.status,
        })),
      });
    } catch (error) {
      setLoadError(
        error instanceof Error
          ? error.message
          : "Could not load hospital records.",
      );
    }
  }, [user]);

  useEffect(() => {
    let active = true;
    apiClient
      .me()
      .then((u) => {
        if (active) setUser(u);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    if (!loading) void refresh();
  }, [loading, refresh]);

  const mutate = useCallback(
    async (
      method: "create" | "update" | "delete",
      resource: string,
      id?: string,
      payload?: Record<string, unknown>,
    ) => {
      if (method === "create") await apiClient.create(resource, payload || {});
      if (method === "update")
        await apiClient.update(resource, id || "", payload || {});
      if (method === "delete") await apiClient.remove(resource, id || "");
      await refresh();
    },
    [refresh],
  );
  const value = useMemo(
    () => ({
      ...data,
      user,
      setUser,
      loading,
      loadError,
      refresh,
      createRecord: (r: string, p: Record<string, unknown>) =>
        mutate("create", r, undefined, p),
      updateRecord: (r: string, id: string, p: Record<string, unknown>) =>
        mutate("update", r, id, p),
      deleteRecord: (r: string, id: string) => mutate("delete", r, id),
      medications,
      prescriptions,
      notify,
      notice,
    }),
    [
      data,
      user,
      loading,
      loadError,
      refresh,
      mutate,
      notify,
      notice,
      medications,
      prescriptions,
    ],
  );
  return (
    <HospitalContext.Provider value={value}>
      {children}
    </HospitalContext.Provider>
  );
};
