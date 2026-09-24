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
const { createInboundForwarder, installInboundListener } = require("./inbound");
const { authorizeApiKey, authorizeOutboundSend } = require("./security");
const { fetchRegistryVersions, launchApprovedUpdate, readVersionState } = require("./maintenance");
require("dotenv").config();

const app     = express();
app.use(express.json());

const PORT     = parseInt(process.env.PORT    || "3001");
const API_KEY  = (process.env.API_KEY         || "").trim();
const AUTH_DIR = process.env.AUTH_DIR         || "./auth_info_baileys";
const OUTBOUND_ENABLED = process.env.WHATSAPP_OUTBOUND_ENABLED || "false";
const OUTBOUND_MODE = process.env.WHATSAPP_OUTBOUND_MODE ||
    (String(process.env.WHATSAPP_INBOUND_MODE || "").toLowerCase() === "sandbox" ? "sandbox" : "disabled");
const OUTBOUND_SANDBOX_NUMBERS = process.env.WHATSAPP_OUTBOUND_SANDBOX_NUMBERS ||
    process.env.WHATSAPP_INBOUND_SANDBOX_NUMBERS || "";
const OUTBOUND_PRODUCTION_APPROVED = process.env.WHATSAPP_OUTBOUND_PRODUCTION_APPROVED || "false";
const inbound = createInboundForwarder({
    enabled: process.env.WHATSAPP_INBOUND_ENABLED || "false",
    mode: process.env.WHATSAPP_INBOUND_MODE || "disabled",
    sandboxNumbers: process.env.WHATSAPP_INBOUND_SANDBOX_NUMBERS || "",
    sandboxLidMap: process.env.WHATSAPP_INBOUND_SANDBOX_LID_MAP || "",
    instance: process.env.WHATSAPP_INBOUND_INSTANCE || "",
    token: process.env.WHATSAPP_INBOUND_TOKEN || "",
    url: process.env.WHATSAPP_INBOUND_URL || "http://127.0.0.1:8765/internal/whatsapp/events",
    timeoutMs: process.env.WHATSAPP_INBOUND_TIMEOUT_MS || "5000",
    maxAttempts: process.env.WHATSAPP_INBOUND_MAX_ATTEMPTS || "3",
    maxQueue: process.env.WHATSAPP_INBOUND_MAX_QUEUE || "100",
});

let sock      = null;
let qrString  = null;   // string do QR (Baileys devolve a string raw)
let connected = false;
let retries   = 0;
let starting  = false;
let manualDisconnect = false;
let lastConnectionUpdate = null;
let inboundListenerInstalled = false;
const outboundReceipts = new Map();
const MAX_OUTBOUND_RECEIPTS = 2000;

function deliveryLabel(status) {
    return ({ 0: "failed", 1: "pending", 2: "server_ack", 3: "delivered", 4: "read", 5: "played" })[Number(status)] || "accepted";
}

function rememberOutboundReceipt(message) {
    const id = message && message.key && String(message.key.id || "").trim();
    if (!id) return null;
    outboundReceipts.set(id, { provider_message_id: id, delivery_status: "accepted", accepted_at: new Date().toISOString() });
    while (outboundReceipts.size > MAX_OUTBOUND_RECEIPTS) outboundReceipts.delete(outboundReceipts.keys().next().value);
    return outboundReceipts.get(id);
}

function updateOutboundReceipts(updates) {
    for (const item of Array.isArray(updates) ? updates : []) {
        const id = item && item.key && String(item.key.id || "").trim();
        const receipt = id && outboundReceipts.get(id);
        if (!receipt || item.update && item.update.status == null) continue;
        receipt.delivery_status = deliveryLabel(item.update.status);
        receipt.updated_at = new Date().toISOString();
    }
}

/* ── Auth middleware ─────────────────────────────────────── */
function checkAuth(req, res, next) {
    const auth = authorizeApiKey(API_KEY, req.headers["x-api-key"]);
    if (!auth.ok) return res.status(auth.status).json({ error: auth.code });
    next();
}

