from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=256)


class PatientRegistration(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=256)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    blood_group: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_empty_date(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("gender", "phone", "blood_group", "address", "emergency_contact_name", "emergency_contact_phone", mode="before")
    @classmethod
    def parse_empty_str(cls, v):
        if isinstance(v, str):
            trimmed = v.strip()
            return trimmed if trimmed else None
        return v


class StaffAccountCreate(BaseModel):
    email: str
    password: str = Field(min_length=12, max_length=256)
    role: Literal["DOCTOR", "PATIENT"]
    display_name: str = Field(min_length=1, max_length=255)
    profile_id: int | None = None


class DoctorAccountCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=256)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    department_id: int
    specialization: str = Field(min_length=1, max_length=120)
    availability: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    years_experience: int | None = Field(default=None, ge=0)
    degree: str | None = Field(default=None, max_length=120)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    email: str
    role: str
    display_name: str | None = None
    is_active: bool
    created_at: datetime | None = None


class DepartmentPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class AppointmentPayload(BaseModel):
    patient_id: int | None = None
    department_id: int | None = None
    doctor_id: int | None = None
    scheduled_at: datetime
    reason: str | None = None
    status: str = "scheduled"
    notes: str | None = None


class MedicinePayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str | None = None
    description: str | None = None
    manufacturer: str | None = None
    stock_quantity: int = Field(ge=0, default=0)
    unit_price: Decimal = Field(ge=0, default=0)
    expiry_date: date | None = None
