"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { authApi } from "@/lib/api";
import { GoogleIcon, GitHubIcon, MailIcon, LockIcon } from "@/components/icons";
import { AxiosError } from "axios";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof AxiosError) {
        const detail = err.response?.data?.detail;
        if (err.response?.status === 401) {
          setError("Invalid email or password.");
        } else if (err.response?.status === 403) {
          setError("Your account has been deactivated.");
        } else {
          setError(
            typeof detail === "string" ? detail : "Login failed. Please try again.",
          );
        }
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-[440px]">
      {/* Heading */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-black tracking-tight text-slate-900">
          Welcome back
        </h1>
        <p className="mt-2 text-slate-500">
          Enter your details to access your account
        </p>
      </div>

      {/* Social login */}
      <div className="mb-4 grid grid-cols-2 gap-3">
        <a
          href={authApi.googleAuthUrl()}
          className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50"
        >
          <GoogleIcon className="size-5" />
          Google
        </a>
        <button
          disabled
          className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 opacity-50 cursor-not-allowed"
        >
          <GitHubIcon className="size-5" />
          GitHub
        </button>
      </div>

      {/* Divider */}
      <div className="relative my-4 flex items-center justify-center py-4">
        <div className="absolute inset-x-0 top-1/2 h-px bg-slate-200" />
        <span className="relative bg-page-bg px-2 text-xs font-medium uppercase text-slate-500">
          Or continue with email
        </span>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {/* Email */}
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            Email address
          </label>
          <div className="relative">
            <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              <MailIcon className="size-5" />
            </div>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              required
              className="w-full rounded-xl border border-slate-200 bg-white py-3.5 pl-10 pr-4 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none"
            />
          </div>
        </div>

        {/* Password */}
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-700">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-sm font-semibold text-brand hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              <LockIcon className="size-5" />
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full rounded-xl border border-slate-200 bg-white py-3.5 pl-10 pr-4 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none"
            />
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-xl bg-brand py-3 text-base font-bold text-white shadow-[0_10px_15px_-3px_rgba(37,19,236,0.2),0_4px_6px_-4px_rgba(37,19,236,0.2)] hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Logging in..." : "Log in"}
        </button>
      </form>

      {/* Sign up link */}
      <p className="mt-4 text-center text-sm text-slate-500">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-bold text-brand hover:underline">
          Sign Up
        </Link>
      </p>
    </div>
  );
}
