"use strict";

const crypto = require("crypto");

const INSTALLED_SOCKETS = new WeakSet();
const SYSTEM_TYPES = new Set([
    "protocolMessage", "senderKeyDistributionMessage", "messageContextInfo",
    "reactionMessage", "pollUpdateMessage", "keepInChatMessage",
]);

function isEnabled(value) {
    return ["1", "true", "yes", "on"].includes(String(value || "").trim().toLowerCase());
}

function validateLocalUrl(value) {
    const parsed = new URL(value);
    if (parsed.protocol !== "http:" || !["127.0.0.1", "localhost", "[::1]"].includes(parsed.hostname)) {
        throw new Error("WHATSAPP_INBOUND_URL deve usar HTTP em loopback");
    }
    if (parsed.pathname !== "/internal/whatsapp/events") {
        throw new Error("WHATSAPP_INBOUND_URL possui rota inesperada");
    }
    return parsed.toString();
}

function unwrapMessage(content) {
    let current = content || {};
    for (const key of ["ephemeralMessage", "viewOnceMessage", "viewOnceMessageV2", "documentWithCaptionMessage"]) {
        if (current[key] && current[key].message) current = current[key].message;
    }
    return current;
}

function messageTypeAndText(content) {
    const message = unwrapMessage(content);
    const type = Object.keys(message)[0] || "unknown";
    let text = "";
    if (type === "conversation") text = message.conversation || "";
    else if (message[type] && typeof message[type] === "object") {
        text = message[type].text || message[type].caption || message[type].selectedDisplayText || "";
    }
    return { type, text: String(text).slice(0, 10000), system: SYSTEM_TYPES.has(type) };
}

function timestampIso(value, now = () => Date.now()) {
    let seconds = Number(value);
    if (!Number.isFinite(seconds) && value && typeof value.toNumber === "function") seconds = value.toNumber();
    const millis = Number.isFinite(seconds) && seconds > 0 ? seconds * 1000 : now();
    return new Date(millis).toISOString();
}

function buildInboundEvent(message, instance, now) {
    const key = message && message.key || {};
    const messageId = String(key.id || "").trim();
    const remoteJid = String(key.remoteJid || "").trim().toLowerCase();
    if (!messageId || !remoteJid) return null;
    const parsed = messageTypeAndText(message.message);
    const identity = `${instance}\n${messageId}\n${remoteJid}`;
    return {
        provider: "baileys",
        instance,
        event_id: crypto.createHash("sha256").update(identity).digest("hex"),
        message_id: messageId,
        remote_jid: remoteJid,
        from_me: key.fromMe === true,
        message_type: parsed.type,
        text: parsed.text,
        timestamp: timestampIso(message.messageTimestamp, now),
        raw_type: parsed.system ? parsed.type : undefined,
    };
}

function createInboundForwarder(options = {}) {
    const enabled = isEnabled(options.enabled);
    const instance = String(options.instance || "").trim();
    const token = String(options.token || "").trim();
    const url = validateLocalUrl(options.url || "http://127.0.0.1:8765/internal/whatsapp/events");
    const maxQueue = Math.max(1, Math.min(Number(options.maxQueue || 100), 1000));
    const timeoutMs = Math.max(250, Math.min(Number(options.timeoutMs || 5000), 30000));
    const maxAttempts = Math.max(1, Math.min(Number(options.maxAttempts || 3), 5));
    const request = options.fetch || globalThis.fetch;
    const sleep = options.sleep || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
    const logger = options.logger || console;
    const queue = [];
    let processing = false;
    let drainPromise = Promise.resolve();
    const stats = { queued: 0, forwarded: 0, failed: 0, dropped: 0 };

    async function post(event) {
        let lastError;
        for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), timeoutMs);
            try {
                const response = await request(url, {
                    method: "POST",
                    headers: { "content-type": "application/json", "x-whatsapp-inbound-token": token },
                    body: JSON.stringify(event),
                    signal: controller.signal,
                });
                if (response.ok) return true;
                lastError = new Error(`backend_http_${response.status}`);
                if (response.status < 500 && ![408, 429].includes(response.status)) break;
            } catch (error) {
                lastError = error;
            } finally {
                clearTimeout(timeout);
            }
            if (attempt < maxAttempts) await sleep(Math.min(500 * (2 ** (attempt - 1)), 4000));
        }
        logger.error(`[Baileys inbound] Evento nao entregue apos ${maxAttempts} tentativa(s): ${lastError && lastError.message || "erro"}`);
        return false;
    }

    async function work() {
        if (processing) return drainPromise;
        processing = true;
        drainPromise = (async () => {
            while (queue.length) {
                const event = queue.shift();
                const ok = await post(event);
                if (ok) stats.forwarded += 1;
                else stats.failed += 1;
            }
            processing = false;
        })();
        return drainPromise;
    }

    function enqueue(event) {
        if (!enabled) return false;
        if (!instance || !token) {
            logger.error("[Baileys inbound] Configuracao incompleta; evento nao encaminhado.");
            stats.dropped += 1;
            return false;
        }
        if (queue.length >= maxQueue) {
            logger.error("[Baileys inbound] Fila em memoria cheia; evento nao encaminhado.");
            stats.dropped += 1;
            return false;
        }
        queue.push(event);
        stats.queued += 1;
        void work();
        return true;
    }

    function handleUpsert(update) {
        for (const message of update && Array.isArray(update.messages) ? update.messages : []) {
            const event = buildInboundEvent(message, instance, options.now);
            if (event) enqueue(event);
        }
    }

    return { enabled, enqueue, handleUpsert, drain: () => drainPromise, stats, queueLength: () => queue.length };
}

function installInboundListener(sock, forwarder) {
    if (!sock || !sock.ev || INSTALLED_SOCKETS.has(sock)) return false;
    INSTALLED_SOCKETS.add(sock);
    sock.ev.on("messages.upsert", forwarder.handleUpsert);
    return true;
}

module.exports = {
    buildInboundEvent, createInboundForwarder, installInboundListener,
    isEnabled, messageTypeAndText, timestampIso, validateLocalUrl,
};
