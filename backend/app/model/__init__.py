from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Department(Base):
    __tablename__ = "departments"
    department_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Doctor(Base):
    __tablename__ = "doctors"
    doctor_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), unique=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.department_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialization: Mapped[str] = mapped_column(String(120), nullable=False)
    availability: Mapped[str] = mapped_column(String(120), nullable=False, default="Monday - Friday (09:00 - 17:00)")
    phone: Mapped[str | None] = mapped_column(String(32))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    degree: Mapped[str | None] = mapped_column(String(120))


class Patient(Base):
    __tablename__ = "patients"
    patient_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), unique=True)
    primary_doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.doctor_id", ondelete="SET NULL", onupdate="CASCADE"), index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[object | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(24))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(254), index=True)
    blood_group: Mapped[str | None] = mapped_column(String(8))
    address: Mapped[str | None] = mapped_column(String(500))
    emergency_contact_name: Mapped[str | None] = mapped_column(String(201))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32))


class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.patient_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.doctor_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    scheduled_at: Mapped[object] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="scheduled", server_default="scheduled")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())


class Operation(Base):
    __tablename__ = "operations"
    operation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.patient_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    lead_doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.doctor_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    procedure_name: Mapped[str] = mapped_column(String(200), nullable=False)
    operation_at: Mapped[object] = mapped_column(DateTime, nullable=False)
    follow_up_at: Mapped[object | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="scheduled")
    report_summary: Mapped[str | None] = mapped_column(Text)


class Room(Base):
    __tablename__ = "rooms"
    room_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="available")


class RoomVisit(Base):
    __tablename__ = "room_visits"
    visit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.patient_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.doctor_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.room_id", ondelete="SET NULL", onupdate="CASCADE"), index=True)
    scheduled_at: Mapped[object] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="scheduled")
    notes: Mapped[str | None] = mapped_column(Text)


class Medicine(Base):
    __tablename__ = "medicines"
    medicine_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    manufacturer: Mapped[str | None] = mapped_column(String(160))
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price: Mapped[object] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    expiry_date: Mapped[object | None] = mapped_column(Date, index=True)


class Prescription(Base):
    __tablename__ = "prescriptions"
    prescription_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.patient_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.doctor_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.appointment_id", ondelete="SET NULL", onupdate="CASCADE"), index=True)
    prescribed_at: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.prescription_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.medicine_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    dosage: Mapped[str] = mapped_column(String(120), nullable=False)
    frequency: Mapped[str] = mapped_column(String(120), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[object | None] = mapped_column(Date)
    end_date: Mapped[object | None] = mapped_column(Date)


class Report(Base):
    __tablename__ = "reports"
    report_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.patient_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.appointment_id", ondelete="SET NULL", onupdate="CASCADE"), index=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    report_date: Mapped[object] = mapped_column(Date, nullable=False)
    file_storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)


class SessionRecord(Base):
    __tablename__ = "sessions"
    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[object] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

