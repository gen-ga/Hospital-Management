import os
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from ..core.database import get_db
from .. import models
from ..services import scheduling
from .auth import current_user

router = APIRouter(prefix="/api")
FILE_ROOT = Path(os.getenv("FILE_STORAGE_DIR", Path(__file__).resolve().parents[2] / "storage")).resolve()
RESOURCES = {
    "departments": (models.Department, "department_id"), 
    "doctors": (models.Doctor, "doctor_id"),
    "patients": (models.Patient, "patient_id"), 
    "appointments": (models.Appointment, "appointment_id"),
    "operations": (models.Operation, "operation_id"), 
    "rooms": (models.Room, "room_id"),
    "room-visits": (models.RoomVisit, "visit_id"), 
    "medicines": (models.Medicine, "medicine_id"),
    "prescriptions": (models.Prescription, "prescription_id"), 
    "prescription-items": (models.PrescriptionItem, "item_id"),
    "reports": (models.Report, "report_id"),
}
READ_ROLES = {"departments": {"ADMIN", "DOCTOR", "PATIENT"}, "doctors": {"ADMIN", "DOCTOR", "PATIENT"}, "patients": {"ADMIN", "DOCTOR", "PATIENT"},
              "medicines": {"ADMIN", "DOCTOR", "PATIENT"}}
PATIENT_OWNED = {"appointments", "operations", "room-visits", "prescriptions", "prescription-items", "reports"}
DOCTOR_OWNED = {"appointments", "operations", "room-visits", "prescriptions", "prescription-items", "reports", "patients"}
ADMIN_WRITE_ONLY = {"departments", "doctors", "rooms", "medicines"}


def record_dict(row: Any) -> dict[str, Any]:
    result = {column.key: getattr(row, column.key) for column in inspect(row).mapper.column_attrs if column.key != "password_hash"}
    if isinstance(row, models.Report): result.pop("file_storage_key", None)
    return {key: value.isoformat() if isinstance(value, (date, datetime)) else str(value) if isinstance(value, Decimal) else value for key, value in result.items()}


def _scoped(query, resource: str, user: models.User):
    if user.role == "ADMIN":
        return query
    if resource in {"departments", "doctors", "medicines"}:
        return query
    if resource == "patients" and user.role == "DOCTOR":
        doctor_id = select(models.Doctor.doctor_id).where(models.Doctor.user_id == user.user_id).scalar_subquery()
        return query.filter(models.Patient.primary_doctor_id == doctor_id)
    if resource == "patients" and user.role == "PATIENT":
        return query.filter(models.Patient.user_id == user.user_id)
    if resource in PATIENT_OWNED:
        if user.role == "PATIENT":
            if resource in ("appointments", "operations", "room-visits", "prescriptions"):
                entity = {"appointments": models.Appointment, "operations": models.Operation, "room-visits": models.RoomVisit, "prescriptions": models.Prescription}[resource]
                query = query.join(models.Patient, models.Patient.patient_id == entity.patient_id)
            elif resource == "prescription-items":
                query = query.join(models.Prescription).join(models.Patient, models.Patient.patient_id == models.Prescription.patient_id)
            else:
                query = query.join(models.Patient, models.Patient.patient_id == models.Report.patient_id)
            return query.filter(models.Patient.user_id == user.user_id)
        if user.role == "DOCTOR":
            doctor_id = select(models.Doctor.doctor_id).where(models.Doctor.user_id == user.user_id).scalar_subquery()
            if resource in ("appointments", "operations", "room-visits", "prescriptions"):
                entity = {"appointments": models.Appointment, "operations": models.Operation, "room-visits": models.RoomVisit, "prescriptions": models.Prescription}[resource]
                doctor_field = "lead_doctor_id" if resource == "operations" else "doctor_id"
                return query.filter(getattr(entity, doctor_field) == doctor_id)
            if resource == "prescription-items":
                return query.join(models.Prescription).filter(models.Prescription.doctor_id == doctor_id)
            return query.filter(models.Report.patient_id.in_(select(models.Patient.patient_id).where(models.Patient.primary_doctor_id == doctor_id)))
    return query.filter(False)


def authorize_read(resource: str, user: models.User):
    if user.role == "ADMIN" or user.role in READ_ROLES.get(resource, set()) or resource in PATIENT_OWNED and user.role in {"DOCTOR", "PATIENT"}:
        return
    raise HTTPException(403, "You do not have permission to view this resource")


DOCTOR_APPOINTMENT_STATUSES = {"scheduled", "requested", "completed"}
PATIENT_APPOINTMENT_STATUSES = {"cancelled"}


