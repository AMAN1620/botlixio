"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { LockIcon, EyeIcon, EyeOffIcon } from "@/components/icons";
import { AxiosError } from "axios";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="size-8 animate-spin rounded-full border-3 border-slate-200 border-t-brand" />}>
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  if (!token) {
    return (
      <div className="w-full max-w-[440px] text-center">
        <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-full bg-red-100">
          <svg className="size-8 text-red-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="m15 9-6 6" />
            <path d="m9 9 6 6" />
          </svg>
        </div>
        <h1 className="text-3xl font-black tracking-tight text-slate-900">
          Invalid Link
        </h1>
        <p className="mt-3 text-slate-600">
          This password reset link is invalid or has expired.
        </p>
        <Link
          href="/forgot-password"
          className="mt-8 inline-block rounded-lg bg-brand px-8 py-3 font-bold text-white hover:bg-brand/90"
        >
          Request New Link
        </Link>
      </div>
    );
  }

  if (success) {
    return (
      <div className="w-full max-w-[440px] text-center">
        <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-full bg-green-100">
          <svg className="size-8 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <h1 className="text-3xl font-black tracking-tight text-slate-900">
          Password Reset!
        </h1>
        <p className="mt-3 text-slate-600">
          Your password has been updated. You can now log in with your new password.
        </p>
        <Link
          href="/login"
          className="mt-8 inline-block rounded-lg bg-brand px-8 py-3 font-bold text-white hover:bg-brand/90"
        >
          Go to Login
        </Link>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await authApi.resetPassword({ token, new_password: password });
      setSuccess(true);
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(
          err.response?.data?.detail || "Reset failed. The link may have expired.",
        );
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-[440px]">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-black tracking-tight text-slate-900">
          Set new password
        </h1>
        <p className="mt-2 text-slate-500">
          Choose a strong password for your account.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            New Password
          </label>
          <div className="relative">
            <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              <LockIcon className="size-5" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={8}
              className="w-full rounded-xl border border-slate-200 bg-white py-3.5 pl-10 pr-12 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              {showPassword ? (
                <EyeOffIcon className="size-5" />
              ) : (
                <EyeIcon className="size-5" />
              )}
            </button>
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            Confirm Password
          </label>
          <div className="relative">
            <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              <LockIcon className="size-5" />
            </div>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={8}
              className="w-full rounded-xl border border-slate-200 bg-white py-3.5 pl-10 pr-4 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-xl bg-brand py-3 text-base font-bold text-white shadow-[0_10px_15px_-3px_rgba(37,19,236,0.2),0_4px_6px_-4px_rgba(37,19,236,0.2)] hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    </div>
  );
}
