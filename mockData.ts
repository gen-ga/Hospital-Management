// Frontend view models for records returned by the FastAPI service.
// This module contains type definitions only; application data comes from the API.
export type Role = 'admin' | 'doctor' | 'patient';
export type Availability = string;
export type AppointmentStatus = 'Due' | 'Scheduled' | 'Completed' | 'Cancelled';

export interface Patient {
  id: string;
  name: string;
  gender: string;
  age: number;
  phone: string;
  email: string;
  doctor: string;
  concern: string;
  lastVisit: string;
  nextAppointment: string;
  bloodGroup: string;
  emergencyContact: string;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  address: string;
  dateOfBirth?: string;
}

export interface Doctor {
  id: string;
  userId?: number;
  name: string;
  department: string;
  specialization: string;
  availability: Availability;
  phone: string;
  email: string;
  experience: number;
  degree: string;
}

export interface Appointment {
  id: string;
  patient: string;
  doctor: string;
  gender: string;
  date: string;
  time: string;
  disease: string;
  reason: string;
  status: AppointmentStatus;
  rawStatus?: string;
  department?: string;
}

export interface Operation {
  id: string;
  patient: string;
  doctor: string;
  operationDate: string;
  followUp: string;
  disease: string;
  status: string;
  rawStatus?: string;
  report: string;
}

export interface Medicine {
  id: string;
  name: string;
  category: string;
  stock: number;
  price: number;
  expiry: string;
  company: string;
}

export interface Report {
  id: string;
  name: string;
  type: string;
  date: string;
  uploadedBy: string;
  patient: string;
}

export interface RoomVisit {
  id: string;
  patient: string;
  doctor: string;
  room: string;
  date: string;
  time: string;
  status: string;
}
