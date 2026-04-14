import axios from "axios";
import pino from "pino";

const logger = pino({ name: "bridge" });

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://backend:8000";
const INTERNAL_SECRET = process.env.INTERNAL_SECRET ?? "";
const FALLBACK_REPLY = "Agent is currently unavailable. Please try again later.";
const RATE_LIMIT_REPLY = "Too many messages. Please slow down.";

// ---------------------------------------------------------------------------
// Per-sender rate limiting — max 10 messages per 60-second window
// ---------------------------------------------------------------------------
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 10;

const senderTimestamps = new Map<string, number[]>();

function isRateLimited(senderPhone: string): boolean {
  const now = Date.now();
  const timestamps = (senderTimestamps.get(senderPhone) ?? []).filter(
    (t) => now - t < RATE_WINDOW_MS
  );
  timestamps.push(now);
  senderTimestamps.set(senderPhone, timestamps);
  return timestamps.length > RATE_MAX;
}

// Periodically clean up stale sender entries to avoid memory leaks
setInterval(() => {
  const now = Date.now();
  for (const [phone, timestamps] of senderTimestamps.entries()) {
    const fresh = timestamps.filter((t) => now - t < RATE_WINDOW_MS);
    if (fresh.length === 0) {
      senderTimestamps.delete(phone);
    } else {
      senderTimestamps.set(phone, fresh);
    }
  }
}, RATE_WINDOW_MS);

// ---------------------------------------------------------------------------
// Main bridge function
// ---------------------------------------------------------------------------

export async function forwardToFastAPI(
  agentId: string,
  senderPhone: string,
  message: string,
  userId: string
): Promise<string> {
  if (isRateLimited(senderPhone)) {
    logger.warn({ senderPhone }, "Rate limit exceeded");
    return RATE_LIMIT_REPLY;
  }

  try {
    const response = await axios.post(
      `${FASTAPI_URL}/api/v1/channels/whatsapp/message`,
      {
        agent_id: agentId,
        sender_phone: senderPhone,
        message,
        user_id: userId,
      },
      {
        headers: {
          "X-Internal-Secret": INTERNAL_SECRET,
          "Content-Type": "application/json",
        },
        timeout: 15_000,
      }
    );

    const reply = response.data?.reply;
    if (typeof reply === "string" && reply.trim().length > 0) {
      return reply;
    }

    logger.warn({ agentId, response: response.data }, "FastAPI returned no reply field");
    return FALLBACK_REPLY;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      logger.error(
        { agentId, senderPhone, status: err.response?.status, message: err.message },
        "FastAPI request failed"
      );
    } else {
      logger.error({ err }, "Unexpected error forwarding to FastAPI");
    }
    return FALLBACK_REPLY;
  }
}
