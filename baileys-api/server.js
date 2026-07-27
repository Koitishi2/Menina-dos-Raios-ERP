/**
 * Menina dos Raios — WhatsApp Baileys API
 * Serviço local que conecta ao WhatsApp Web via Baileys e expõe
 * um endpoint HTTP para o backend Python enviar mensagens.
 *
 * Portas: 3001 (padrão) — não conflita com Python (8765).
 */
"use strict";

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion }
    = require("@whiskeysockets/baileys");
const express = require("express");
const pino    = require("pino");
const fs      = require("fs");
require("dotenv").config();

const app     = express();
app.use(express.json());

const PORT     = parseInt(process.env.PORT    || "3001");
const API_KEY  = (process.env.API_KEY         || "").trim();
const AUTH_DIR = process.env.AUTH_DIR         || "./auth_info_baileys";

let sock      = null;
let qrString  = null;   // string do QR (Baileys devolve a string raw)
let connected = false;
let retries   = 0;
let starting  = false;
let manualDisconnect = false;
let lastConnectionUpdate = null;

/* ── Auth middleware ─────────────────────────────────────── */
function checkAuth(req, res, next) {
    if (API_KEY && req.headers["x-api-key"] !== API_KEY) {
        return res.status(401).json({ error: "Unauthorized" });
    }
    next();
}

/* ── Conexão Baileys ─────────────────────────────────────── */
async function startBaileys() {
    if (starting) return;
    starting = true;
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        logger: pino({ level: "silent" }),
        printQRInTerminal: true,   // também imprime no console para fallback
        auth: state,
        browser: ["Menina dos Raios", "Chrome", "1.0.0"],
        connectTimeoutMs: 30000,
        defaultQueryTimeoutMs: 30000,
        keepAliveIntervalMs: 15000,
    });
    starting = false;

    sock.ev.on("connection.update", (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            qrString  = qr;
            connected = false;
            lastConnectionUpdate = new Date().toISOString();
            console.log(`[Baileys] QR Code pronto. Acesse GET /qr para exibir no sistema.`);
        }

        if (connection === "close") {
            connected = false;
            qrString  = null;
            lastConnectionUpdate = new Date().toISOString();
            const code = lastDisconnect?.error?.output?.statusCode;
            const isLoggedOut = code === DisconnectReason.loggedOut;
            console.log(`[Baileys] Desconectado (código ${code}).`, isLoggedOut ? "Sessão encerrada." : "Reconectando...");
            if (!isLoggedOut && !manualDisconnect) {
                retries++;
                const delay = Math.min(3000 * retries, 30000);
                setTimeout(startBaileys, delay);
            }
        }

        if (connection === "open") {
            connected = true;
            qrString  = null;
            retries   = 0;
            manualDisconnect = false;
            lastConnectionUpdate = new Date().toISOString();
            console.log("[Baileys] ✅ Conectado ao WhatsApp!");
        }
    });

    sock.ev.on("creds.update", saveCreds);
}

/* ── Endpoints ───────────────────────────────────────────── */

// Status (sem auth — o Python usa para health-check)
app.get("/status", (_req, res) => {
    res.json({ connected, hasQR: !!qrString, starting, lastConnectionUpdate });
});

// QR Code em texto (o frontend exibe com uma lib JS qrcode)
app.get("/qr", (_req, res) => {
    if (connected) return res.json({ connected: true, message: "Já conectado!" });
    if (!qrString) return res.json({ connected: false, message: "Aguardando QR Code... Reiniciando serviço?" });
    res.json({ connected: false, qr: qrString });
});

// Tenta restabelecer a sessao existente sem apagar as credenciais.
app.post("/reconnect", checkAuth, async (_req, res) => {
    if (connected) return res.json({ ok: true, connected: true, message: "WhatsApp ja esta conectado." });
    manualDisconnect = false;
    try {
        if (sock && sock.ws) sock.ws.close();
    } catch (_) {}
    sock = null;
    startBaileys().catch((e) => console.error("[Baileys] Falha ao reconectar:", e));
    return res.json({ ok: true, connected: false, message: "Reconexao iniciada. Aguarde alguns segundos." });
});

// Encerra a sessao, remove as credenciais locais e inicia uma nova leitura de QR.
app.post("/disconnect", checkAuth, async (_req, res) => {
    manualDisconnect = true;
    connected = false;
    qrString = null;
    try {
        if (sock) await sock.logout();
    } catch (e) {
        console.warn("[Baileys] Logout retornou:", e.message);
    }
    sock = null;
    try { fs.rmSync(AUTH_DIR, { recursive: true, force: true }); } catch (e) {
        return res.status(500).json({ ok: false, error: "Nao foi possivel limpar a sessao: " + e.message });
    }
    setTimeout(() => {
        manualDisconnect = false;
        startBaileys().catch((e) => console.error("[Baileys] Falha ao gerar nova sessao:", e));
    }, 800);
    return res.json({ ok: true, connected: false, message: "Sessao desconectada. Um novo QR Code sera gerado." });
});

// Envio de mensagem — usado pelo Python
app.post("/send", checkAuth, async (req, res) => {
    const { phone, message } = req.body || {};
    if (!phone || !message) {
        return res.status(400).json({ error: "phone e message são obrigatórios", sent: "false" });
    }
    if (!connected || !sock) {
        return res.status(503).json({ error: "WhatsApp não conectado. Escaneie o QR Code.", sent: "false" });
    }
    try {
        // Aceita "5595999999999" ou "5595999999999@s.whatsapp.net"
        const jid = phone.includes("@") ? phone : `${phone}@s.whatsapp.net`;
        await sock.sendMessage(jid, { text: message });
        return res.json({ sent: "true", ok: true });
    } catch (e) {
        console.error("[Baileys] Erro ao enviar:", e.message);
        return res.status(500).json({ error: e.message, sent: "false" });
    }
});

/* ── Start ───────────────────────────────────────────────── */
app.listen(PORT, "127.0.0.1", () => {
    console.log(`[Baileys] API rodando em http://127.0.0.1:${PORT}`);
    console.log(`[Baileys] Auth dir: ${AUTH_DIR}`);
});

startBaileys().catch((e) => {
    console.error("[Baileys] Falha fatal:", e);
    process.exit(1);
});
