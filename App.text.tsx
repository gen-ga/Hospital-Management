import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

const user = { user_id: 21, email: 'admin@example.test', role: 'ADMIN', display_name: 'Test Admin', is_active: true };
const response = (body: unknown, status = 200) => ({ ok: status >= 200 && status < 300, status, headers: new Headers(), json: async () => body }) as Response;
const setUrl = (url: string) => window.history.replaceState({}, '', url);

beforeEach(() => { jest.resetAllMocks(); setUrl('/'); global.fetch = jest.fn(); });

test('requires a session before showing protected workspaces', async () => {
  (global.fetch as jest.Mock).mockResolvedValue(response({ detail: 'Authentication required' }, 401));
  render(<App />);
  expect(await screen.findByPlaceholderText('Email')).toBeInTheDocument();
  expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/auth/me', expect.objectContaining({ credentials: 'include' }));
});

test('logs in and opens the role returned by the API', async () => {
  setUrl('/login');
  (global.fetch as jest.Mock)
    .mockResolvedValueOnce(response({ detail: 'Authentication required' }, 401))
    .mockResolvedValueOnce(response(user))
    .mockImplementation(async (input: RequestInfo | URL) => response(String(input).includes('/api/') ? [] : {}));
  render(<App />);
  fireEvent.change(await screen.findByPlaceholderText('Email'), { target: { value: user.email } });
  fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'test-password-admin' } });
  fireEvent.click(screen.getByRole('button', { name: 'Login' }));
  expect(await screen.findByRole('heading', { name: /welcome, test admin/i })).toBeInTheDocument();
  expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/auth/login', expect.objectContaining({ method: 'POST', credentials: 'include' }));
  expect(screen.queryByRole('combobox', { name: 'Switch role' })).not.toBeInTheDocument();
});

test('public registration only creates a patient account', async () => {
  setUrl('/register');
  (global.fetch as jest.Mock).mockResolvedValue(response({ detail: 'Authentication required' }, 401));
  render(<App />);
  expect(await screen.findByText('Patient registration')).toBeInTheDocument();
  expect(screen.queryByText('Admin')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Create patient account' })).toBeInTheDocument();
});

test('sign out invalidates the API session', async () => {
  setUrl('/admin/dashboard');
  (global.fetch as jest.Mock)
    .mockResolvedValueOnce(response(user))
    .mockImplementation(async (input: RequestInfo | URL) => String(input).includes('/api/auth/logout') ? response({}, 204) : response([]));
  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: /sign out/i }));
  await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/auth/logout', expect.objectContaining({ method: 'POST', credentials: 'include' })));
  expect(await screen.findByPlaceholderText('Email')).toBeInTheDocument();
});
