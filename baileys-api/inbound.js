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

function normalizePhone(value) {
    return String(value || "").split("@")[0].split(":")[0].replace(/\D/g, "");
}

function shortHash(value) {
    return crypto.createHash("sha256").update(String(value || "")).digest("hex").slice(0, 12);
}

function maskPhone(value) {
    const phone = normalizePhone(value);
    if (!phone) return "none";
    return `****${phone.slice(-4)}`;
}

function jidKind(value) {
    const jid = String(value || "").trim().toLowerCase();
    if (!jid) return "unknown";
    if (jid === "status@broadcast") return "status";
    if (jid.endsWith("@broadcast")) return "broadcast";
    if (jid.endsWith("@s.whatsapp.net")) return "jid";
    if (jid.endsWith("@lid")) return "lid";
    return "unknown";
}

function keyMetadata(message = {}) {
    const key = message && message.key || {};
    const remoteJid = String(key.remoteJid || "").trim().toLowerCase();
    const remoteJidAlt = String(key.remoteJidAlt || "").trim().toLowerCase();
    const participant = String(key.participant || "").trim().toLowerCase();
    const participantAlt = String(key.participantAlt || "").trim().toLowerCase();
    const selected = individualJid(key);
    return {
        messageIdHash: shortHash(key.id || ""),
        senderKind: jidKind(remoteJid),
        selectedKind: jidKind(selected),
        senderMasked: maskPhone(selected || remoteJid || participant),
        fromMe: key.fromMe === true,
        hasRemoteJidAlt: !!remoteJidAlt,
        hasParticipantAlt: !!participantAlt,
        hasParticipant: !!participant,
        selectedJid: selected,
    };
}

function logMarker(logger, marker, data = {}) {
    const line = Object.entries(data)
        .map(([key, value]) => `${key}=${String(value == null ? "" : value)}`)
        .join(" ");
    const message = line ? `${marker} ${line}` : marker;
    if (typeof logger.info === "function") logger.info(message);
    else if (typeof logger.log === "function") logger.log(message);
}

function phoneAliases(value) {
    const phone = normalizePhone(value);
    const aliases = new Set(phone ? [phone] : []);
    // O WhatsApp ainda pode entregar celulares brasileiros no JID legado,
    // sem o nono digito. A equivalencia fica restrita ao DDI 55.
    if (/^55\d{11}$/.test(phone) && phone[4] === "9") {
        aliases.add(`${phone.slice(0, 4)}${phone.slice(5)}`);
    } else if (/^55\d{10}$/.test(phone)) {
        aliases.add(`${phone.slice(0, 4)}9${phone.slice(4)}`);
    }
    return aliases;
}

function parseSandboxNumbers(value) {
    const entries = Array.isArray(value) ? value : String(value || "").split(",");
    const numbers = new Set();
    for (const entry of entries) {
        for (const phone of phoneAliases(entry)) {
            if (phone.length >= 10 && phone.length <= 15) numbers.add(phone);
        }
    }
    return numbers;
}

function individualJid(key = {}) {
    const candidates = [key.remoteJidAlt, key.participantAlt, key.remoteJid, key.participant]
        .map((value) => String(value || "").trim().toLowerCase())
        .filter(Boolean);
    return candidates.find((jid) => jid.endsWith("@s.whatsapp.net")) || candidates[0] || "";
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
    const remoteJid = individualJid(key);
    const remoteJidAlt = String(key.remoteJidAlt || "").trim().toLowerCase();
    const participantAlt = String(key.participantAlt || "").trim().toLowerCase();
    if (!messageId || !remoteJid) return null;
    const parsed = messageTypeAndText(message.message);
    const identity = `${instance}\n${messageId}\n${remoteJid}`;
    return {
        provider: "baileys",
        instance,
        event_id: crypto.createHash("sha256").update(identity).digest("hex"),
        message_id: messageId,
        remote_jid: remoteJid,
        remote_jid_alt: remoteJidAlt || undefined,
        participant_alt: participantAlt || undefined,
        from_me: key.fromMe === true,
        message_type: parsed.type,
        text: parsed.text,
        timestamp: timestampIso(message.messageTimestamp, now),
        raw_type: parsed.system ? parsed.type : undefined,
    };
}