def authorize_write(resource: str, user: models.User, method: str):
    if user.role == "ADMIN":
        return
    if method == "POST" and resource == "appointments" and user.role == "PATIENT":
        return
    if method == "PATCH" and resource == "appointments" and user.role == "PATIENT":
        return
    if method == "PATCH" and resource == "patients" and user.role == "PATIENT":
        return
    if user.role == "DOCTOR" and method == "POST" and resource in {"prescriptions", "prescription-items"}:
        return
    if user.role == "DOCTOR" and method in {"PATCH", "PUT"} and resource in {"appointments", "operations", "room-visits"}:
        return
    raise HTTPException(403, "You do not have permission to change this resource")


def _linked_doctor(db: Session, user: models.User) -> models.Doctor:
    doctor = db.query(models.Doctor).filter_by(user_id=user.user_id).first()
    if not doctor:
        raise HTTPException(403, "No doctor profile is linked to this account")
    return doctor


def _normalize_appointment_status(value: str) -> str:
    status = str(value or "").strip().lower().replace(" ", "_")
    if status == "due":
        return "requested"
    return status


def _create_prescription_bundle(db: Session, user: models.User, payload: dict[str, Any]) -> models.Prescription:
    items = payload.pop("items", None)
    if not isinstance(items, list) or not items:
        raise HTTPException(422, "Select at least one medicine to prescribe")
    parsed = _parse_payload(models.Prescription, {key: value for key, value in payload.items() if key != "items"}, True)
    if user.role == "DOCTOR":
        doctor = _linked_doctor(db, user)
        parsed["doctor_id"] = doctor.doctor_id
        appointment_id = parsed.get("appointment_id")
        if not appointment_id:
            raise HTTPException(422, "Prescriptions must be linked to an assigned appointment")
        appointment = db.query(models.Appointment).filter_by(appointment_id=appointment_id, doctor_id=doctor.doctor_id).first()
        if not appointment:
            raise HTTPException(403, "You can only prescribe for appointments assigned to you")
        if appointment.status == "cancelled":
            raise HTTPException(409, "Cannot prescribe medicines for a cancelled appointment")
        parsed["patient_id"] = appointment.patient_id
    else:
        appointment_id = parsed.get("appointment_id")
        if appointment_id:
            appointment = db.query(models.Appointment).filter_by(appointment_id=appointment_id).first()
            if not appointment:
                raise HTTPException(404, "Appointment not found")
            if appointment.status == "cancelled":
                raise HTTPException(409, "Cannot prescribe medicines for a cancelled appointment")
            if parsed.get("patient_id") and parsed["patient_id"] != appointment.patient_id:
                raise HTTPException(422, "The appointment does not belong to this patient")
            parsed["patient_id"] = parsed.get("patient_id") or appointment.patient_id
            parsed["doctor_id"] = parsed.get("doctor_id") or appointment.doctor_id
    if not db.get(models.Patient, parsed.get("patient_id")):
        raise HTTPException(404, "Patient not found")
    if not db.get(models.Doctor, parsed.get("doctor_id")):
        raise HTTPException(404, "Doctor not found")
    row = models.Prescription(**parsed)
    db.add(row)
    db.flush()
    for raw_item in items:
        if not isinstance(raw_item, dict):
            raise HTTPException(422, "Each prescribed medicine must include dosage and frequency")
        duration = raw_item.pop("duration", None)
        item_payload = _parse_payload(models.PrescriptionItem, raw_item, True)
        item_payload["prescription_id"] = row.prescription_id
        if not db.get(models.Medicine, item_payload.get("medicine_id")):
            raise HTTPException(404, "A selected medicine was not found in inventory")
        if duration and not item_payload.get("end_date"):
            start = item_payload.get("start_date") or date.today()
            item_payload["start_date"] = start
            try:
                days = int(str(duration).split()[0])
                item_payload["end_date"] = start + timedelta(days=days)
            except (TypeError, ValueError):
                extra = f"Duration: {duration}"
                item_payload["instructions"] = f"{item_payload.get('instructions') or ''} {extra}".strip()
        db.add(models.PrescriptionItem(**item_payload))
    return row


