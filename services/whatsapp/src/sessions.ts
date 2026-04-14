import Redis from "ioredis";
import pino from "pino";

const logger = pino({ name: "sessions" });

export type SessionStatus = "disconnected" | "scanning" | "connected";

export interface SessionInfo {
  userId: string;
  agentId: string;
  status: SessionStatus;
  phone?: string;    // set once connected
  qrCode?: string;   // base64 PNG, 60s TTL
  qrExpiry?: number; // unix ms
}

// ---------------------------------------------------------------------------
// In-memory store
// ---------------------------------------------------------------------------
const sessions = new Map<string, SessionInfo>();

// ---------------------------------------------------------------------------
// Redis client (optional — gracefully disabled if REDIS_URL is unset)
// ---------------------------------------------------------------------------
let redis: Redis | null = null;

if (process.env.REDIS_URL) {
  redis = new Redis(process.env.REDIS_URL, {
    lazyConnect: true,
    maxRetriesPerRequest: 2,
  });

  redis.on("error", (err) => {
    logger.error({ err }, "Redis connection error");
  });

  redis.connect().catch((err) => {
    logger.warn({ err }, "Could not connect to Redis — running without cache");
    redis = null;
  });
}

// ---------------------------------------------------------------------------
// Exported helpers
// ---------------------------------------------------------------------------

export function getSession(userId: string): SessionInfo | undefined {
  return sessions.get(userId);
}

/**
 * Merges `info` into the existing session entry (or creates a new one).
 * Also persists non-QR session metadata to Redis for cross-instance visibility.
 */
export function setSession(userId: string, info: Partial<SessionInfo>): void {
  const existing = sessions.get(userId);
  const updated: SessionInfo = { ...(existing ?? { userId, agentId: "", status: "disconnected" }), ...info };
  sessions.set(userId, updated);

  if (redis) {
    const { qrCode: _qr, qrExpiry: _exp, ...meta } = updated;
    redis
      .set(`wa_session:${userId}`, JSON.stringify(meta))
      .catch((err) => logger.warn({ err }, "Redis setSession failed"));
  }
}

export function deleteSession(userId: string): void {
  sessions.delete(userId);

  if (redis) {
    redis
      .del(`wa_session:${userId}`, `wa_qr:${userId}`)
      .catch((err) => logger.warn({ err }, "Redis deleteSession failed"));
  }
}

/**
 * Saves a QR code to in-memory store and Redis with a 60-second TTL.
 */
export async function setQR(userId: string, qrBase64: string): Promise<void> {
  const qrExpiry = Date.now() + 60_000;

  setSession(userId, { qrCode: qrBase64, qrExpiry, status: "scanning" });

  if (redis) {
    await redis
      .set(`wa_qr:${userId}`, qrBase64, "EX", 60)
      .catch((err) => logger.warn({ err }, "Redis setQR failed"));
  }
}

/**
 * Returns the QR code from in-memory store (fast path).
 * Returns undefined if no session, no QR, or the QR has expired.
 */
export function getQR(userId: string): string | undefined {
  const session = sessions.get(userId);
  if (!session?.qrCode) return undefined;
  if (session.qrExpiry && Date.now() > session.qrExpiry) {
    // Expired — clean up the stale QR fields
    setSession(userId, { qrCode: undefined, qrExpiry: undefined });
    return undefined;
  }
  return session.qrCode;
}