function createInboundForwarder(options = {}) {
    const enabled = isEnabled(options.enabled);
    const mode = String(options.mode || "disabled").trim().toLowerCase();
    const sandboxNumbers = parseSandboxNumbers(options.sandboxNumbers);
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
    const knownEvents = new Map();
    const maxKnownEvents = Math.max(100, Math.min(Number(options.maxKnownEvents || 2000), 10000));
    let processing = false;
    let drainPromise = Promise.resolve();
    const stats = { queued: 0, forwarded: 0, failed: 0, dropped: 0, filtered: 0, duplicate: 0 };

    function rememberEvent(eventId) {
        knownEvents.delete(eventId);
        knownEvents.set(eventId, true);
        while (knownEvents.size > maxKnownEvents) knownEvents.delete(knownEvents.keys().next().value);
    }

    function isForwardableIndividual(event) {
        if (!event || event.from_me) return false;
        const remoteJid = String(event.remote_jid || "");
        if (remoteJid.endsWith("@s.whatsapp.net")) return true;
        return mode === "production" && remoteJid.endsWith("@lid");
    }

    function isSandboxAllowed(event) {
        if (!isForwardableIndividual(event)) return false;
        if (mode !== "sandbox" || sandboxNumbers.size === 0) return false;
        return [...phoneAliases(event.remote_jid)].some((phone) => sandboxNumbers.has(phone));
    }

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
        logMarker(logger, "WA_AUTOREPLY_DECISION", {
            messageIdHash: shortHash(event && event.message_id),
            decision: "error",
            reason: "backend_unavailable",
            messageType: event && event.message_type,
            senderMasked: maskPhone(event && event.remote_jid),
        });
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
                if (ok) {
                    stats.forwarded += 1;
                    rememberEvent(event.event_id);
                    if (typeof logger.info === "function") logger.info("[Baileys inbound] Evento encaminhado.");
                } else {
                    stats.failed += 1;
                    knownEvents.delete(event.event_id);
                }
            }
            processing = false;
        })();
        return drainPromise;
    }

    function enqueue(event) {
        if (!enabled) {
            logMarker(logger, "WA_INBOUND_IGNORED_REASON", {
                messageIdHash: shortHash(event && event.message_id), reason: "config_disabled",
                messageType: event && event.message_type, fromMe: !!(event && event.from_me),
                senderMasked: maskPhone(event && event.remote_jid),
                senderKind: jidKind(event && event.remote_jid),
            });
            return false;
        }
        if (mode !== "sandbox" && mode !== "production") {
            stats.filtered += 1;
            logMarker(logger, "WA_INBOUND_IGNORED_REASON", {
                messageIdHash: shortHash(event && event.message_id), reason: "config_disabled",
                mode, messageType: event && event.message_type,
                senderMasked: maskPhone(event && event.remote_jid),
                senderKind: jidKind(event && event.remote_jid),
            });
            return false;
        }
        if (!isForwardableIndividual(event)) {
            stats.filtered += 1;
            const kind = jidKind(event && event.remote_jid);
            let reason = "non_individual_jid";
            if (event && event.from_me) reason = "from_me";
            else if (kind === "status" || kind === "broadcast") reason = "status_or_broadcast";
            else if (kind === "lid") reason = "lid_without_alt";
            logMarker(logger, "WA_INBOUND_IGNORED_REASON", {
                messageIdHash: shortHash(event && event.message_id),
                reason,
                messageType: event && event.message_type,
                fromMe: !!(event && event.from_me),
                senderMasked: maskPhone(event && event.remote_jid),
                senderKind: kind,
            });
            return false;
        }
        if (mode === "sandbox" && !isSandboxAllowed(event)) {
            stats.filtered += 1;
            logMarker(logger, "WA_INBOUND_IGNORED_REASON", {
                messageIdHash: shortHash(event.message_id), reason: "sandbox_inbound_blocked",
                messageType: event.message_type,
                senderMasked: maskPhone(event.remote_jid),
                senderKind: jidKind(event.remote_jid),
            });
            return false;
        }
        if (String(event.message_type || "") === "unknown" && !String(event.text || "").trim()) {
            stats.filtered += 1;
            logMarker(logger, "WA_INBOUND_IGNORED_REASON", {
                messageIdHash: shortHash(event.message_id), reason: "message_not_decoded",
                messageType: event.message_type,
                senderMasked: maskPhone(event.remote_jid),
                senderKind: jidKind(event.remote_jid),
            });
            return false;
        }
        if (!instance || !token) {
            logMarker(logger, "WA_AUTOREPLY_DECISION", {
                messageIdHash: shortHash(event.message_id), decision: "blocked", reason: "config_disabled",
                messageType: event.message_type,
                senderMasked: maskPhone(event.remote_jid),
                senderKind: jidKind(event.remote_jid),
            });
            logger.error("[Baileys inbound] Configuracao incompleta; evento nao encaminhado.");
            stats.dropped += 1;
            return false;
        }
        if (!event.event_id || knownEvents.has(event.event_id)) {
            stats.duplicate += 1;
            logMarker(logger, "WA_INBOUND_IGNORED_REASON", {
                messageIdHash: shortHash(event.message_id), reason: "duplicate",
                messageType: event.message_type,
                senderMasked: maskPhone(event.remote_jid),
                senderKind: jidKind(event.remote_jid),
                duplicate: true,
            });
            return false;
        }
        if (queue.length >= maxQueue) {
            logMarker(logger, "WA_AUTOREPLY_DECISION", {
                messageIdHash: shortHash(event.message_id), decision: "blocked", reason: "queue_full",
                messageType: event.message_type,
                senderMasked: maskPhone(event.remote_jid),
                senderKind: jidKind(event.remote_jid),
            });
            logger.error("[Baileys inbound] Fila em memoria cheia; evento nao encaminhado.");
            stats.dropped += 1;
            return false;
        }
        logMarker(logger, "WA_INBOUND_ELIGIBLE", {
            messageIdHash: shortHash(event.message_id),
            inboundAllowed: true,
            duplicate: false,
            senderKind: jidKind(event.remote_jid),
            senderMasked: maskPhone(event.remote_jid),
            messageType: event.message_type,
            hasText: !!String(event.text || "").trim(),
        });
        logMarker(logger, "WA_AUTOREPLY_DECISION", {
            messageIdHash: shortHash(event.message_id),
            decision: String(event.text || "").trim() ? "reply" : "no_reply",
            reason: String(event.text || "").trim() ? "forward_backend" : "missing_text",
            outboundAllowed: true,
            mode,
            messageType: event.message_type,
            hasText: !!String(event.text || "").trim(),
            senderMasked: maskPhone(event.remote_jid),
            senderKind: jidKind(event.remote_jid),
        });
        knownEvents.set(event.event_id, false);
        queue.push(event);
        stats.queued += 1;
        void work();
        return true;
    }

    function handleUpsert(update) {
        const messages = update && Array.isArray(update.messages) ? update.messages : [];
        logMarker(logger, "WA_INBOUND_EVENT_RECEIVED", {
            eventType: update && update.type || "unknown", messageCount: messages.length,
        });
        for (const message of messages) {
            const meta = keyMetadata(message);
            logMarker(logger, "WA_INBOUND_EVENT_RECEIVED", {
                eventType: update && update.type || "unknown",
                messageIdHash: meta.messageIdHash,
                senderKind: meta.senderKind,
                senderMasked: meta.senderMasked,
                fromMe: meta.fromMe,
                hasRemoteJidAlt: meta.hasRemoteJidAlt,
            });
            const event = buildInboundEvent(message, instance, options.now);
            if (!event) {
                logMarker(logger, "WA_INBOUND_IGNORED_REASON", {
                    messageIdHash: meta.messageIdHash,
                    reason: message && message.key ? "missing_message" : "missing_key",
                    senderKind: meta.senderKind,
                    senderMasked: meta.senderMasked,
                    fromMe: meta.fromMe,
                    hasRemoteJidAlt: meta.hasRemoteJidAlt,
                    messageType: "unknown",
                });
                continue;
            }
            logMarker(logger, "WA_INBOUND_NORMALIZED", {
                messageIdHash: shortHash(event.message_id),
                senderKind: meta.selectedKind,
                senderMasked: maskPhone(event.remote_jid),
                hasRemoteJidAlt: meta.hasRemoteJidAlt,
                normalized: true,
                messageType: event.message_type,
                fromMe: event.from_me,
                hasText: !!String(event.text || "").trim(),
            });
            if (event) enqueue(event);
        }
    }

    return {
        enabled, mode, enqueue, handleUpsert, isSandboxAllowed,
        drain: () => drainPromise, stats, queueLength: () => queue.length,
    };
}

function installInboundListener(sock, forwarder) {
    if (!sock || !sock.ev || INSTALLED_SOCKETS.has(sock)) return false;
    INSTALLED_SOCKETS.add(sock);
    sock.ev.on("messages.upsert", forwarder.handleUpsert);
    return true;
}

module.exports = {
    buildInboundEvent, createInboundForwarder, installInboundListener,
    individualJid, isEnabled, jidKind, keyMetadata, maskPhone, messageTypeAndText, normalizePhone, parseSandboxNumbers, phoneAliases,
    shortHash,
    timestampIso, validateLocalUrl,
};
