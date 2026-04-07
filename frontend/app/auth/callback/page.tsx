"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export default function OAuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <div className="size-8 animate-spin rounded-full border-3 border-slate-200 border-t-brand" />
        </div>
      }
    >
      <OAuthCallbackContent />
    </Suspense>
  );
}

function OAuthCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { fetchUser } = useAuthStore();
  const [error, setError] = useState("");

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setError(errorParam);
      return;
    }

    if (accessToken && refreshToken) {
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      fetchUser().then(() => {
        router.replace("/dashboard");
      });
    } else {
      setError("Missing tokens from OAuth callback.");
    }
  }, [searchParams, router, fetchUser]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-page-bg">
        <div className="w-full max-w-[440px] text-center">
          <h1 className="text-3xl font-black tracking-tight text-slate-900">
            Authentication Failed
          </h1>
          <p className="mt-3 text-slate-600">{error}</p>
          <a
            href="/login"
            className="mt-8 inline-block rounded-lg bg-brand px-8 py-3 font-bold text-white hover:bg-brand/90"
          >
            Back to Login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-page-bg">
      <div className="size-8 animate-spin rounded-full border-3 border-slate-200 border-t-brand" />
      <p className="text-sm text-slate-500">Completing sign in...</p>
    </div>
  );
}
