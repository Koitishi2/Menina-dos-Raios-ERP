"use strict";

const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const {
    exactVersion,
    fetchRegistryVersions,
    launchApprovedUpdate,
    readVersionState,
    validateUpdateScript,
} = require("../../baileys-api/maintenance");

const root = fs.mkdtempSync(path.join(os.tmpdir(), "baileys-maintenance-"));
fs.mkdirSync(path.join(root, "node_modules", "@whiskeysockets", "baileys"), { recursive: true });
fs.writeFileSync(path.join(root, "package.json"), JSON.stringify({ dependencies: { "@whiskeysockets/baileys": "6.7.24" } }));
fs.writeFileSync(path.join(root, "node_modules", "@whiskeysockets", "baileys", "package.json"), JSON.stringify({ version: "6.7.23" }));
const statusFile = path.join(root, "status.json");
fs.writeFileSync(statusFile, JSON.stringify({ status: "success", detail: "ok" }));

const state = readVersionState(root, { statusFile });
assert.strictEqual(state.installed_version, "6.7.23");
assert.strictEqual(state.approved_version, "6.7.24");
assert.strictEqual(state.update_available, true);
assert.strictEqual(state.can_update, true);
assert.strictEqual(state.update_status, "success");
assert.strictEqual(exactVersion("^6.7.24"), "");
assert.strictEqual(exactVersion("6.7.24"), "6.7.24");

fs.writeFileSync(path.join(root, "node_modules", "@whiskeysockets", "baileys", "package.json"), JSON.stringify({ version: "6.7.24" }));
const currentState = readVersionState(root, { statusFile });
assert.strictEqual(currentState.update_available, false);
assert.strictEqual(currentState.can_update, false);

const registryRequest = (_url, _options, callback) => {
    const handlers = {};
    const response = {
        statusCode: 200,
        setEncoding() {},
        on(name, handler) { handlers[name] = handler; },
    };
    callback(response);
    process.nextTick(() => {
        handlers.data(JSON.stringify({ "dist-tags": { latest: "7.0.0-rc14", legacy: "6.7.24" } }));
        handlers.end();
    });
    return { setTimeout() {}, on() {} };
};

assert.throws(
    () => validateUpdateScript("/unsafe", { lstat: () => ({ isFile: () => false, isSymbolicLink: () => false }) }),
    /update_script_invalido/,
);

let spawnCall = null;
const child = { unrefCalled: false, unref() { this.unrefCalled = true; } };
const launched = launchApprovedUpdate({
    scriptPath: "/opt/menina/baileys-api/update-baileys-safe.sh",
    lstat: () => ({ isFile: () => true, isSymbolicLink: () => false, uid: 0, mode: 0o100644 }),
    spawn(command, args, options) {
        spawnCall = { command, args, options };
        return child;
    },
});
assert.strictEqual(launched.accepted, true);
assert.strictEqual(spawnCall.command, "/usr/bin/systemd-run");
assert.deepStrictEqual(spawnCall.args.slice(-2), ["/bin/bash", "/opt/menina/baileys-api/update-baileys-safe.sh"]);
assert.strictEqual(spawnCall.options.detached, true);
assert.strictEqual(child.unrefCalled, true);

fetchRegistryVersions({ request: registryRequest }).then((versions) => {
    assert.deepStrictEqual(versions, { latest: "7.0.0-rc14", legacy: "6.7.24" });
    fs.rmSync(root, { recursive: true, force: true });
    console.log("baileys maintenance: OK");
});
