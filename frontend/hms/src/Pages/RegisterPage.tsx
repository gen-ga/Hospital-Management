import { Button, NativeSelect, PasswordInput, TextInput, Textarea } from '@mantine/core';
import { IconFirstAidKit, IconHeartbeat, IconPhoneCall, IconUser } from '@tabler/icons-react';
import React, { useState } from 'react';
import { useForm } from '@mantine/form';
import { Link, useNavigate } from 'react-router-dom';
import { apiClient } from '../api';

const RegisterPage = () => {
  const form = useForm({
    initialValues: {
      first_name: '',
      last_name: '',
      email: '',
      password: '',
      confirmPassword: '',
      date_of_birth: '',
      gender: '',
      phone: '',
      blood_group: '',
      address: '',
      emergency_contact_name: '',
      emergency_contact_phone: '',
    },
    validate: {
      first_name: (v) => (v.trim() ? null : 'Enter your first name'),
      last_name: (v) => (v.trim() ? null : 'Enter your last name'),
      email: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : 'Enter a valid email address'),
      password: (v) => (v.length < 10 ? 'Use at least 10 characters' : null),
      confirmPassword: (v, values) => (v === values.password ? null : "Passwords don't match"),
    },
  });

  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async ({ confirmPassword, ...payload }: typeof form.values) => {
    void confirmPassword;
    setBusy(true);
    setError('');
    const cleanPayload: Record<string, unknown> = {
      ...payload,
      date_of_birth: payload.date_of_birth || null,
      gender: payload.gender || null,
      phone: payload.phone || null,
      blood_group: payload.blood_group || null,
      address: payload.address || null,
      emergency_contact_name: payload.emergency_contact_name || null,
      emergency_contact_phone: payload.emergency_contact_phone || null,
    };
    try {
      await apiClient.register(cleanPayload);
      navigate('/login', {
        replace: true,
        state: { message: 'Account created successfully! Sign in to continue.' },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Registration failed. Try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen w-screen py-10 px-4 flex flex-col items-center justify-center bg-gray-50/50">
      <div className="py-3 text-primary-400 flex gap-1 items-center">
        <IconFirstAidKit size={40} stroke={2.5} />
        <span className="font-heading font-semibold text-3xl">HSM</span>
      </div>
      <div className="w-[620px] max-w-full backdrop-blur-md p-6 sm:p-10 rounded-xl border border-gray-200 bg-white shadow-xl">
        <form onSubmit={form.onSubmit(submit)} className="flex flex-col gap-6">
          <div className="text-center">
            <h1 className="font-medium font-heading text-2xl text-primary-400">Patient Registration</h1>
            <p className="text-sm text-gray-600 mt-1">
              Create your patient account and complete your healthcare profile.
            </p>
          </div>

          {error && (
            <div role="alert" className="p-3 text-sm rounded bg-red-50 text-red-700 border border-red-200">
              {error}
            </div>
          )}

          {/* Section 1: Account Credentials */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
              <IconUser size={15} />
              <span>Account Credentials</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <TextInput
                required
                label="First name"
                placeholder="First name"
                autoComplete="given-name"
                {...form.getInputProps('first_name')}
              />
              <TextInput
                required
                label="Last name"
                placeholder="Last name"
                autoComplete="family-name"
                {...form.getInputProps('last_name')}
              />
            </div>
            <TextInput
              required
              label="Email address"
              placeholder="name@example.com"
              autoComplete="email"
              {...form.getInputProps('email')}
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <PasswordInput
                required
                label="Password"
                placeholder="10+ characters"
                autoComplete="new-password"
                {...form.getInputProps('password')}
              />
              <PasswordInput
                required
                label="Confirm password"
                placeholder="Repeat password"
                autoComplete="new-password"
                {...form.getInputProps('confirmPassword')}
              />
            </div>
          </div>

          {/* Section 2: Personal & Medical Information */}
          <div className="flex flex-col gap-3 pt-2 border-t border-gray-100">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
              <IconHeartbeat size={15} />
              <span>Personal & Medical Details</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <TextInput
                type="date"
                label="Date of birth"
                placeholder="YYYY-MM-DD"
                {...form.getInputProps('date_of_birth')}
              />
              <NativeSelect
                label="Gender"
                data={[
                  { value: '', label: 'Select gender' },
                  { value: 'Female', label: 'Female' },
                  { value: 'Male', label: 'Male' },
                  { value: 'Other', label: 'Other' },
                ]}
                {...form.getInputProps('gender')}
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <TextInput
                type="tel"
                label="Mobile number"
                placeholder="+1 555-0199"
                autoComplete="tel"
                {...form.getInputProps('phone')}
              />
              <NativeSelect
                label="Blood group"
                data={[
                  { value: '', label: 'Select blood group' },
                  { value: 'A+', label: 'A+' },
                  { value: 'A-', label: 'A-' },
                  { value: 'B+', label: 'B+' },
                  { value: 'B-', label: 'B-' },
                  { value: 'AB+', label: 'AB+' },
                  { value: 'AB-', label: 'AB-' },
                  { value: 'O+', label: 'O+' },
                  { value: 'O-', label: 'O-' },
                ]}
                {...form.getInputProps('blood_group')}
              />
            </div>
            <Textarea
              label="Address"
              placeholder="Residential address"
              autosize
              minRows={2}
              maxRows={4}
              {...form.getInputProps('address')}
            />
          </div>

          {/* Section 3: Emergency Contact */}
          <div className="flex flex-col gap-3 pt-2 border-t border-gray-100">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
              <IconPhoneCall size={15} />
              <span>Emergency Contact</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <TextInput
                label="Contact name"
                placeholder="Full name"
                {...form.getInputProps('emergency_contact_name')}
              />
              <TextInput
                type="tel"
                label="Contact number"
                placeholder="Phone number"
                {...form.getInputProps('emergency_contact_phone')}
              />
            </div>
          </div>

          <Button type="submit" color="#32b9a9" size="md" loading={busy} className="mt-2">
            Complete Registration
          </Button>

          <div className="text-sm self-center text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-500 font-medium hover:underline">
              Login
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterPage;
