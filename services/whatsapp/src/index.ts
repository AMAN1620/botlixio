import express, { Request, Response, NextFunction } from "express";
import pino from "pino";
import { startSession, stopSession } from "./baileys";
import { getSession, getQR } from "./sessions";

const logger = pino({ name: "server" });

const app = express();
app.use(express.json());

const INTERNAL_SECRET = process.env.INTERNAL_SECRET ?? "";
const PORT = parseInt(process.env.PORT ?? "3001", 10);

// ---------------------------------------------------------------------------
// Health check — no auth required
// ---------------------------------------------------------------------------
app.get("/health", (_req: Request, res: Response) => {
  res.json({ ok: true });
});

// ---------------------------------------------------------------------------
// Auth middleware — all other routes require X-Internal-Secret
// ---------------------------------------------------------------------------
function requireSecret(req: Request, res: Response, next: NextFunction): void {
  const provided = req.headers["x-internal-secret"];
  if (!INTERNAL_SECRET || provided !== INTERNAL_SECRET) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  next();
}

app.use(requireSecret);

// ---------------------------------------------------------------------------
// POST /sessions/start
// ---------------------------------------------------------------------------
app.post("/sessions/start", async (req: Request, res: Response): Promise<void> => {
  const { user_id: userId, agent_id: agentId } = req.body as {
    user_id?: string;
    agent_id?: string;
  };

  if (!userId || !agentId) {
    res.status(400).json({ error: "user_id and agent_id are required" });
    return;
  }

  try {
    // Fire and forget — QR will be available via /sessions/qr shortly after
    startSession(userId, agentId).catch((err) =>
      logger.error({ err, userId }, "startSession error")
    );
    res.json({ message: "Session starting. Scan QR to connect." });
  } catch (err) {
    logger.error({ err, userId }, "Failed to start session");
    res.status(500).json({ error: "Failed to start session" });
  }
});

// ---------------------------------------------------------------------------
// GET /sessions/qr?user_id=...
// ---------------------------------------------------------------------------
app.get("/sessions/qr", (req: Request, res: Response): void => {
  const userId = req.query["user_id"] as string | undefined;

  if (!userId) {
    res.status(400).json({ error: "user_id query parameter is required" });
    return;
  }

  const session = getSession(userId);
  if (!session) {
    res.status(404).json({ error: "No session found for this user" });
    return;
  }

  if (session.status !== "scanning") {
    res.status(404).json({ error: "Session is not in scanning state", status: session.status });
    return;
  }

  const qrCode = getQR(userId);
  if (!qrCode) {
    res.status(404).json({ error: "QR code not available or expired" });
    return;
  }

  res.json({ qr_code: qrCode, status: "scanning" });
});

// ---------------------------------------------------------------------------
// GET /sessions/status?user_id=...
// ---------------------------------------------------------------------------
app.get("/sessions/status", (req: Request, res: Response): void => {
  const userId = req.query["user_id"] as string | undefined;

  if (!userId) {
    res.status(400).json({ error: "user_id query parameter is required" });
    return;
  }

  const session = getSession(userId);
  if (!session) {
    res.status(404).json({ error: "No session found for this user" });
    return;
  }

  res.json({ status: session.status, phone: session.phone ?? null });
});

// ---------------------------------------------------------------------------
// POST /sessions/stop
// ---------------------------------------------------------------------------
app.post("/sessions/stop", async (req: Request, res: Response): Promise<void> => {
  const { user_id: userId } = req.body as { user_id?: string };

  if (!userId) {
    res.status(400).json({ error: "user_id is required" });
    return;
  }

  try {
    await stopSession(userId);
    res.json({ message: "Session stopped." });
  } catch (err) {
    logger.error({ err, userId }, "Failed to stop session");
    res.status(500).json({ error: "Failed to stop session" });
  }
});

// ---------------------------------------------------------------------------
// Global error handler
// ---------------------------------------------------------------------------
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  logger.error({ err }, "Unhandled error");
  res.status(500).json({ error: "Internal server error" });
});

// ---------------------------------------------------------------------------
// Start server
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  logger.info({ port: PORT }, "Botlixio WhatsApp service started");
});

export default app;
