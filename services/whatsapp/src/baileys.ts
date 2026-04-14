import path from "path";
import fs from "fs";
import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  WASocket,
  proto,
} from "@whiskeysockets/baileys";
import { Boom } from "@hapi/boom";
import QRCode from "qrcode";
import pino from "pino";
import { setSession, setQR, deleteSession, getSession } from "./sessions";
import { forwardToFastAPI } from "./bridge";

const logger = pino({ name: "baileys" });

// Suppress Baileys' own verbose logger
const baileysLogger = pino({ level: "silent" });

// Map of active sockets keyed by userId
const sockets = new Map<string, WASocket>();

const SESSIONS_DIR = process.env.SESSIONS_DIR ?? "./sessions";

function sessionDir(userId: string): string {
  return path.join(SESSIONS_DIR, userId);
}

// ---------------------------------------------------------------------------
// startSession
// ---------------------------------------------------------------------------

export async function startSession(userId: string, agentId: string): Promise<void> {
  // If a socket already exists for this user, stop it first
  if (sockets.has(userId)) {
    logger.info({ userId }, "Replacing existing session");
    await stopSession(userId);
  }

  // Ensure per-user auth directory exists
  const authDir = sessionDir(userId);
  fs.mkdirSync(authDir, { recursive: true });

  setSession(userId, { userId, agentId, status: "disconnected" });

  const { version } = await fetchLatestBaileysVersion();
  const { state, saveCreds } = await useMultiFileAuthState(authDir);

  const sock = makeWASocket({
    version,
    auth: {
      creds: state.creds,
      keys: makeCacheableSignalKeyStore(state.keys, baileysLogger as any),
    },
    printQRInTerminal: false,
    logger: baileysLogger as any,
    browser: ["Botlixio", "Chrome", "1.0.0"],
    syncFullHistory: false,
  });

  sockets.set(userId, sock);

  // ------------------------------------------------------------------
  // connection.update
  // ------------------------------------------------------------------
  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      try {
        const qrBase64 = await QRCode.toDataURL(qr);
        await setQR(userId, qrBase64);
        logger.info({ userId }, "QR code generated");
      } catch (err) {
        logger.error({ err, userId }, "Failed to generate QR PNG");
      }
    }

    if (connection === "open") {
      const phone = sock.user?.id?.split(":")[0] ?? undefined;
      setSession(userId, { status: "connected", phone });
      logger.info({ userId, phone }, "WhatsApp session connected");
    }

    if (connection === "close") {
      const statusCode = (lastDisconnect?.error as Boom)?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

      logger.info({ userId, statusCode, shouldReconnect }, "Connection closed");
      setSession(userId, { status: "disconnected" });

      if (shouldReconnect) {
        logger.info({ userId }, "Reconnecting...");
        // Small delay before reconnect to avoid tight loops
        setTimeout(() => {
          startSession(userId, agentId).catch((err) =>
            logger.error({ err, userId }, "Reconnect failed")
          );
        }, 3_000);
      } else {
        // Logged out — clean up persisted auth
        sockets.delete(userId);
        deleteSession(userId);
        try {
          fs.rmSync(authDir, { recursive: true, force: true });
        } catch {
          // best effort
        }
      }
    }
  });

  // ------------------------------------------------------------------
  // creds.update — persist auth credentials
  // ------------------------------------------------------------------
  sock.ev.on("creds.update", saveCreds);

  // ------------------------------------------------------------------
  // messages.upsert — handle inbound messages
  // ------------------------------------------------------------------
  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;

    const session = getSession(userId);
    if (!session) return;

    for (const msg of messages) {
      // Skip messages sent by this account
      if (msg.key.fromMe) continue;

      // Only handle real conversations (not groups for now)
      const jid = msg.key.remoteJid;
      if (!jid || jid.endsWith("@g.us")) continue;

      const text = extractText(msg);
      if (!text) continue;

      // Normalise phone: strip @s.whatsapp.net suffix
      const senderPhone = jid.replace("@s.whatsapp.net", "");

      logger.info({ userId, senderPhone, text: text.slice(0, 80) }, "Inbound message");

      try {
        const reply = await forwardToFastAPI(session.agentId, senderPhone, text, userId);
        await sock.sendMessage(jid, { text: reply });
        logger.info({ userId, senderPhone }, "Reply sent");
      } catch (err) {
        logger.error({ err, userId, senderPhone }, "Failed to send reply");
      }
    }
  });
}

// ---------------------------------------------------------------------------
// stopSession
// ---------------------------------------------------------------------------

export async function stopSession(userId: string): Promise<void> {
  const sock = sockets.get(userId);
  if (sock) {
    try {
      await sock.end(undefined);
    } catch {
      // ignore errors on close
    }
    sockets.delete(userId);
  }
  setSession(userId, { status: "disconnected" });
  logger.info({ userId }, "Session stopped");
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function extractText(msg: proto.IWebMessageInfo): string | null {
  const content = msg.message;
  if (!content) return null;

  return (
    content.conversation ??
    content.extendedTextMessage?.text ??
    content.imageMessage?.caption ??
    content.videoMessage?.caption ??
    null
  );
}
