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

module.exports = { authorizeApiKey, authorizeLegacySend, constantTimeEqual, enabled };
