"use strict";

const assert = require("assert");
const { authorizeApiKey, authorizeLegacySend, constantTimeEqual } = require("../../baileys-api/security");

assert.strictEqual(constantTimeEqual("local-test-key", "local-test-key"), true);
assert.strictEqual(constantTimeEqual("local-test-key", "wrong"), false);
assert.deepStrictEqual(authorizeApiKey("", "anything"), { ok: false, status: 503, code: "api_key_not_configured" });
assert.deepStrictEqual(authorizeApiKey("   ", "anything"), { ok: false, status: 503, code: "api_key_not_configured" });
assert.deepStrictEqual(authorizeApiKey("local-test-key", ""), { ok: false, status: 401, code: "unauthorized" });
assert.deepStrictEqual(authorizeApiKey("local-test-key", "wrong"), { ok: false, status: 401, code: "unauthorized" });
assert.deepStrictEqual(authorizeLegacySend("local-test-key", "local-test-key", "false"), { ok: false, status: 503, code: "outbound_disabled" });
assert.deepStrictEqual(authorizeLegacySend("local-test-key", "local-test-key", "true"), { ok: true });

console.log("Baileys legacy send security harness: OK");