def _parse_payload(entity, payload: dict[str, Any], creating: bool):
    valid = {column.key: column for column in inspect(entity).mapper.column_attrs}
    primary_keys = {column.key for column in inspect(entity).mapper.primary_key}
    forbidden = {"password_hash", "created_at", *primary_keys}
    if entity is models.User:
        forbidden |= {"role", "is_active"}
    unknown = set(payload) - set(valid)
    if unknown:
        raise HTTPException(422, f"Unknown fields: {', '.join(sorted(unknown))}")
    result = {}
    for key, value in payload.items():
        if key in forbidden:
            raise HTTPException(422, f"Field '{key}' cannot be changed here")
        column = valid[key].columns[0]
        try:
            if value is not None and isinstance(value, str):
                if column.type.python_type is datetime:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
                elif column.type.python_type is date:
                    value = date.fromisoformat(value)
                elif column.type.python_type is int:
                    value = int(value)
                elif column.type.python_type is Decimal:
                    value = Decimal(value)
            result[key] = value
        except (ValueError, TypeError, NotImplementedError):
            raise HTTPException(422, f"Invalid value for '{key}'")
    return result


@router.get("/schedule/slots")
def schedule_slots(department_id: int, date: date, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if user.role not in {"ADMIN", "PATIENT", "DOCTOR"}:
        raise HTTPException(403, "You do not have permission to view this resource")
    if not db.get(models.Department, department_id):
        raise HTTPException(404, "Department not found")
    return scheduling.list_slots(db, department_id, date)


@router.get("/{resource}")
def list_records(resource: str, request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if resource not in RESOURCES:
        raise HTTPException(404, "Resource not found")
    authorize_read(resource, user)
    entity, _ = RESOURCES[resource]
    query = select(entity)
    if user.role != "ADMIN":
        query = _scoped(db.query(entity), resource, user).with_entities(entity)
        records = query.order_by(getattr(entity, RESOURCES[resource][1]).desc()).limit(500).all()
    else:
        records = db.scalars(select(entity).order_by(getattr(entity, RESOURCES[resource][1]).desc()).limit(500)).all()
    serialized = [record_dict(row) for row in records]
    if resource == "doctors":
        linked_user_ids = {row.user_id for row in records if row.user_id and (user.role == "ADMIN" or row.user_id == user.user_id)}
        account_emails = dict(db.query(models.User.user_id, models.User.email).filter(models.User.user_id.in_(linked_user_ids)).all()) if linked_user_ids else {}
        for row, item in zip(records, serialized):
            item["email"] = account_emails.get(row.user_id)
    return serialized


@router.post("/{resource}", status_code=201)
async def create_record(resource: str, request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if resource not in RESOURCES: raise HTTPException(404, "Resource not found")
    authorize_write(resource, user, "POST")
    entity, _ = RESOURCES[resource]
    body = await request.json()
    if resource == "prescriptions" and isinstance(body, dict) and body.get("items"):
        try:
            row = _create_prescription_bundle(db, user, body)
            db.commit(); db.refresh(row)
        except IntegrityError as exc:
            db.rollback(); raise HTTPException(409, "The record conflicts with a constraint or linked record") from exc
        return record_dict(row)
    if resource == "appointments":
        department_id = body.pop("department_id", None)
        if user.role == "PATIENT":
            patient = db.query(models.Patient).filter_by(user_id=user.user_id).first()
            if not patient: raise HTTPException(403, "No patient profile is linked to this account")
            body["patient_id"] = patient.patient_id
            body.pop("doctor_id", None)
        payload = _parse_payload(entity, body, True)
        if "patient_id" not in payload or "scheduled_at" not in payload:
            raise HTTPException(422, "Patient and appointment time are required")
        try:
            row = scheduling.book_appointment(
                db,
                patient_id=payload["patient_id"],
                scheduled_at=payload["scheduled_at"],
                department_id=int(department_id) if department_id else None,
                doctor_id=payload.get("doctor_id"),
                reason=payload.get("reason"),
                notes=payload.get("notes"),
                status=payload.get("status"),
            )
            db.commit(); db.refresh(row)
        except IntegrityError as exc:
            db.rollback(); raise HTTPException(409, "The record conflicts with a constraint or linked record") from exc
        return record_dict(row)
    if resource == "prescriptions" and user.role == "DOCTOR":
        raise HTTPException(422, "Select at least one medicine to prescribe")
    payload = _parse_payload(entity, body, True)
    if resource == "reports": payload["uploaded_by_user_id"] = user.user_id
    if resource == "prescription-items" and user.role == "DOCTOR":
        doctor = _linked_doctor(db, user)
        prescription = db.get(models.Prescription, payload.get("prescription_id"))
        if not prescription or prescription.doctor_id != doctor.doctor_id:
            raise HTTPException(403, "You can only add medicines to your own prescriptions")
    row = entity(**payload)
    db.add(row)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "The record conflicts with a constraint or linked record") from exc
    return record_dict(row)


@router.get("/{resource}/{record_id:int}")
def get_record(resource: str, record_id: int, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if resource not in RESOURCES: raise HTTPException(404, "Resource not found")
    authorize_read(resource, user)
    entity, id_field = RESOURCES[resource]
    query = db.query(entity).filter(getattr(entity, id_field) == record_id)
    row = query.first() if user.role == "ADMIN" else _scoped(query, resource, user).first()
    if not row: raise HTTPException(404, "Record not found")
    result = record_dict(row)
    if resource == "doctors" and row.user_id and (user.role == "ADMIN" or row.user_id == user.user_id):
        account = db.get(models.User, row.user_id)
        result["email"] = account.email if account else None
    elif resource == "doctors":
        result["email"] = None
    return result


@router.patch("/{resource}/{record_id:int}")
async def update_record(resource: str, record_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if resource not in RESOURCES: raise HTTPException(404, "Resource not found")
    authorize_write(resource, user, "PATCH")
    entity, id_field = RESOURCES[resource]
    query = db.query(entity).filter(getattr(entity, id_field) == record_id)
    row = query.first() if user.role == "ADMIN" else _scoped(query, resource, user).first()
    if not row: raise HTTPException(404, "Record not found")
    changes = _parse_payload(entity, await request.json(), False)
    if user.role == "PATIENT" and resource == "appointments":
        if set(changes) != {"status"}:
            raise HTTPException(403, "Patients can only cancel their own upcoming appointments")
        status = _normalize_appointment_status(changes["status"])
        if status not in PATIENT_APPOINTMENT_STATUSES:
            raise HTTPException(403, "Patients can only cancel their own upcoming appointments")
        if row.status not in {"scheduled", "requested"} or row.scheduled_at <= datetime.now():
            raise HTTPException(409, "Only upcoming scheduled appointments can be cancelled")
        changes["status"] = "cancelled"
    if user.role == "PATIENT" and resource == "patients":
        allowed = {"first_name", "last_name", "date_of_birth", "gender", "phone", "address", "emergency_contact_name", "emergency_contact_phone"}
        if set(changes) - allowed:
            raise HTTPException(403, "Patients can only update their contact and demographic details")
    if user.role == "DOCTOR":
        allowed_by_resource = {"appointments": {"status", "notes"}, "operations": {"status", "report_summary"}, "room-visits": {"status", "notes"}}
        if set(changes) - allowed_by_resource.get(resource, set()):
            raise HTTPException(403, "Doctors can only update clinical status and notes on assigned records")
        if resource == "appointments" and "status" in changes:
            status = _normalize_appointment_status(changes["status"])
            if status not in DOCTOR_APPOINTMENT_STATUSES:
                raise HTTPException(403, "Doctors can mark assigned appointments as scheduled, due, or completed")
            if row.status == "cancelled":
                raise HTTPException(409, "Cannot modify a cancelled appointment")
            changes["status"] = status
        if resource == "operations" and "status" in changes and str(changes["status"]).lower() not in {"scheduled", "in_progress", "completed", "cancelled"}:
            raise HTTPException(422, "Choose a valid operation status")
    if user.role == "ADMIN" and resource == "appointments" and "status" in changes:
        status = _normalize_appointment_status(changes["status"])
        if status not in {"scheduled", "requested", "completed", "cancelled"}:
            raise HTTPException(422, "Invalid appointment status")
        changes["status"] = status
    for key, value in changes.items(): setattr(row, key, value)
    try:
        db.commit(); db.refresh(row)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "The change conflicts with a constraint or linked record") from exc
    return record_dict(row)


@router.delete("/{resource}/{record_id:int}", status_code=204)
def delete_record(resource: str, record_id: int, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if resource not in RESOURCES: raise HTTPException(404, "Resource not found")
    authorize_write(resource, user, "DELETE")
    entity, id_field = RESOURCES[resource]
    row = db.query(entity).filter(getattr(entity, id_field) == record_id).first()
    if not row: raise HTTPException(404, "Record not found")
    storage_key = row.file_storage_key if resource == "reports" else None
    db.delete(row)
    try: db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "This record has linked records and cannot be deleted") from exc
    if storage_key and Path(storage_key).name == storage_key:
        (FILE_ROOT / storage_key).unlink(missing_ok=True)


@router.post("/reports/upload", status_code=201)
async def upload_report(request: Request, patient_id: int, document_name: str, document_type: str, report_date: date | None = None,
                        appointment_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    patient = db.query(models.Patient).filter_by(patient_id=patient_id).first()
    if not patient: raise HTTPException(404, "Patient not found")
    if user.role == "PATIENT":
        own = db.query(models.Patient).filter_by(patient_id=patient_id, user_id=user.user_id).first()
        if not own: raise HTTPException(403, "Patients can only upload to their own record")
        patient = own
    elif user.role == "DOCTOR":
        doctor = db.query(models.Doctor).filter_by(user_id=user.user_id).first()
        if not doctor or patient.primary_doctor_id != doctor.doctor_id:
            raise HTTPException(403, "You can only upload to patients under your care")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    extensions = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}
    if content_type not in extensions: raise HTTPException(415, "Only PDF, JPEG, and PNG reports are accepted")
    content = await request.body()
    if not content or len(content) > 10 * 1024 * 1024: raise HTTPException(413, "Report files must be between 1 byte and 10 MB")
    signatures = {"application/pdf": content.startswith(b"%PDF-"), "image/jpeg": content.startswith(b"\xff\xd8\xff"), "image/png": content.startswith(b"\x89PNG\r\n\x1a\n")}
    if not signatures[content_type]: raise HTTPException(415, "The file contents do not match the declared document type")
    if appointment_id is not None and not db.query(models.Appointment).filter_by(appointment_id=appointment_id, patient_id=patient_id).first():
        raise HTTPException(422, "The appointment does not belong to this patient")
    FILE_ROOT.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(24) + extensions[content_type]
    path = FILE_ROOT / key
    path.write_bytes(content)
    record = models.Report(patient_id=patient_id, appointment_id=appointment_id, uploaded_by_user_id=user.user_id,
                           document_name=Path(document_name).name[:255] or "Report", document_type=document_type[:80],
                           report_date=report_date or date.today(), file_storage_key=key)
    db.add(record)
    try:
        db.commit(); db.refresh(record)
    except Exception:
        db.rollback(); path.unlink(missing_ok=True); raise
    return record_dict(record)


@router.get("/reports/{report_id:int}/download")
def download_report(report_id: int, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    authorize_read("reports", user)
    query = db.query(models.Report).filter_by(report_id=report_id)
    report = query.first() if user.role == "ADMIN" else _scoped(query, "reports", user).first()
    if not report: raise HTTPException(404, "Report not found")
    key = report.file_storage_key
    if Path(key).name != key: raise HTTPException(404, "Report file not found")
    path = (FILE_ROOT / key).resolve()
    if path.parent != FILE_ROOT or not path.is_file(): raise HTTPException(404, "Report file not found")
    media = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".png": "image/png"}.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media, filename=report.document_name)


@router.get("/admin/dashboard")
def admin_dashboard(db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if user.role != "ADMIN": raise HTTPException(403, "Admin access required")
    counts = {name: db.scalar(select(func.count()).select_from(entity)) or 0 for name, (entity, _) in RESOURCES.items()}
    upcoming = db.scalars(select(models.Appointment).where(models.Appointment.scheduled_at >= datetime.now()).order_by(models.Appointment.scheduled_at).limit(10)).all()
    return {"counts": counts, "upcoming_appointments": [record_dict(row) for row in upcoming]}


@router.get("/doctor/dashboard")
def doctor_dashboard(db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if user.role != "DOCTOR": raise HTTPException(403, "Doctor access required")
    doctor = db.query(models.Doctor).filter_by(user_id=user.user_id).first()
    if not doctor: raise HTTPException(403, "No doctor profile is linked to this account")
    appointments = db.scalars(select(models.Appointment).where(models.Appointment.doctor_id == doctor.doctor_id, models.Appointment.scheduled_at >= datetime.now()).order_by(models.Appointment.scheduled_at).limit(20)).all()
    return {"doctor": doctor.doctor_id, "patient_count": db.scalar(select(func.count()).select_from(models.Patient).where(models.Patient.primary_doctor_id == doctor.doctor_id)), "appointments": [record_dict(x) for x in appointments]}


@router.get("/patient/dashboard")
def patient_dashboard(db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    if user.role != "PATIENT": raise HTTPException(403, "Patient access required")
    patient = db.query(models.Patient).filter_by(user_id=user.user_id).first()
    if not patient: raise HTTPException(403, "No patient profile is linked to this account")
    appointments = db.scalars(select(models.Appointment).where(models.Appointment.patient_id == patient.patient_id).order_by(models.Appointment.scheduled_at.desc()).limit(20)).all()
    reports = db.scalars(select(models.Report).where(models.Report.patient_id == patient.patient_id).order_by(models.Report.report_date.desc()).limit(20)).all()
    return {"patient": patient.patient_id, "appointments": [record_dict(x) for x in appointments], "reports": [record_dict(x) for x in reports]}
