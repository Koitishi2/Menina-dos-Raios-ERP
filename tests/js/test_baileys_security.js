"use strict";

const assert = require("assert");
const { authorizeApiKey, authorizeLegacySend, authorizeOutboundSend, constantTimeEqual } = require("../../baileys-api/security");

assert.strictEqual(constantTimeEqual("local-test-key", "local-test-key"), true);
assert.strictEqual(constantTimeEqual("local-test-key", "wrong"), false);
assert.deepStrictEqual(authorizeApiKey("", "anything"), { ok: false, status: 503, code: "api_key_not_configured" });
assert.deepStrictEqual(authorizeApiKey("   ", "anything"), { ok: false, status: 503, code: "api_key_not_configured" });
assert.deepStrictEqual(authorizeApiKey("local-test-key", ""), { ok: false, status: 401, code: "unauthorized" });
assert.deepStrictEqual(authorizeApiKey("local-test-key", "wrong"), { ok: false, status: 401, code: "unauthorized" });
assert.deepStrictEqual(authorizeLegacySend("local-test-key", "local-test-key", "false"), { ok: false, status: 503, code: "outbound_disabled" });
assert.deepStrictEqual(authorizeLegacySend("local-test-key", "local-test-key", "true"), { ok: true });
assert.deepStrictEqual(authorizeOutboundSend({
  configuredKey: "local-test-key", providedKey: "local-test-key", outboundEnabled: "true",
  mode: "sandbox", sandboxNumbers: "+5521984261686", phone: "+5521984261686", hasTrustedJid: true
}), { ok: true });
assert.deepStrictEqual(authorizeOutboundSend({
  configuredKey: "local-test-key", providedKey: "local-test-key", outboundEnabled: "true",
  mode: "sandbox", sandboxNumbers: "+5521984261686", phone: "+559591505239", hasTrustedJid: true
}), { ok: false, status: 403, code: "sandbox_number_not_allowed" });
assert.deepStrictEqual(authorizeOutboundSend({
  configuredKey: "local-test-key", providedKey: "local-test-key", outboundEnabled: "true",
  mode: "sandbox", sandboxNumbers: "+5521984261686", phone: "+5521984261686", hasTrustedJid: false
}), { ok: false, status: 409, code: "outbound_route_unverified" });
assert.deepStrictEqual(authorizeOutboundSend({
  configuredKey: "local-test-key", providedKey: "local-test-key", outboundEnabled: "true",
  mode: "production", productionApproved: "false", phone: "+5521984261686"
}), { ok: false, status: 503, code: "production_not_approved" });

console.log("Baileys legacy send security harness: OK");
