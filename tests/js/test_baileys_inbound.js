"use strict";

const assert = require("assert");
const {
  buildInboundEvent, createInboundForwarder, installInboundListener,
  individualJid, normalizePhone, parseSandboxNumbers, phoneAliases, validateLocalUrl,
} = require("../../baileys-api/inbound");

async function main() {
  assert.throws(() => validateLocalUrl("https://example.com/internal/whatsapp/events"), /loopback/);
  const event = buildInboundEvent({
    key: { id: "msg-1", remoteJid: "5595991234567@s.whatsapp.net", fromMe: false },
    message: { conversation: "Oi" }, messageTimestamp: 1000
  }, "raios-primary");
  assert.strictEqual(event.message_type, "conversation");
  assert.strictEqual(event.text, "Oi");
  assert.strictEqual(event.timestamp, "1970-01-01T00:16:40.000Z");
  assert.strictEqual(normalizePhone("5595991234567:4@s.whatsapp.net"), "5595991234567");
  assert.deepStrictEqual([...parseSandboxNumbers("+55 (95) 99123-4567,invalid")], ["5595991234567", "559591234567"]);
  assert.deepStrictEqual([...phoneAliases("5521984261686")], ["5521984261686", "552184261686"]);
  assert.strictEqual(individualJid({ remoteJid: "123@lid", remoteJidAlt: "5521984261686@s.whatsapp.net" }), "5521984261686@s.whatsapp.net");
  const altEvent = buildInboundEvent({
    key: { id: "msg-alt", remoteJid: "123456@lid", remoteJidAlt: "5521984261686@s.whatsapp.net" },
    message: { conversation: "Oi alternativo" }, messageTimestamp: 1000,
  }, "raios-primary");
  assert.strictEqual(altEvent.remote_jid, "5521984261686@s.whatsapp.net");

  const calls = [], waits = [], errors = [];
  const forwarder = createInboundForwarder({
    enabled: "true", mode: "sandbox", sandboxNumbers: "5595991234567",
    instance: "raios-primary", token: "secret",
    fetch: async (_url, options) => {
      calls.push(JSON.parse(options.body));
      return { ok: calls.length >= 3, status: calls.length >= 3 ? 200 : 503 };
    },
    sleep: async (ms) => { waits.push(ms); },
    logger: { error: (message) => errors.push(message) }, maxAttempts: 3
  });
  forwarder.handleUpsert({ messages: [{ key: { id: "msg-2", remoteJid: "5595991234567@s.whatsapp.net" }, message: { conversation: "Pedido" }, messageTimestamp: 1001 }] });
  await forwarder.drain();
  assert.strictEqual(calls.length, 3);
  assert.deepStrictEqual(waits, [500, 1000]);
  assert.strictEqual(forwarder.stats.forwarded, 1);
  assert.strictEqual(errors.length, 0);

  const brazilLegacyCalls = [];
  const brazilLegacy = createInboundForwarder({
    enabled: "true", mode: "sandbox", sandboxNumbers: "5521984261686",
    instance: "raios-primary", token: "secret",
    fetch: async (_url, options) => { brazilLegacyCalls.push(JSON.parse(options.body)); return { ok: true, status: 200 }; },
  });
  brazilLegacy.handleUpsert({ messages: [{
    key: { id: "msg-br-legacy", remoteJid: "552184261686@s.whatsapp.net", fromMe: false },
    message: { conversation: "Oi legado" }, messageTimestamp: 1001,
  }] });
  await brazilLegacy.drain();
  assert.strictEqual(brazilLegacyCalls.length, 1);
  assert.strictEqual(brazilLegacy.stats.forwarded, 1);

  forwarder.handleUpsert({ messages: [{ key: { id: "msg-2", remoteJid: "5595991234567@s.whatsapp.net" }, message: { conversation: "Pedido repetido" }, messageTimestamp: 1002 }] });
  await forwarder.drain();
  assert.strictEqual(calls.length, 3);
  assert.strictEqual(forwarder.stats.duplicate, 1);

  for (const blockedMessage of [
    { key: { id: "other", remoteJid: "5595990000000@s.whatsapp.net" }, message: { conversation: "fora" } },
    { key: { id: "group", remoteJid: "120@g.us" }, message: { conversation: "grupo" } },
    { key: { id: "self", remoteJid: "5595991234567@s.whatsapp.net", fromMe: true }, message: { conversation: "propria" } },
  ]) forwarder.handleUpsert({ messages: [blockedMessage] });
  await forwarder.drain();
  assert.strictEqual(calls.length, 3);
  assert.strictEqual(forwarder.stats.filtered, 3);

  const failClosedCalls = [];
  for (const config of [
    { enabled: "true", mode: "disabled", sandboxNumbers: "5595991234567" },
    { enabled: "true", mode: "sandbox", sandboxNumbers: "" },
  ]) {
    const failClosed = createInboundForwarder({
      ...config, instance: "x", token: "y", fetch: async () => failClosedCalls.push(1),
    });
    failClosed.enqueue(event);
    await failClosed.drain();
    assert.strictEqual(failClosed.stats.filtered, 1);
  }
  assert.deepStrictEqual(failClosedCalls, []);

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
  let reconnectHandler;
  const reconnectedSock = { ev: { on: (_name, callback) => { reconnectHandler = callback; } } };
  assert.strictEqual(installInboundListener(reconnectedSock, disabled), true);
  assert.strictEqual(typeof reconnectHandler, "function");

  const incompleteCalls = [];
  const incomplete = createInboundForwarder({
    enabled: "true", mode: "sandbox", sandboxNumbers: "5595991234567",
    instance: "raios-primary", token: "", fetch: async () => incompleteCalls.push(1),
    logger: { error: (message) => errors.push(message) },
  });
  incomplete.enqueue(event);
  await incomplete.drain();
  assert.deepStrictEqual(incompleteCalls, []);
  assert.strictEqual(incomplete.stats.dropped, 1);
  assert.ok(errors.some((message) => message.includes("Configuracao incompleta")));

  const failingCalls = [];
  const failing = createInboundForwarder({
    enabled: "true", mode: "sandbox", sandboxNumbers: "5595991234567",
    instance: "x", token: "y", maxAttempts: 3,
    fetch: async () => { failingCalls.push(1); throw new Error("offline"); }, sleep: async () => {},
    logger: { error: (message) => errors.push(message) }
  });
  failing.enqueue(event); await failing.drain();
  assert.strictEqual(failingCalls.length, 3);
  assert.strictEqual(failing.stats.failed, 1);
  assert.ok(errors.some((message) => message.includes("3 tentativa")));
  failing.enqueue(event); await failing.drain();
  assert.strictEqual(failingCalls.length, 6);

  let nonRetryCalls = 0;
  const nonRetry = createInboundForwarder({
    enabled: "true", mode: "sandbox", sandboxNumbers: "5595991234567",
    instance: "x", token: "y", maxAttempts: 3,
    fetch: async () => { nonRetryCalls += 1; return { ok: false, status: 422 }; },
    sleep: async () => { throw new Error("must not retry 4xx"); }, logger: { error: () => {} }
  });
  nonRetry.enqueue(event); await nonRetry.drain();
  assert.strictEqual(nonRetryCalls, 1);
  console.log("Baileys inbound harness: OK");
}

main().catch((error) => { console.error(error); process.exit(1); });
