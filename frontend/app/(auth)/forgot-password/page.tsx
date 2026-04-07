"use client";

import { useState } from "react";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { MailIcon } from "@/components/icons";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await authApi.forgotPassword(email);
    } catch {
      // Backend always returns success to prevent email enumeration
    } finally {
      setIsSubmitting(false);
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <div className="w-full max-w-[440px] text-center">
        <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-full bg-brand-light">
          <MailIcon className="size-8 text-brand" />
        </div>
        <h1 className="text-3xl font-black tracking-tight text-slate-900">
          Check your email
        </h1>
        <p className="mt-3 text-slate-600">
          If an account exists for <strong>{email}</strong>, we&apos;ve sent a
          password reset link. The link expires in 1 hour.
        </p>
        <Link
          href="/login"
          className="mt-8 inline-block rounded-lg border border-slate-200 bg-white px-8 py-3 font-bold text-slate-900 hover:bg-slate-50"
        >
          Back to Login
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[440px]">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-black tracking-tight text-slate-900">
          Forgot password?
        </h1>
        <p className="mt-2 text-slate-500">
          No worries, we&apos;ll send you a reset link.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
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

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-xl bg-brand py-3 text-base font-bold text-white shadow-[0_10px_15px_-3px_rgba(37,19,236,0.2),0_4px_6px_-4px_rgba(37,19,236,0.2)] hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Sending..." : "Send Reset Link"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        Remember your password?{" "}
        <Link href="/login" className="font-bold text-brand hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
