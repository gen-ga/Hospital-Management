import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import Department, Doctor, Patient, SessionRecord, User
from ..schemas import DoctorAccountCreate, LoginRequest, PatientRegistration, StaffAccountCreate, UserRead
from ..services.security import hash_password, new_session_token, session_digest, session_expiry, verify_password

router = APIRouter(prefix="/api/auth", tags=["authentication"])
COOKIE_NAME = "hms_session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Authentication required")
    session = db.query(SessionRecord).filter_by(session_id=session_digest(token)).first()
    if not session or session.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        if session:
            db.delete(session); db.commit()
        raise HTTPException(401, "Session expired; please sign in again")
    user = db.query(User).filter_by(user_id=session.user_id, is_active=True).first()
    if not user:
        db.delete(session); db.commit()
        raise HTTPException(401, "Account is unavailable")
    return user


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    token = new_session_token()
    db.add(SessionRecord(session_id=session_digest(token), user_id=user.user_id, expires_at=session_expiry()))
    db.commit()
    response.set_cookie(COOKIE_NAME, token, httponly=True, secure=COOKIE_SECURE, samesite="lax", max_age=12 * 60 * 60, path="/")
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        session = db.query(SessionRecord).filter_by(session_id=session_digest(token)).first()
        if session:
            db.delete(session); db.commit()
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, secure=COOKIE_SECURE, samesite="lax")


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user


@router.post("/register", response_model=UserRead, status_code=201)
def register_patient(payload: PatientRegistration, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(email=email, password_hash=hash_password(payload.password), role="PATIENT", is_active=True,
                display_name=f"{payload.first_name.strip()} {payload.last_name.strip()}".strip())
    db.add(user)
    try:
        db.flush()
        db.add(Patient(
            user_id=user.user_id,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            phone=payload.phone,
            email=email,
            blood_group=payload.blood_group,
            address=payload.address,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
        ))
        db.commit(); db.refresh(user)
    except Exception:
        db.rollback(); raise
    return user


@router.post("/admin/users", response_model=UserRead, status_code=201)
def create_staff_account(payload: StaffAccountCreate, db: Session = Depends(get_db), admin: User = Depends(current_user)):
    if admin.role != "ADMIN":
        raise HTTPException(403, "Admin access required")
    email = payload.email.strip().lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists")
    profile = None
    if payload.profile_id is not None:
        profile_model = Doctor if payload.role == "DOCTOR" else Patient
        id_column = "doctor_id" if payload.role == "DOCTOR" else "patient_id"
        profile = db.query(profile_model).filter(getattr(profile_model, id_column) == payload.profile_id).with_for_update().first()
        if not profile:
            raise HTTPException(404, "Profile not found")
        if profile.user_id is not None:
            raise HTTPException(409, "That profile already has a linked account")
    user = User(email=email, password_hash=hash_password(payload.password), role=payload.role, is_active=True, display_name=payload.display_name.strip())
    db.add(user)
    db.flush()
    if profile:
        profile.user_id = user.user_id
    db.commit(); db.refresh(user)
    return user


@router.post("/admin/doctors", status_code=201)
def create_doctor_account(payload: DoctorAccountCreate, db: Session = Depends(get_db), admin: User = Depends(current_user)):
    if admin.role != "ADMIN":
        raise HTTPException(403, "Admin access required")
    email = payload.email.strip().lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists")
    if not db.query(Department).filter_by(department_id=payload.department_id).first():
        raise HTTPException(422, "Select a valid department")
    user = User(email=email, password_hash=hash_password(payload.password), role="DOCTOR", is_active=True,
                display_name=f"Dr. {payload.first_name.strip()} {payload.last_name.strip()}")
    db.add(user)
    db.flush()
    doctor = Doctor(
        user_id=user.user_id,
        first_name=payload.first_name.strip(), last_name=payload.last_name.strip(),
        department_id=payload.department_id, specialization=payload.specialization.strip(),
        availability=payload.availability.strip(), phone=payload.phone,
        years_experience=payload.years_experience, degree=payload.degree,
    )
    db.add(doctor)
    try:
        db.commit()
        db.refresh(doctor)
    except Exception:
        db.rollback()
        raise
    return {"doctor_id": doctor.doctor_id, "user_id": user.user_id, "email": user.email}
