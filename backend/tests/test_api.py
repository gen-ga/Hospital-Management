import unittest
import tempfile
import threading
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.routers import records as records_router
from app.models import Appointment, Department, Doctor, Medicine, Operation, Patient, Prescription, PrescriptionItem, Report, Room, RoomVisit, SessionRecord, User
from app.services.security import hash_password, session_digest


@compiles(BigInteger, "sqlite")
def compile_bigint_as_integer(_type, _compiler, **_kw):
    return "INTEGER"


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(cls.engine, "connect")
        def enable_foreign_keys(dbapi_connection, _record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(cls.engine)
        cls.storage = tempfile.TemporaryDirectory()
        records_router.FILE_ROOT = Path(cls.storage.name)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        app.dependency_overrides[get_db] = cls.override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()
        cls.storage.cleanup()

    _db_mutex = threading.Lock()

    @classmethod
    def override_db(cls):
        with cls._db_mutex:
            db = cls.Session()
            try:
                yield db
            finally:
                db.close()

    def setUp(self):
        self.db = self.Session()
        self.admin = User(email="admin@example.test", password_hash=hash_password("test-password-admin"), role="ADMIN", is_active=True, display_name="Test Admin")
        self.patient_user = User(email="patient@example.test", password_hash=hash_password("test-password-patient"), role="PATIENT", is_active=True, display_name="Test Patient")
        self.other_user = User(email="other@example.test", password_hash=hash_password("test-password-other"), role="PATIENT", is_active=True, display_name="Other Patient")
        self.department = Department(name="Test Care", description="test")
        self.db.add_all([self.admin, self.patient_user, self.other_user, self.department]); self.db.flush()
        self.doctor = Doctor(user_id=None, department_id=self.department.department_id, first_name="Ari", last_name="Doctor", specialization="General", availability="Weekdays", phone=None, years_experience=2, degree="MD")
        self.db.add(self.doctor); self.db.flush()
        self.patient = Patient(user_id=self.patient_user.user_id, primary_doctor_id=self.doctor.doctor_id, first_name="Test", last_name="Patient", email=self.patient_user.email)
        self.other_patient = Patient(user_id=self.other_user.user_id, first_name="Other", last_name="Patient", email=self.other_user.email)
        self.unlinked_patient = Patient(first_name="Unlinked", last_name="Person")
        self.db.add_all([self.patient, self.other_patient, self.unlinked_patient]); self.db.commit()
        self.admin_id = self.admin.user_id
        self.patient_id = self.patient.patient_id
        self.other_patient_id = self.other_patient.patient_id
        self.unlinked_patient_id = self.unlinked_patient.patient_id
        self.doctor_id = self.doctor.doctor_id
        self.department_id = self.department.department_id
        self.admin_email = self.admin.email
        self.patient_email = self.patient_user.email
        self.db.close()
        self.client.cookies.clear()

    def tearDown(self):
        self.client.cookies.clear()
        db = self.Session()
        for model in (SessionRecord, Report, PrescriptionItem, Prescription, RoomVisit, Operation, Appointment, Patient, Doctor, Room, Medicine, Department, User):
            db.query(model).delete()
        db.commit(); db.close()

    def login(self, email, password="test-password-admin"):
        response = self.client.post("/api/auth/login", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.headers.get("set-cookie", "").lower().find("httponly") >= 0)

    def test_auth_session_expiration_and_logout(self):
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.login(self.admin_email)
        self.assertEqual(self.client.get("/api/auth/me").json()["role"], "ADMIN")
        token = self.client.cookies.get("hms_session")
        db = self.Session()
        session = db.query(SessionRecord).filter_by(session_id=session_digest(token)).one()
        session.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1); db.commit(); db.close()
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.login(self.admin_email)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_crud_relationships_dashboards_and_role_scope(self):
        self.login(self.admin_email)
        payloads = {
            "departments": {"name": "API Cardiology", "description": "test"},
            "doctors": {"department_id": self.department_id, "first_name": "New", "last_name": "Doctor", "specialization": "Cardiology", "availability": "Weekdays"},
            "patients": {"first_name": "New", "last_name": "Patient", "gender": "Other"},
            "appointments": {"patient_id": self.patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-04-01T09:00:00", "reason": "Review"},
            "operations": {"patient_id": self.patient_id, "lead_doctor_id": self.doctor_id, "procedure_name": "Test procedure", "operation_at": "2030-04-02T09:00:00"},
            "rooms": {"room_number": "API-101", "type": "General"},
            "room-visits": {"patient_id": self.patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-04-03T09:00:00"},
            "medicines": {"name": "API Medicine", "category": "Tablet", "stock_quantity": 4, "unit_price": "3.25"},
        }
        created = {}
        id_fields = {"departments": "department_id", "doctors": "doctor_id", "patients": "patient_id", "appointments": "appointment_id", "operations": "operation_id", "rooms": "room_id", "room-visits": "visit_id", "medicines": "medicine_id", "prescriptions": "prescription_id", "prescription-items": "item_id", "reports": "report_id"}
        for resource, payload in payloads.items():
            response = self.client.post(f"/api/{resource}", json=payload)
            self.assertEqual(response.status_code, 201, f"{resource}: {response.text}")
            created[resource] = response.json()
            record_id = created[resource][id_fields[resource]]
            self.assertEqual(self.client.get(f"/api/{resource}/{record_id}").status_code, 200)
        rx = self.client.post("/api/prescriptions", json={"patient_id": self.patient_id, "doctor_id": self.doctor_id, "appointment_id": created["appointments"]["appointment_id"]})
        self.assertEqual(rx.status_code, 201, rx.text); created["prescriptions"] = rx.json()
        item = self.client.post("/api/prescription-items", json={"prescription_id": rx.json()["prescription_id"], "medicine_id": created["medicines"]["medicine_id"], "dosage": "1 tablet", "frequency": "daily"})
        self.assertEqual(item.status_code, 201, item.text); created["prescription-items"] = item.json()
        report = self.client.post("/api/reports", json={"patient_id": self.patient_id, "appointment_id": created["appointments"]["appointment_id"], "document_name": "API report", "document_type": "Lab", "report_date": "2030-04-01", "file_storage_key": "test/api.pdf"})
        self.assertEqual(report.status_code, 201, report.text); created["reports"] = report.json()
        self.assertEqual(report.json()["uploaded_by_user_id"], self.admin_id)
        patched = self.client.patch(f"/api/medicines/{created['medicines']['medicine_id']}", json={"stock_quantity": 9})
        self.assertEqual(patched.status_code, 200, patched.text); self.assertEqual(patched.json()["stock_quantity"], 9)
        dash = self.client.get("/api/admin/dashboard")
        self.assertEqual(dash.status_code, 200, dash.text); self.assertGreaterEqual(dash.json()["counts"]["appointments"], 1)
        for resource in ("reports", "prescription-items", "prescriptions", "room-visits", "operations", "appointments", "medicines", "rooms", "patients", "doctors", "departments"):
            response = self.client.delete(f"/api/{resource}/{created[resource][id_fields[resource]]}")
            self.assertEqual(response.status_code, 204, f"{resource}: {response.text}")
        self.client.post("/api/auth/logout")
        self.login(self.patient_email, "test-password-patient")
        self.assertEqual(self.client.get("/api/admin/dashboard").status_code, 403)
        own_patients = self.client.get("/api/patients")
        self.assertEqual(own_patients.status_code, 200, own_patients.text)
        self.assertEqual([p["patient_id"] for p in own_patients.json()], [self.patient_id])

    def test_report_upload_access_download_and_delete(self):
        self.login(self.admin_email)
        uploaded = self.client.post("/api/reports/upload", params={"patient_id": self.patient_id, "document_name": "Test report.pdf", "document_type": "Lab report", "report_date": "2030-04-01"}, content=b"%PDF-1.4\nunit test", headers={"Content-Type": "application/pdf"})
        self.assertEqual(uploaded.status_code, 201, uploaded.text)
        report_id = uploaded.json()["report_id"]
        db = self.Session(); key = db.query(Report).filter_by(report_id=report_id).one().file_storage_key; db.close()
        downloaded = self.client.get(f"/api/reports/{report_id}/download")
        self.assertEqual(downloaded.status_code, 200, downloaded.text)
        self.assertEqual(downloaded.content, b"%PDF-1.4\nunit test")
        self.client.post("/api/auth/logout")
        self.login(self.patient_email, "test-password-patient")
        self.assertEqual(self.client.get(f"/api/reports/{report_id}/download").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/reports/{report_id}").status_code, 403)
        self.client.post("/api/auth/logout")
        self.login(self.admin_email)
        self.assertEqual(self.client.delete(f"/api/reports/{report_id}").status_code, 204)
        self.assertFalse((records_router.FILE_ROOT / key).exists())

    def test_staff_account_linking_and_role_dashboards(self):
        self.login(self.admin_email)
        appointment = self.client.post("/api/appointments", json={"patient_id": self.patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-04-01T09:00:00", "reason": "Follow-up"})
        self.assertEqual(appointment.status_code, 201, appointment.text)
        operation = self.client.post("/api/operations", json={"patient_id": self.patient_id, "lead_doctor_id": self.doctor_id, "procedure_name": "Test procedure", "operation_at": "2030-04-02T09:00:00"})
        self.assertEqual(operation.status_code, 201, operation.text)
        linked = self.client.post("/api/auth/admin/users", json={"email": "doctor@example.test", "password": "test-password-doctor", "role": "DOCTOR", "display_name": "Ari Doctor", "profile_id": self.doctor_id})
        self.assertEqual(linked.status_code, 201, linked.text)
        self.client.post("/api/auth/logout")
        self.login("doctor@example.test", "test-password-doctor")
        doctor_dashboard = self.client.get("/api/doctor/dashboard")
        self.assertEqual(doctor_dashboard.status_code, 200, doctor_dashboard.text)
        self.assertEqual(doctor_dashboard.json()["patient_count"], 1)
        self.assertEqual(len(doctor_dashboard.json()["appointments"]), 1)
        changed_operation = self.client.patch(f"/api/operations/{operation.json()['operation_id']}", json={"status": "in_progress"})
        self.assertEqual(changed_operation.status_code, 200, changed_operation.text)
        self.assertEqual(changed_operation.json()["status"], "in_progress")
        self.assertEqual(self.client.patch(f"/api/appointments/{appointment.json()['appointment_id']}", json={"patient_id": self.other_patient.patient_id}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/appointments/{appointment.json()['appointment_id']}", json={"notes": "Reviewed"}).status_code, 200)
        self.assertEqual(self.client.patch(f"/api/appointments/{appointment.json()['appointment_id']}", json={"status": "completed"}).json()["status"], "completed")
        doctor_patients = self.client.get("/api/patients")
        self.assertEqual([p["patient_id"] for p in doctor_patients.json()], [self.patient_id])
        self.assertEqual(self.client.get("/api/patient/dashboard").status_code, 403)
        self.client.post("/api/auth/logout")
        self.login(self.patient_email, "test-password-patient")
        patient_dashboard = self.client.get("/api/patient/dashboard")
        self.assertEqual(patient_dashboard.status_code, 200, patient_dashboard.text)
        self.assertEqual(self.client.get("/api/doctor/dashboard").status_code, 403)
        visible_doctors = self.client.get("/api/doctors")
        self.assertEqual(visible_doctors.status_code, 200, visible_doctors.text)
        self.assertTrue(any(doctor["doctor_id"] == self.doctor_id for doctor in visible_doctors.json()))
        own_patients = self.client.get("/api/patients")
        self.assertEqual([p["patient_id"] for p in own_patients.json()], [self.patient_id])

    def test_patient_can_cancel_only_own_upcoming_appointments(self):
        self.login(self.admin_email)
        appointment = self.client.post("/api/appointments", json={"patient_id": self.patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2099-04-01T09:00:00", "reason": "Follow-up"})
        other_appointment = self.client.post("/api/appointments", json={"patient_id": self.other_patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2099-04-02T09:00:00", "reason": "Review"})
        self.assertEqual(appointment.status_code, 201, appointment.text)
        self.assertEqual(other_appointment.status_code, 201, other_appointment.text)
        self.client.post("/api/auth/logout")
        self.login(self.patient_email, "test-password-patient")
        cancelled = self.client.patch(f"/api/appointments/{appointment.json()['appointment_id']}", json={"status": "cancelled"})
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        self.assertEqual(cancelled.json()["status"], "cancelled")
        self.assertEqual(self.client.patch(f"/api/appointments/{other_appointment.json()['appointment_id']}", json={"status": "cancelled"}).status_code, 404)

    def test_admin_creates_doctor_and_linked_login_together(self):
        self.login(self.admin_email)
        created = self.client.post("/api/auth/admin/doctors", json={
            "email": "new.doctor@example.test", "password": "secure-doctor-password",
            "first_name": "New", "last_name": "Doctor", "department_id": self.department_id,
            "specialization": "Cardiology", "availability": "Weekdays", "phone": "555-0100",
            "years_experience": 5, "degree": "MD",
        })
        self.assertEqual(created.status_code, 201, created.text)
        doctor = self.client.get(f"/api/doctors/{created.json()['doctor_id']}")
        self.assertEqual(doctor.status_code, 200, doctor.text)
        self.assertEqual(doctor.json()["email"], "new.doctor@example.test")
        db = self.Session()
        account = db.query(User).filter_by(email="new.doctor@example.test").one()
        self.assertNotEqual(account.password_hash, "secure-doctor-password")
        self.assertEqual(db.query(Doctor).filter_by(doctor_id=doctor.json()["doctor_id"]).one().user_id, account.user_id)
        db.close()

    def _add_patient(self, email):
        db = self.Session()
        account = User(email=email, password_hash=hash_password("test-password-patient"), role="PATIENT", is_active=True, display_name=email)
        db.add(account); db.flush()
        patient = Patient(user_id=account.user_id, first_name="Extra", last_name=email.split("@")[0], email=email)
        db.add(patient); db.commit()
        patient_id = patient.patient_id
        db.close()
        return patient_id

    def test_patient_books_available_slot_and_cannot_complete(self):
        self.login(self.patient_email, "test-password-patient")
        booked = self.client.post("/api/appointments", json={"department_id": self.department_id, "scheduled_at": "2030-04-01T09:00:00", "reason": "Checkup"})
        self.assertEqual(booked.status_code, 201, booked.text)
        self.assertEqual(booked.json()["doctor_id"], self.doctor_id)
        self.assertEqual(booked.json()["patient_id"], self.patient_id)
        appointment_id = booked.json()["appointment_id"]
        self.assertEqual(self.client.patch(f"/api/appointments/{appointment_id}", json={"status": "completed"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/appointments/{appointment_id}", json={"status": "due"}).status_code, 403)
        cancelled = self.client.patch(f"/api/appointments/{appointment_id}", json={"status": "cancelled"})
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        self.assertEqual(cancelled.json()["status"], "cancelled")

    def test_admin_cannot_book_unlinked_or_non_patient_account(self):
        self.login(self.admin_email)
        unlinked = self.client.post("/api/appointments", json={"patient_id": self.unlinked_patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-04-01T09:00:00"})
        self.assertEqual(unlinked.status_code, 422, unlinked.text)
        db = self.Session()
        other = db.query(User).filter_by(email="other@example.test").one()
        other.role = "ADMIN"
        db.commit(); db.close()
        not_patient = self.client.post("/api/appointments", json={"patient_id": self.other_patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-04-01T10:00:00"})
        self.assertEqual(not_patient.status_code, 422, not_patient.text)

    def test_slot_capacity_alternate_doctor_and_admin_same_rules(self):
        self.login(self.admin_email)
        second = self.client.post("/api/doctors", json={"department_id": self.department_id, "first_name": "Bea", "last_name": "Doctor", "specialization": "General", "availability": "Weekdays"})
        self.assertEqual(second.status_code, 201, second.text)
        second_id = second.json()["doctor_id"]
        patient_ids = [self.patient_id, self.other_patient_id] + [self._add_patient(f"p{i}@example.test") for i in range(11)]
        for patient_id in patient_ids[:6]:
            response = self.client.post("/api/appointments", json={"patient_id": patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-04-08T09:00:00", "reason": "Review"})
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(response.json()["doctor_id"], self.doctor_id)
        overflow = self.client.post("/api/appointments", json={"patient_id": patient_ids[6], "doctor_id": self.doctor_id, "scheduled_at": "2030-04-08T09:00:00", "reason": "Overflow"})
        self.assertEqual(overflow.status_code, 201, overflow.text)
        self.assertEqual(overflow.json()["doctor_id"], second_id)
        for patient_id in patient_ids[7:12]:
            response = self.client.post("/api/appointments", json={"patient_id": patient_id, "department_id": self.department_id, "scheduled_at": "2030-04-08T09:00:00", "reason": "Fill"})
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(response.json()["doctor_id"], second_id)
        blocked_id = self._add_patient("blocked@example.test")
        self.client.post("/api/auth/logout")
        self.login("blocked@example.test", "test-password-patient")
        both_full = self.client.post("/api/appointments", json={"department_id": self.department_id, "scheduled_at": "2030-04-08T09:00:00", "reason": "Late"})
        self.assertEqual(both_full.status_code, 409, both_full.text)
        detail = both_full.json()["detail"]
        self.assertIn("full", detail["message"].lower() if isinstance(detail, dict) else str(detail).lower())
        if isinstance(detail, dict):
            self.assertTrue(detail.get("alternatives"))
        self.client.post("/api/auth/logout")
        self.login(self.admin_email)
        admin_same = self.client.post("/api/appointments", json={"patient_id": blocked_id, "department_id": self.department_id, "scheduled_at": "2030-04-08T09:00:00"})
        self.assertEqual(admin_same.status_code, 409, admin_same.text)

    def test_doctor_status_permissions_and_prescriptions_leave_inventory(self):
        self.login(self.admin_email)
        appointment = self.client.post("/api/appointments", json={"patient_id": self.patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-04-01T10:00:00", "reason": "Review"})
        medicine = self.client.post("/api/medicines", json={"name": "Amoxicillin", "category": "Antibiotic", "stock_quantity": 20, "unit_price": "1.50"})
        second_med = self.client.post("/api/medicines", json={"name": "Ibuprofen", "category": "Pain", "stock_quantity": 11, "unit_price": "0.80"})
        linked = self.client.post("/api/auth/admin/users", json={"email": "doctor@example.test", "password": "test-password-doctor", "role": "DOCTOR", "display_name": "Ari Doctor", "profile_id": self.doctor_id})
        self.assertEqual(appointment.status_code, 201, appointment.text)
        self.assertEqual(linked.status_code, 201, linked.text)
        self.client.post("/api/auth/logout")
        self.login("doctor@example.test", "test-password-doctor")
        own_id = appointment.json()["appointment_id"]
        self.assertEqual(self.client.patch(f"/api/appointments/{own_id}", json={"status": "cancelled"}).status_code, 403)
        due = self.client.patch(f"/api/appointments/{own_id}", json={"status": "due"})
        self.assertEqual(due.status_code, 200, due.text)
        self.assertEqual(due.json()["status"], "requested")
        completed = self.client.patch(f"/api/appointments/{own_id}", json={"status": "completed"})
        self.assertEqual(completed.status_code, 200, completed.text)
        prescribed = self.client.post("/api/prescriptions", json={
            "appointment_id": own_id,
            "items": [
                {"medicine_id": medicine.json()["medicine_id"], "dosage": "500mg", "frequency": "twice daily", "duration": "7"},
                {"medicine_id": second_med.json()["medicine_id"], "dosage": "200mg", "frequency": "as needed", "duration": "5"},
            ],
        })
        self.assertEqual(prescribed.status_code, 201, prescribed.text)
        self.client.post("/api/auth/logout")
        self.login(self.admin_email)
        items = self.client.get("/api/prescription-items")
        self.assertEqual(items.status_code, 200, items.text)
        self.assertEqual(len(items.json()), 2)
        stock = self.client.get(f"/api/medicines/{medicine.json()['medicine_id']}")
        self.assertEqual(stock.json()["stock_quantity"], 20)
        other_stock = self.client.get(f"/api/medicines/{second_med.json()['medicine_id']}")
        self.assertEqual(other_stock.json()["stock_quantity"], 11)

    def test_concurrent_bookings_cannot_exceed_capacity(self):
        self.login(self.admin_email)
        patient_ids = [self._add_patient(f"concurrent_{i}@example.test") for i in range(10)]
        target_time = "2030-05-01T09:00:00"

        # Share cookie across test client calls
        token = self.client.cookies.get("hms_session")
        cookies = {"hms_session": token}

        results = []
        def book(pid):
            client = TestClient(app, cookies=cookies)
            return client.post("/api/appointments", json={
                "patient_id": pid,
                "department_id": self.department_id,
                "scheduled_at": target_time,
                "reason": "Concurrent load test",
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(book, pid) for pid in patient_ids]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        successes = [r for r in results if r.status_code == 201]
        conflicts = [r for r in results if r.status_code == 409]

        self.assertEqual(len(successes), 6)
        self.assertEqual(len(conflicts), 4)

        db = self.Session()
        hour_start = datetime(2030, 5, 1, 9, 0)
        hour_end = datetime(2030, 5, 1, 10, 0)
        appts = db.query(Appointment).filter(
            Appointment.doctor_id == self.doctor_id,
            Appointment.scheduled_at >= hour_start,
            Appointment.scheduled_at < hour_end,
        ).order_by(Appointment.scheduled_at).all()
        self.assertEqual(len(appts), 6)

        # Ensure all 6 appointments have distinct 10-minute slots
        times = [a.scheduled_at for a in appts]
        self.assertEqual(len(set(times)), 6)
        db.close()

    def test_doctor_cannot_modify_or_prescribe_cancelled_appointment(self):
        self.login(self.admin_email)
        med = self.client.post("/api/medicines", json={"name": "Paracetamol", "category": "Pain", "stock_quantity": 50, "unit_price": "0.50"})
        self.assertEqual(med.status_code, 201, med.text)
        appt = self.client.post("/api/appointments", json={"patient_id": self.patient_id, "doctor_id": self.doctor_id, "scheduled_at": "2030-06-03T09:00:00", "reason": "Test"})
        self.assertEqual(appt.status_code, 201, appt.text)
        appt_id = appt.json()["appointment_id"]
        linked = self.client.post("/api/auth/admin/users", json={"email": "doc_cancel@example.test", "password": "test-password-doctor", "role": "DOCTOR", "display_name": "Dr Ari", "profile_id": self.doctor_id})
        self.assertEqual(linked.status_code, 201, linked.text)

        # Patient cancels their appointment
        self.client.post("/api/auth/logout")
        self.login(self.patient_email, "test-password-patient")
        cancelled = self.client.patch(f"/api/appointments/{appt_id}", json={"status": "cancelled"})
        self.assertEqual(cancelled.status_code, 200, cancelled.text)

        # Doctor logs in and attempts to modify or prescribe for the cancelled appointment
        self.client.post("/api/auth/logout")
        self.login("doc_cancel@example.test", "test-password-doctor")
        cant_complete = self.client.patch(f"/api/appointments/{appt_id}", json={"status": "completed"})
        self.assertEqual(cant_complete.status_code, 409, cant_complete.text)
        cant_prescribe = self.client.post("/api/prescriptions", json={
            "appointment_id": appt_id,
            "items": [{"medicine_id": med.json()["medicine_id"], "dosage": "500mg", "frequency": "daily"}],
        })
        self.assertEqual(cant_prescribe.status_code, 409, cant_prescribe.text)

    def test_patient_registration_with_all_details(self):
        payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.test",
            "password": "secure-patient-password-123",
            "date_of_birth": "1995-08-20",
            "gender": "Female",
            "phone": "555-0199",
            "blood_group": "O+",
            "address": "456 Health Ave, Care City",
            "emergency_contact_name": "John Doe",
            "emergency_contact_phone": "555-0188",
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201, res.text)
        data = res.json()
        self.assertEqual(data["email"], "jane.doe@example.test")
        self.assertEqual(data["role"], "PATIENT")

        db = self.Session()
        patient = db.query(Patient).filter_by(email="jane.doe@example.test").first()
        self.assertIsNotNone(patient)
        self.assertEqual(patient.first_name, "Jane")
        self.assertEqual(patient.last_name, "Doe")
        self.assertEqual(str(patient.date_of_birth), "1995-08-20")
        self.assertEqual(patient.gender, "Female")
        self.assertEqual(patient.phone, "555-0199")
        self.assertEqual(patient.blood_group, "O+")
        self.assertEqual(patient.address, "456 Health Ave, Care City")
        self.assertEqual(patient.emergency_contact_name, "John Doe")
        self.assertEqual(patient.emergency_contact_phone, "555-0188")
        self.assertEqual(patient.user_id, data["user_id"])
        db.close()

        # Verify the new patient can log in and view their profile
        self.login("jane.doe@example.test", "secure-patient-password-123")
        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["role"], "PATIENT")


if __name__ == "__main__":
    unittest.main()
