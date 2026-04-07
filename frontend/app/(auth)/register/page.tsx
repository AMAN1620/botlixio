"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { authApi } from "@/lib/api";
import {
  GoogleIcon,
  GitHubIcon,
  EyeIcon,
  EyeOffIcon,
  InfoIcon,
  ArrowRightIcon,
} from "@/components/icons";
import { AxiosError } from "axios";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuthStore();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (fullName.trim().length === 0) {
      setError("Full name is required.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register(email, password, fullName);
      setSuccess(true);
    } catch (err) {
      if (err instanceof AxiosError) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Registration failed. Please try again.");
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="w-full max-w-[480px] text-center">
        <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-full bg-green-100">
          <svg className="size-8 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <h1 className="text-3xl font-black tracking-tight text-slate-900">
          Check your email
        </h1>
        <p className="mt-3 text-slate-600">
          We&apos;ve sent a verification link to <strong>{email}</strong>.
          Click the link to verify your account, then log in.
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

  return (
    <div className="w-full max-w-[480px]">
      {/* Heading */}
      <div className="mb-8">
        <h1 className="text-4xl font-black tracking-tight text-slate-900">
          Create your account
        </h1>
        <p className="mt-2 text-slate-600">
          Join Botlixio to start your journey and streamline your workflow.
        </p>
      </div>

      {/* Social login */}
      <div className="mb-8 grid grid-cols-2 gap-3">
        <a
          href={authApi.googleAuthUrl()}
          className="flex items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3.5 font-semibold text-slate-900 hover:bg-slate-50"
        >
          <GoogleIcon className="size-5" />
          Google
        </a>
        <button
          disabled
          className="flex items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3.5 font-semibold text-slate-900 opacity-50 cursor-not-allowed"
        >
          <GitHubIcon className="size-4" />
          GitHub
        </button>
      </div>

      {/* Divider */}
      <div className="mb-8 flex items-center gap-4">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-medium uppercase tracking-widest text-slate-400">
          or sign up with email
        </span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {/* Full Name */}
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            Full Name
          </label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="John Doe"
            required
            className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3.5 text-base text-slate-900 placeholder:text-gray-400 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none"
          />
        </div>

        {/* Email */}
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            Email Address
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="john@example.com"
            required
            className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3.5 text-base text-slate-900 placeholder:text-gray-400 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none"
          />
        </div>

        {/* Password */}
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700">
            Password
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={8}
              className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3.5 pr-12 text-base text-slate-900 placeholder:text-gray-400 focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none"
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
          <div className="mt-1.5 flex items-center gap-2">
            <InfoIcon className="size-2.5 text-slate-500" />
            <span className="text-xs text-slate-500">
              Must be at least 8 characters with a number and symbol.
            </span>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex items-center justify-center gap-2 rounded-lg bg-brand py-3.5 text-base font-bold text-white shadow-[0_10px_15px_-3px_rgba(37,19,236,0.2),0_4px_6px_-4px_rgba(37,19,236,0.2)] hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Creating account..." : "Create Account"}
          {!isSubmitting && <ArrowRightIcon className="size-3" />}
        </button>
      </form>

      {/* Legal + footer */}
      <div className="mt-8">
        <p className="text-center text-xs text-slate-500">
          By creating an account, you agree to our{" "}
          <Link href="#" className="font-medium text-brand hover:underline">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="#" className="font-medium text-brand hover:underline">
            Privacy Policy
          </Link>
          .
        </p>

        <div className="mt-6 border-t border-slate-200 pt-4 text-center">
          <p className="text-slate-600">
            Already have an account?{" "}
            <Link href="/login" className="font-bold text-brand hover:underline">
              Log In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
