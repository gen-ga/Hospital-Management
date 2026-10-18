-- Fresh Hospital Management System schema (MySQL 8+).
-- Select the intended, empty database before running this file.
-- This script creates tables only; it does not drop or replace existing objects.

CREATE TABLE departments (
    department_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (department_id),
    CONSTRAINT uq_departments_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    display_name VARCHAR(255) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_role CHECK (role IN ('ADMIN', 'DOCTOR', 'PATIENT'))
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE doctors (
    doctor_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NULL,
    department_id BIGINT UNSIGNED NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(120) NOT NULL,
    availability VARCHAR(120) NOT NULL DEFAULT 'Monday - Friday (09:00 - 17:00)',
    phone VARCHAR(32) NULL,
    years_experience SMALLINT UNSIGNED NULL,
    degree VARCHAR(120) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doctor_id),
    CONSTRAINT uq_doctors_user UNIQUE (user_id),
    INDEX ix_doctors_department (department_id),
    CONSTRAINT fk_doctors_user FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_doctors_department FOREIGN KEY (department_id) REFERENCES departments (department_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE patients (
    patient_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NULL,
    primary_doctor_id BIGINT UNSIGNED NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NULL,
    gender VARCHAR(24) NULL,
    phone VARCHAR(32) NULL,
    email VARCHAR(254) NULL,
    blood_group VARCHAR(8) NULL,
    address VARCHAR(500) NULL,
    emergency_contact_name VARCHAR(201) NULL,
    emergency_contact_phone VARCHAR(32) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (patient_id),
    CONSTRAINT uq_patients_user UNIQUE (user_id),
    INDEX ix_patients_name (last_name, first_name),
    CONSTRAINT fk_patients_user FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX ix_patients_primary_doctor (primary_doctor_id),
    CONSTRAINT fk_patients_primary_doctor FOREIGN KEY (primary_doctor_id) REFERENCES doctors (doctor_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE appointments (
    appointment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    patient_id BIGINT UNSIGNED NOT NULL,
    doctor_id BIGINT UNSIGNED NOT NULL,
    scheduled_at DATETIME NOT NULL,
    reason VARCHAR(500) NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'scheduled',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (appointment_id),
    INDEX ix_appointments_patient_time (patient_id, scheduled_at),
    INDEX ix_appointments_doctor_time (doctor_id, scheduled_at),
    CONSTRAINT chk_appointments_status CHECK (status IN ('requested', 'scheduled', 'completed', 'cancelled')),
    CONSTRAINT fk_appointments_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_appointments_doctor FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE operations (
    operation_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    patient_id BIGINT UNSIGNED NOT NULL,
    lead_doctor_id BIGINT UNSIGNED NOT NULL,
    procedure_name VARCHAR(200) NOT NULL,
    operation_at DATETIME NOT NULL,
    follow_up_at DATETIME NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'scheduled',
    report_summary TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (operation_id),
    INDEX ix_operations_patient_time (patient_id, operation_at),
    INDEX ix_operations_doctor_time (lead_doctor_id, operation_at),
    CONSTRAINT chk_operations_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    CONSTRAINT fk_operations_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_operations_lead_doctor FOREIGN KEY (lead_doctor_id) REFERENCES doctors (doctor_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rooms (
    room_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    room_number VARCHAR(32) NOT NULL,
    type VARCHAR(80) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'available',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id),
    CONSTRAINT uq_rooms_room_number UNIQUE (room_number),
    CONSTRAINT chk_rooms_status CHECK (status IN ('available', 'occupied', 'maintenance', 'inactive'))
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE room_visits (
    visit_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    patient_id BIGINT UNSIGNED NOT NULL,
    doctor_id BIGINT UNSIGNED NOT NULL,
    room_id BIGINT UNSIGNED NULL,
    scheduled_at DATETIME NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'scheduled',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (visit_id),
    INDEX ix_room_visits_patient_time (patient_id, scheduled_at),
    INDEX ix_room_visits_doctor_time (doctor_id, scheduled_at),
    INDEX ix_room_visits_room_time (room_id, scheduled_at),
    CONSTRAINT chk_room_visits_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    CONSTRAINT fk_room_visits_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_room_visits_doctor FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_room_visits_room FOREIGN KEY (room_id) REFERENCES rooms (room_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE medicines (
    medicine_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NULL,
    description TEXT NULL,
    manufacturer VARCHAR(160) NULL,
    stock_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    expiry_date DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (medicine_id),
    INDEX ix_medicines_name (name),
    INDEX ix_medicines_expiry (expiry_date),
    CONSTRAINT chk_medicines_unit_price CHECK (unit_price >= 0)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE prescriptions (
    prescription_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    patient_id BIGINT UNSIGNED NOT NULL,
    doctor_id BIGINT UNSIGNED NOT NULL,
    appointment_id BIGINT UNSIGNED NULL,
    prescribed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (prescription_id),
    INDEX ix_prescriptions_patient_time (patient_id, prescribed_at),
    INDEX ix_prescriptions_doctor_time (doctor_id, prescribed_at),
    INDEX ix_prescriptions_appointment (appointment_id),
    CONSTRAINT fk_prescriptions_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_prescriptions_doctor FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_prescriptions_appointment FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE prescription_items (
    item_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    prescription_id BIGINT UNSIGNED NOT NULL,
    medicine_id BIGINT UNSIGNED NOT NULL,
    dosage VARCHAR(120) NOT NULL,
    frequency VARCHAR(120) NOT NULL,
    instructions TEXT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id),
    INDEX ix_prescription_items_medicine (medicine_id),
    CONSTRAINT fk_prescription_items_prescription FOREIGN KEY (prescription_id) REFERENCES prescriptions (prescription_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_prescription_items_medicine FOREIGN KEY (medicine_id) REFERENCES medicines (medicine_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_prescription_item_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE reports (
    report_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    patient_id BIGINT UNSIGNED NOT NULL,
    appointment_id BIGINT UNSIGNED NULL,
    uploaded_by_user_id BIGINT UNSIGNED NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(80) NOT NULL,
    report_date DATE NOT NULL,
    file_storage_key VARCHAR(1024) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (report_id),
    INDEX ix_reports_patient_date (patient_id, report_date),
    INDEX ix_reports_appointment (appointment_id),
    INDEX ix_reports_uploaded_by (uploaded_by_user_id),
    CONSTRAINT fk_reports_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_reports_appointment FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_reports_uploaded_by_user FOREIGN KEY (uploaded_by_user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sessions (
    session_id CHAR(64) NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id),
    INDEX ix_sessions_user_expires (user_id, expires_at),
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
