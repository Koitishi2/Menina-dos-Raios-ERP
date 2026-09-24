"use strict";

const crypto = require("crypto");

function enabled(value) {
    return ["1", "true", "yes", "on"].includes(String(value || "").trim().toLowerCase());
}

function constantTimeEqual(expected, received) {
    const left = Buffer.from(String(expected || ""), "utf8");
    const right = Buffer.from(String(received || ""), "utf8");
    if (!left.length || left.length !== right.length) return false;
    return crypto.timingSafeEqual(left, right);
}

function authorizeApiKey(configuredKey, providedKey) {
    const configured = String(configuredKey || "").trim();
    if (!configured) return { ok: false, status: 503, code: "api_key_not_configured" };
    if (!constantTimeEqual(configured, providedKey)) return { ok: false, status: 401, code: "unauthorized" };
    return { ok: true };
}

function authorizeLegacySend(configuredKey, providedKey, outboundEnabled) {
    const auth = authorizeApiKey(configuredKey, providedKey);
    if (!auth.ok) return auth;
    if (!enabled(outboundEnabled)) return { ok: false, status: 503, code: "outbound_disabled" };
    return { ok: true };
}

function normalizePhone(value) {
    return String(value || "").split("@")[0].split(":")[0].replace(/\D/g, "");
}

function phoneAliases(value) {
    const phone = normalizePhone(value);
    const aliases = new Set(phone ? [phone] : []);
    if (/^55\d{11}$/.test(phone) && phone[4] === "9") {
        aliases.add(`${phone.slice(0, 4)}${phone.slice(5)}`);
    } else if (/^55\d{10}$/.test(phone)) {
        aliases.add(`${phone.slice(0, 4)}9${phone.slice(4)}`);
    }
    return aliases;
}

function authorizeOutboundSend(options = {}) {
    const auth = authorizeApiKey(options.configuredKey, options.providedKey);
    if (!auth.ok) return auth;
    if (!enabled(options.outboundEnabled)) return { ok: false, status: 503, code: "outbound_disabled" };

    const mode = String(options.mode || "disabled").trim().toLowerCase();
    if (mode === "sandbox") {
        const allowed = new Set();
        for (const entry of String(options.sandboxNumbers || "").split(",")) {
            for (const phone of phoneAliases(entry)) allowed.add(phone);
        }
        const authorized = [...phoneAliases(options.phone)].some((phone) => allowed.has(phone));
        if (!authorized) return { ok: false, status: 403, code: "sandbox_number_not_allowed" };
        if (!options.hasTrustedJid) return { ok: false, status: 409, code: "outbound_route_unverified" };
        return { ok: true };
    }
    if (mode === "production") {
        if (!enabled(options.productionApproved)) return { ok: false, status: 503, code: "production_not_approved" };
        return { ok: true };
    }
    return { ok: false, status: 503, code: "outbound_mode_disabled" };
}

module.exports = { authorizeApiKey, authorizeLegacySend, authorizeOutboundSend, constantTimeEqual, enabled, normalizePhone, phoneAliases };