function checkLegacySend(req, res, next) {
    const phone = req.body && req.body.phone;
    const mappedJid = inbound.resolveOutboundJid(phone);
    const auth = authorizeOutboundSend({
        configuredKey: API_KEY,
        providedKey: req.headers["x-api-key"],
        outboundEnabled: OUTBOUND_ENABLED,
        mode: OUTBOUND_MODE,
        sandboxNumbers: OUTBOUND_SANDBOX_NUMBERS,
        productionApproved: OUTBOUND_PRODUCTION_APPROVED,
        phone,
        hasTrustedJid: Boolean(mappedJid),
    });
    if (!auth.ok) return res.status(auth.status).json({ error: auth.code, sent: "false" });
    req.outboundJid = mappedJid;
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
        browser: ["Menina dos Raios", "Chrome", "2.0.0"],
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
    sock.ev.on("messages.update", updateOutboundReceipts);
    inboundListenerInstalled = installInboundListener(sock, inbound);
}

/* ── Endpoints ───────────────────────────────────────────── */

// Status (sem auth — o Python usa para health-check)
app.get("/status", (_req, res) => {
    res.json({
        connected, hasQR: !!qrString, starting, lastConnectionUpdate,
        inbound: {
            enabled: inbound.enabled,
            mode: inbound.mode,
            listenerInstalled: inboundListenerInstalled,
            queued: inbound.queueLength(),
            received: inbound.stats.received,
            accepted: inbound.stats.accepted,
            forwarded: inbound.stats.forwarded,
            retry: inbound.stats.retry,
            forwardFailed: inbound.stats.forward_failed,
            failed: inbound.stats.failed,
            filtered: inbound.stats.filtered,
            duplicate: inbound.stats.duplicate,
        },
        outbound: { tracked: outboundReceipts.size },
    });
});

app.get("/send-status/:messageId", checkAuth, (req, res) => {
    const receipt = outboundReceipts.get(String(req.params.messageId || ""));
    if (!receipt) return res.status(404).json({ error: "message_not_tracked" });
    return res.json(receipt);
});

app.get("/maintenance/status", checkAuth, async (req, res) => {
    const state = readVersionState(__dirname);
    const refresh = String(req.query.refresh || "") === "1";
    const registry = refresh ? await fetchRegistryVersions() : { latest: null, legacy: null };
    res.json({
        ...state,
        latest_version: registry.latest,
        legacy_version: registry.legacy,
        connected,
        inbound_enabled: inbound.enabled,
        inbound_mode: inbound.mode,
        listener_installed: inboundListenerInstalled,
        node_version: process.version,
    });
});

app.post("/maintenance/update", checkAuth, (_req, res) => {
    const state = readVersionState(__dirname);
    if (state.update_status === "running") return res.status(409).json({ ok: false, error: "atualizacao_em_andamento" });
    if (!state.approved_version) return res.status(409).json({ ok: false, error: "versao_aprovada_ausente" });
    if (!state.update_available) return res.status(409).json({ ok: false, error: "versao_aprovada_ja_instalada" });
    try {
        const launched = launchApprovedUpdate();
        return res.status(202).json({ ok: true, message: "Atualizacao segura iniciada.", ...launched });
    } catch (error) {
        console.error("[Baileys] Falha ao iniciar atualizacao:", error.message);
        return res.status(503).json({ ok: false, error: error.message });
    }
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
app.post("/send", checkLegacySend, async (req, res) => {
    const { phone, message } = req.body || {};
    if (!phone || !message) {
        return res.status(400).json({ error: "phone e message são obrigatórios", sent: "false" });
    }
    if (!connected || !sock) {
        return res.status(503).json({ error: "WhatsApp não conectado. Escaneie o QR Code.", sent: "false" });
    }
    try {
        // Aceita "5595999999999" ou "5595999999999@s.whatsapp.net"
        const mappedJid = req.outboundJid || inbound.resolveOutboundJid(phone);
        const jid = mappedJid || (phone.includes("@") ? phone : `${phone}@s.whatsapp.net`);
        if (mappedJid) console.log("[Baileys] Envio sandbox usando o LID capturado na mensagem recebida.");
        const result = await sock.sendMessage(jid, { text: message });
        const receipt = rememberOutboundReceipt(result);
        return res.json({ sent: "true", ok: true, delivery_status: "accepted", provider_message_id: receipt && receipt.provider_message_id || null });
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
