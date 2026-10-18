import { Button, PasswordInput, TextInput } from "@mantine/core";
import { IconFirstAidKit } from "@tabler/icons-react";
import React, { useState } from "react";
import { useForm } from "@mantine/form";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { apiClient } from "../api";
import { useHospital } from "../context/HospitalContext";

const LoginPage = () => {
  const form = useForm({
    initialValues: { email: "", password: "" },
    validate: {
      email: (v) =>
        /^\S+@\S+\.\S+$/.test(v) ? null : "Enter a valid email address",
      password: (v) => (v.length < 1 ? "Enter your password" : null),
    },
  });
  const { user, setUser, loading } = useHospital();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (!loading && user)
    return <Navigate to={`/${user.role.toLowerCase()}/dashboard`} replace />;
  const handleSubmit = async (values: typeof form.values) => {
    setBusy(true);
    setError("");
    try {
      const loggedIn = await apiClient.login(values.email, values.password);
      setUser(loggedIn);
      navigate(`/${loggedIn.role.toLowerCase()}/dashboard`, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed. Try again.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center">
      <div className="py-3 text-primary-400 flex gap-1 items-center">
        <IconFirstAidKit size={40} stroke={2.5} />
        <span className="font-heading font-semibold text-3xl">HSM</span>
      </div>
      <div className="w-[450px] max-w-[calc(100vw-2rem)] backdrop-blur-md p-10 py-8 rounded-lg border border-gray-200 shadow-lg">
        <form
          onSubmit={form.onSubmit(handleSubmit)}
          className="flex flex-col gap-5"
        >
          <div className="self-center font-medium font-heading text-primary-400">
            Login
          </div>
          {error && (
            <p role="alert" className="text-sm text-red-700">
              {error}
            </p>
          )}
          <TextInput
            {...form.getInputProps("email")}
            size="md"
            placeholder="Email"
            autoComplete="username"
          />
          <PasswordInput
            {...form.getInputProps("password")}
            size="md"
            placeholder="Password"
            autoComplete="current-password"
          />
          <Button type="submit" color="#32b9a9" loading={busy}>
            Login
          </Button>
          <div className="text-sm self-center">
            Don't have an account?{" "}
            <Link to="/register" className="hover:underline">
              Register
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};
export default LoginPage;
