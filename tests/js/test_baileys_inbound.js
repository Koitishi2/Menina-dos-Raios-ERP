"use strict";

const assert = require("assert");
const { buildInboundEvent, createInboundForwarder, installInboundListener, validateLocalUrl } = require("../../baileys-api/inbound");

async function main() {
  assert.throws(() => validateLocalUrl("https://example.com/internal/whatsapp/events"), /loopback/);
  const event = buildInboundEvent({
    key: { id: "msg-1", remoteJid: "5595991234567@s.whatsapp.net", fromMe: false },
    message: { conversation: "Oi" }, messageTimestamp: 1000
  }, "raios-primary");
  assert.strictEqual(event.message_type, "conversation");
  assert.strictEqual(event.text, "Oi");
  assert.strictEqual(event.timestamp, "1970-01-01T00:16:40.000Z");

  const calls = [], waits = [], errors = [];
  const forwarder = createInboundForwarder({
    enabled: "true", instance: "raios-primary", token: "secret",
    fetch: async (_url, options) => {
      calls.push(JSON.parse(options.body));
      return { ok: calls.length >= 3, status: calls.length >= 3 ? 200 : 503 };
    },
    sleep: async (ms) => { waits.push(ms); },
    logger: { error: (message) => errors.push(message) }, maxAttempts: 3
  });
  forwarder.handleUpsert({ messages: [{ key: { id: "msg-2", remoteJid: "120@g.us" }, message: { protocolMessage: {} }, messageTimestamp: 1001 }] });
  await forwarder.drain();
  assert.strictEqual(calls.length, 3);
  assert.deepStrictEqual(waits, [500, 1000]);
  assert.strictEqual(forwarder.stats.forwarded, 1);
  assert.strictEqual(errors.length, 0);

  const disabledCalls = [];
  const disabled = createInboundForwarder({ enabled: "false", instance: "x", token: "y", fetch: async () => disabledCalls.push(1) });
  disabled.handleUpsert({ messages: [{ key: { id: "x", remoteJid: "1@s.whatsapp.net" }, message: { conversation: "x" } }] });
  await disabled.drain();
  assert.deepStrictEqual(disabledCalls, []);

  let handler;
  const sock = { ev: { on: (name, callback) => { assert.strictEqual(name, "messages.upsert"); handler = callback; } } };
  assert.strictEqual(installInboundListener(sock, disabled), true);
  assert.strictEqual(installInboundListener(sock, disabled), false);
  assert.strictEqual(typeof handler, "function");

  const failingCalls = [];
  const failing = createInboundForwarder({
    enabled: "true", instance: "x", token: "y", maxAttempts: 3,
    fetch: async () => { failingCalls.push(1); throw new Error("offline"); }, sleep: async () => {},
    logger: { error: (message) => errors.push(message) }
  });
  failing.enqueue(event); await failing.drain();
  assert.strictEqual(failingCalls.length, 3);
  assert.strictEqual(failing.stats.failed, 1);
  assert.ok(errors[0].includes("3 tentativa"));

  let nonRetryCalls = 0;
  const nonRetry = createInboundForwarder({
    enabled: "true", instance: "x", token: "y", maxAttempts: 3,
    fetch: async () => { nonRetryCalls += 1; return { ok: false, status: 422 }; },
    sleep: async () => { throw new Error("must not retry 4xx"); }, logger: { error: () => {} }
  });
  nonRetry.enqueue(event); await nonRetry.drain();
  assert.strictEqual(nonRetryCalls, 1);
  console.log("Baileys inbound harness: OK");
}

main().catch((error) => { console.error(error); process.exit(1); });
