"use client";

import { useAuthStore } from "@/stores/auth-store";

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div>
      <h1 className="text-3xl font-black tracking-tight text-slate-900">
        Welcome back, {user?.full_name?.split(" ")[0] ?? "there"}!
      </h1>
      <p className="mt-2 text-slate-600">
        This is your Botlixio dashboard. Agent builder features coming soon.
      </p>

      {/* Quick stats placeholder */}
      <div className="mt-8 grid gap-6 md:grid-cols-3">
        {[
          { label: "Agents", value: "0", desc: "No agents yet" },
          { label: "Messages", value: "0", desc: "This month" },
          { label: "Plan", value: "Free", desc: "Upgrade for more" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-slate-200 bg-white p-6"
          >
            <p className="text-sm font-medium text-slate-500">{stat.label}</p>
            <p className="mt-1 text-3xl font-black text-slate-900">
              {stat.value}
            </p>
            <p className="mt-1 text-sm text-slate-500">{stat.desc}</p>
          </div>
        ))}
      </div>

      {/* Account info */}
      <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-bold text-slate-900">Account Details</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-slate-500">Email</p>
            <p className="font-medium text-slate-900">{user?.email}</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Verified</p>
            <p className="font-medium text-slate-900">
              {user?.is_verified ? (
                <span className="text-green-600">Yes</span>
              ) : (
                <span className="text-amber-600">No — check your email</span>
              )}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Role</p>
            <p className="font-medium text-slate-900 capitalize">
              {user?.role}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Member since</p>
            <p className="font-medium text-slate-900">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString()
                : "—"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
