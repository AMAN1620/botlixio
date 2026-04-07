"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { AxiosError } from "axios";

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="size-8 animate-spin rounded-full border-3 border-slate-200 border-t-brand" />}>
      <VerifyEmailContent />
    </Suspense>
  );
}

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error">(
    token ? "loading" : "error",
  );
  const [message, setMessage] = useState(
    token ? "Verifying your email..." : "No verification token provided.",
  );

  useEffect(() => {
    if (!token) return;

    authApi
      .verifyEmail(token)
      .then(({ data }) => {
        setStatus("success");
        setMessage(data.message || "Email verified successfully!");
      })
      .catch((err: AxiosError<{ detail?: string }>) => {
        setStatus("error");
        setMessage(
          err.response?.data?.detail || "Verification failed. The link may have expired.",
        );
      });
  }, [token]);

  return (
    <div className="w-full max-w-[440px] text-center">
      {/* Icon */}
      <div
        className={`mx-auto mb-6 flex size-16 items-center justify-center rounded-full ${
          status === "success"
            ? "bg-green-100"
            : status === "error"
              ? "bg-red-100"
              : "bg-slate-100"
        }`}
      >
        {status === "loading" && (
          <div className="size-6 animate-spin rounded-full border-2 border-slate-300 border-t-brand" />
        )}
        {status === "success" && (
          <svg className="size-8 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        )}
        {status === "error" && (
          <svg className="size-8 text-red-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="m15 9-6 6" />
            <path d="m9 9 6 6" />
          </svg>
        )}
      </div>

      <h1 className="text-3xl font-black tracking-tight text-slate-900">
        {status === "success"
          ? "Email Verified!"
          : status === "error"
            ? "Verification Failed"
            : "Verifying..."}
      </h1>
      <p className="mt-3 text-slate-600">{message}</p>

      <div className="mt-8">
        {status === "success" && (
          <Link
            href="/login"
            className="inline-block rounded-lg bg-brand px-8 py-3 font-bold text-white hover:bg-brand/90"
          >
            Go to Login
          </Link>
        )}
        {status === "error" && (
          <Link
            href="/register"
            className="inline-block rounded-lg border border-slate-200 bg-white px-8 py-3 font-bold text-slate-900 hover:bg-slate-50"
          >
            Back to Register
          </Link>
        )}
      </div>
    </div>
  );
}
