"use client";

import { useState, useEffect, useRef } from "react";

interface WhatsAppConnectProps {
  agentId: string;
  userId: string;
}

type Status = "idle" | "starting" | "scanning" | "connected" | "error";

async function waFetch(method: "GET" | "POST", action: string, body?: object): Promise<Response> {
  if (method === "GET") {
    const params = new URLSearchParams(body as Record<string, string>);
    params.set("action", action);
    return fetch(`/api/whatsapp?${params.toString()}`);
  }
  return fetch(`/api/whatsapp?action=${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export default function WhatsAppConnect({ agentId, userId }: WhatsAppConnectProps) {
  const [status, setStatus] = useState<Status>("idle");
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [phone, setPhone] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const statusRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const qrRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function stopPolling() {
    if (statusRef.current) { clearInterval(statusRef.current); statusRef.current = null; }
    if (qrRef.current)     { clearInterval(qrRef.current);     qrRef.current = null;     }
  }

  useEffect(() => () => stopPolling(), []);

  async function pollStatus() {
    try {
      const res = await waFetch("GET", "status", { user_id: userId });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.status === "connected") {
        stopPolling();
        setPhone(data.phone ?? null);
        setQrCode(null);
        setStatus("connected");
      } else if (data.status === "scanning") {
        setStatus("scanning");
      }
    } catch (err) {
      stopPolling();
      setErrorMsg(err instanceof Error ? err.message : "Failed to fetch status.");
      setStatus("error");
    }
  }

  async function pollQr() {
    try {
      const res = await waFetch("GET", "qr", { user_id: userId });
      if (!res.ok) return; // not ready yet
      const data = await res.json();
      if (data.qr_code) setQrCode(data.qr_code);
    } catch {
      // non-fatal
    }
  }

  function startPolling() {
    statusRef.current = setInterval(pollStatus, 3000);
    qrRef.current     = setInterval(pollQr,     3000);
    pollStatus();
    pollQr();
  }

  async function handleConnect() {
    setStatus("starting");
    setErrorMsg(null);
    setQrCode(null);
    try {
      const res = await waFetch("POST", "start", { user_id: userId, agent_id: agentId });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b?.detail ?? `Error ${res.status}`);
      }
      setStatus("scanning");
      startPolling();
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Could not start session.");
      setStatus("error");
    }
  }

  async function handleDisconnect() {
    stopPolling();
    setErrorMsg(null);
    try {
      const res = await waFetch("POST", "stop", { user_id: userId });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        throw new Error(b?.detail ?? `Error ${res.status}`);
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Could not disconnect.");
      setStatus("error");
      return;
    }
    setStatus("idle");
    setPhone(null);
    setQrCode(null);
  }

  return (
    <div className="flex items-start gap-4">
      {/* Icon */}
      <div className="w-10 h-10 rounded-xl bg-[#25D366]/10 flex items-center justify-center flex-shrink-0">
        <svg className="w-5 h-5 text-[#25D366]" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
          <path d="M12.003 2C6.477 2 2 6.477 2 12.003c0 1.858.505 3.598 1.385 5.1L2 22l4.994-1.369A9.951 9.951 0 0 0 12.003 22C17.523 22 22 17.523 22 12.003 22 6.477 17.523 2 12.003 2zm0 18.175a8.144 8.144 0 0 1-4.153-1.14l-.298-.178-3.085.847.873-3.02-.195-.31a8.143 8.143 0 0 1-1.265-4.371c0-4.513 3.672-8.185 8.185-8.185 4.508 0 8.18 3.672 8.18 8.185 0 4.508-3.672 8.172-8.18 8.172z" />
        </svg>
      </div>

      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-semibold text-slate-900">WhatsApp Channel</h3>
        <p className="text-sm text-slate-500 mt-0.5 mb-3">
          Connect a WhatsApp number to receive and reply to messages via your agent.
        </p>

        {errorMsg && (
          <div className="mb-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {errorMsg}
          </div>
        )}

        {status === "idle" && (
          <button
            type="button"
            onClick={handleConnect}
            className="px-4 py-2 text-sm font-medium text-white bg-[#25D366] rounded-lg hover:bg-[#1ebe5d]"
          >
            Connect WhatsApp
          </button>
        )}

        {status === "starting" && (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <svg className="w-4 h-4 animate-spin text-[#25D366]" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Starting session…
          </div>
        )}

        {status === "scanning" && (
          <div className="space-y-3">
            <p className="text-xs text-slate-600 font-medium">
              Open WhatsApp → More options → Linked devices → Link a device
            </p>
            <div className="flex justify-start">
              {qrCode ? (
                <img src={qrCode} alt="WhatsApp QR code" className="w-48 h-48 rounded-lg border border-slate-200" />
              ) : (
                <div className="w-48 h-48 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-center">
                  <svg className="w-6 h-6 animate-spin text-slate-300" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                </div>
              )}
            </div>
            <p className="text-xs text-slate-400">QR refreshes every 60s. Waiting for scan…</p>
          </div>
        )}

        {status === "connected" && (
          <div className="flex items-center gap-3 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#25D366]/10 text-[#1a9e50] text-xs font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-[#25D366]" />
              Connected{phone ? ` — ${phone}` : ""}
            </span>
            <button
              type="button"
              onClick={handleDisconnect}
              className="text-xs text-slate-500 underline hover:text-slate-700"
            >
              Disconnect
            </button>
          </div>
        )}

        {status === "error" && (
          <button
            type="button"
            onClick={() => { setStatus("idle"); setErrorMsg(null); }}
            className="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
