from __future__ import annotations

import re
import threading
from datetime import date, datetime, time, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models

SLOT_MINUTES = 10
MAX_PER_HOUR = 6
ACTIVE_STATUSES = {"scheduled", "requested"}
UNAVAILABLE_LABELS = {"absent", "on leave", "unavailable", "off duty", "inactive"}
WEEKDAYS = {0, 1, 2, 3, 4}

_booking_lock = threading.Lock()


class SlotUnavailable(HTTPException):
    def __init__(self, message: str, alternatives: list[str] | None = None):
        super().__init__(status_code=409, detail={"message": message, "alternatives": alternatives or []})


def parse_availability(text: str | None) -> tuple[set[int], time, time] | None:
    raw = (text or "").strip()
    if not raw or raw.lower() in UNAVAILABLE_LABELS:
        return None
    days = set(WEEKDAYS)
    start, end = time(9, 0), time(17, 0)
    times = re.findall(r"(\d{1,2}:\d{2})", raw)
    if len(times) >= 2:
        start = _parse_clock(times[0])
        end = _parse_clock(times[1])
        if end <= start:
            return None
    lowered = raw.lower()
    if "weekend" in lowered:
        days = {5, 6}
    elif re.search(r"monday\s*[-to]+\s*sunday|daily|every day", lowered):
        days = set(range(7))
    elif re.search(r"monday\s*[-to]+\s*saturday", lowered):
        days = set(range(6))
    elif re.search(r"monday\s*[-to]+\s*friday|weekday", lowered):
        days = set(WEEKDAYS)
    return days, start, end


def _parse_clock(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour) % 24, int(minute) % 60)


def hour_window(when: datetime) -> tuple[datetime, datetime]:
    start = when.replace(minute=0, second=0, microsecond=0)
    return start, start + timedelta(hours=1)


def doctor_works_at(doctor: models.Doctor, when: datetime) -> bool:
    parsed = parse_availability(doctor.availability)
    if not parsed:
        return False
    days, start, end = parsed
    if when.weekday() not in days:
        return False
    clock = when.replace(second=0, microsecond=0).time()
    return start <= clock < end


def _active_in_hour(db: Session, doctor_id: int, hour_start: datetime, hour_end: datetime, *, lock: bool = False):
    query = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.scheduled_at >= hour_start,
        models.Appointment.scheduled_at < hour_end,
        models.Appointment.status.in_(tuple(ACTIVE_STATUSES)),
    )
    if lock:
        query = query.with_for_update()
    return query.order_by(models.Appointment.scheduled_at).all()


def remaining_capacity(db: Session, doctor_id: int, hour_start: datetime, hour_end: datetime, *, lock: bool = False) -> int:
    return max(0, MAX_PER_HOUR - len(_active_in_hour(db, doctor_id, hour_start, hour_end, lock=lock)))


def first_open_time(
    db: Session,
    doctor_id: int,
    hour_start: datetime,
    hour_end: datetime,
    preferred_time: datetime | None = None,
) -> datetime | None:
    taken = {row.scheduled_at.replace(second=0, microsecond=0) for row in _active_in_hour(db, doctor_id, hour_start, hour_end)}
    if preferred_time and hour_start <= preferred_time < hour_end:
        pref = preferred_time.replace(second=0, microsecond=0)
        if pref not in taken:
            return pref
    cursor = hour_start
    while cursor < hour_end:
        if cursor not in taken:
            return cursor
        cursor += timedelta(minutes=SLOT_MINUTES)
    return None


def department_doctors(db: Session, department_id: int) -> list[models.Doctor]:
    return db.query(models.Doctor).filter(models.Doctor.department_id == department_id).order_by(models.Doctor.doctor_id).all()


def alternative_slots(db: Session, doctors: list[models.Doctor], on_date: date, exclude_hour: datetime | None = None) -> list[str]:
    hours: dict[str, int] = {}
    for doctor in doctors:
        parsed = parse_availability(doctor.availability)
        if not parsed:
            continue
        days, start, end = parsed
        if on_date.weekday() not in days:
            continue
        cursor = datetime.combine(on_date, start)
        close = datetime.combine(on_date, end)
        while cursor < close:
            label = cursor.strftime("%H:%M")
            if exclude_hour is None or cursor != exclude_hour:
                remaining = remaining_capacity(db, doctor.doctor_id, cursor, cursor + timedelta(hours=1))
                hours[label] = hours.get(label, 0) + remaining
            cursor += timedelta(hours=1)
    return [label for label, remaining in sorted(hours.items()) if remaining > 0][:8]


def list_slots(db: Session, department_id: int, on_date: date) -> dict[str, Any]:
    doctors = department_doctors(db, department_id)
    if not doctors:
        raise HTTPException(404, "No doctors are configured for this department")
    hours: dict[str, int] = {}
    for doctor in doctors:
        parsed = parse_availability(doctor.availability)
        if not parsed:
            continue
        days, start, end = parsed
        if on_date.weekday() not in days:
            continue
        cursor = datetime.combine(on_date, start)
        close = datetime.combine(on_date, end)
        while cursor < close:
            label = cursor.strftime("%H:%M")
            hours[label] = hours.get(label, 0) + remaining_capacity(db, doctor.doctor_id, cursor, cursor + timedelta(hours=1))
            cursor += timedelta(hours=1)
    slots = [{"time": label, "remaining": remaining, "available": remaining > 0} for label, remaining in sorted(hours.items())]
    return {
        "department_id": department_id,
        "date": on_date.isoformat(),
        "slot_minutes": SLOT_MINUTES,
        "max_per_hour": MAX_PER_HOUR,
        "slots": slots,
    }


