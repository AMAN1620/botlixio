import Link from "next/link";
import { Logo } from "@/components/Logo";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-page-bg font-sans">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white px-10 py-4">
        <div className="flex items-center justify-between">
          <Logo />
          <Link
            href="/"
            className="text-sm font-semibold text-slate-600 hover:text-slate-900"
          >
            Back to site
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white px-6 py-8">
        <div className="flex flex-col items-center gap-4 md:flex-row md:justify-center md:gap-6">
          <p className="text-sm text-slate-500">
            &copy; 2024 Botlixio Inc. All rights reserved.
          </p>
          <div className="flex gap-4">
            <Link href="#" className="text-sm text-slate-500 hover:text-brand">
              Support
            </Link>
            <Link href="#" className="text-sm text-slate-500 hover:text-brand">
              Documentation
            </Link>
            <Link href="#" className="text-sm text-slate-500 hover:text-brand">
              Status
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
