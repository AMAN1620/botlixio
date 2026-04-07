"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/Logo";
import { AuthGuard } from "@/components/AuthGuard";
import { useAuthStore } from "@/stores/auth-store";

function DashboardNav() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="border-b border-slate-200 bg-white px-6 py-3 lg:px-10">
      <div className="flex items-center justify-between">
        <Logo />
        <div className="flex items-center gap-4">
          {user && !user.is_verified && (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
              Email not verified
            </span>
          )}
          <div className="flex items-center gap-3">
            <div className="flex size-8 items-center justify-center rounded-full bg-brand-light text-sm font-bold text-brand">
              {user?.full_name?.charAt(0).toUpperCase() ?? "U"}
            </div>
            <div className="hidden md:block">
              <p className="text-sm font-semibold text-slate-900">
                {user?.full_name}
              </p>
              <p className="text-xs text-slate-500">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-page-bg font-sans">
        <DashboardNav />
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="flex gap-8 py-8">
            {/* Sidebar nav */}
            <aside className="hidden w-48 shrink-0 md:block">
              <nav className="flex flex-col gap-1">
                {[
                  { href: "/dashboard", label: "Dashboard" },
                  { href: "/agents", label: "Agents" },
                ].map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-white hover:text-brand"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </aside>
            <main className="min-w-0 flex-1">{children}</main>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