def require_bookable_patient(db: Session, patient_id: int) -> models.Patient:
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    if not patient.user_id:
        raise HTTPException(422, "Appointments can only be created for a patient with a linked PATIENT account")
    account = db.get(models.User, patient.user_id)
    if not account or account.role != "PATIENT" or not account.is_active:
        raise HTTPException(422, "The selected patient account is missing, inactive, or is not a PATIENT role")
    return patient


def book_appointment(
    db: Session,
    *,
    patient_id: int,
    scheduled_at: datetime,
    department_id: int | None = None,
    doctor_id: int | None = None,
    reason: str | None = None,
    notes: str | None = None,
    status: str | None = None,
) -> models.Appointment:
    if scheduled_at <= datetime.now():
        raise HTTPException(422, "Choose a date and time in the future")
    patient = require_bookable_patient(db, patient_id)
    hour_start, hour_end = hour_window(scheduled_at)

    preferred = db.get(models.Doctor, doctor_id) if doctor_id else None
    if doctor_id and not preferred:
        raise HTTPException(404, "Doctor not found")
    resolved_department = department_id or (preferred.department_id if preferred else None)
    if not resolved_department:
        raise HTTPException(422, "Select a department or a doctor so the appointment can be scheduled")
    doctors = department_doctors(db, resolved_department)
    if not doctors:
        raise HTTPException(404, "No doctors are configured for this department")
    if preferred and preferred.department_id != resolved_department:
        raise HTTPException(422, "The selected doctor does not belong to this department")

    preferred_id = preferred.doctor_id if preferred else None
    candidates = [doctor for doctor in doctors if doctor_works_at(doctor, hour_start)]
    if not candidates:
        alternatives = alternative_slots(db, doctors, hour_start.date(), exclude_hour=hour_start)
        raise SlotUnavailable(
            "No doctor is available in this department at the selected time. Choose another slot.",
            alternatives,
        )

    with _booking_lock:
        ranked = sorted(candidates, key=lambda doctor: doctor.doctor_id)
        db.query(models.Doctor).filter(models.Doctor.doctor_id.in_([doctor.doctor_id for doctor in ranked])).with_for_update().all()

        assigned: models.Doctor | None = None
        start_time: datetime | None = None
        ranked_by_capacity = sorted(
            ranked,
            key=lambda doctor: (
                0 if preferred_id == doctor.doctor_id else 1,
                -remaining_capacity(db, doctor.doctor_id, hour_start, hour_end),
                doctor.doctor_id,
            ),
        )
        for doctor in ranked_by_capacity:
            existing = _active_in_hour(db, doctor.doctor_id, hour_start, hour_end, lock=True)
            if len(existing) >= MAX_PER_HOUR:
                continue
            open_at = first_open_time(db, doctor.doctor_id, hour_start, hour_end, scheduled_at)
            if open_at is None:
                continue
            assigned = doctor
            start_time = open_at
            break
        if assigned is None or start_time is None:
            alternatives = alternative_slots(db, doctors, hour_start.date(), exclude_hour=hour_start)
            raise SlotUnavailable("This time slot is full. Please choose another available slot.", alternatives)

        overlapping = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient.patient_id,
            models.Appointment.status.in_(tuple(ACTIVE_STATUSES)),
            models.Appointment.scheduled_at < hour_end,
            models.Appointment.scheduled_at >= hour_start,
        ).first()
        if overlapping:
            raise HTTPException(409, "This patient already has an appointment during that hour")

        # Recheck availability when saving the appointment to prevent concurrent requests from overbooking a doctor
        final_active = _active_in_hour(db, assigned.doctor_id, hour_start, hour_end, lock=True)
        if len(final_active) >= MAX_PER_HOUR:
            alternatives = alternative_slots(db, doctors, hour_start.date(), exclude_hour=hour_start)
            raise SlotUnavailable("This time slot is full. Please choose another available slot.", alternatives)
        taken_times = {a.scheduled_at.replace(second=0, microsecond=0) for a in final_active}
        if start_time.replace(second=0, microsecond=0) in taken_times:
            open_at = first_open_time(db, assigned.doctor_id, hour_start, hour_end, scheduled_at)
            if open_at is None:
                alternatives = alternative_slots(db, doctors, hour_start.date(), exclude_hour=hour_start)
                raise SlotUnavailable("This time slot is full. Please choose another available slot.", alternatives)
            start_time = open_at

        allowed_status = (status or "scheduled").lower()
        if allowed_status not in {"scheduled", "requested"}:
            allowed_status = "scheduled"
        row = models.Appointment(
            patient_id=patient.patient_id,
            doctor_id=assigned.doctor_id,
            scheduled_at=start_time,
            reason=reason,
            notes=notes,
            status=allowed_status,
        )
        db.add(row)
        db.flush()
        return row
