/**
 * Next.js API proxy for the Baileys WhatsApp microservice.
 * Adds X-Internal-Secret server-side so the secret is never exposed to the browser.
 *
 * Forwards:  POST /api/whatsapp  →  Baileys POST /sessions/{action}
 *            GET  /api/whatsapp  →  Baileys GET  /sessions/{action}
 *
 * Caller sends ?action=start|stop|status|qr&user_id=...
 */

import { NextRequest, NextResponse } from "next/server";

const WA_URL = process.env.WHATSAPP_SERVICE_URL || "http://localhost:3001";
const SECRET = process.env.INTERNAL_SECRET || "";

function serviceHeaders(contentType?: string) {
  const h: Record<string, string> = { "X-Internal-Secret": SECRET };
  if (contentType) h["Content-Type"] = contentType;
  return h;
}

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const action = searchParams.get("action");
  const userId = searchParams.get("user_id");

  if (!action || !userId) {
    return NextResponse.json({ detail: "Missing action or user_id" }, { status: 400 });
  }

  const upstream = await fetch(
    `${WA_URL}/sessions/${action}?user_id=${encodeURIComponent(userId)}`,
    { headers: serviceHeaders() }
  );

  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}

export async function POST(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const action = searchParams.get("action");

  if (!action) {
    return NextResponse.json({ detail: "Missing action" }, { status: 400 });
  }

  const payload = await req.json().catch(() => ({}));

  const upstream = await fetch(`${WA_URL}/sessions/${action}`, {
    method: "POST",
    headers: serviceHeaders("application/json"),
    body: JSON.stringify(payload),
  });

  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}
