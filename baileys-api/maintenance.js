"use strict";

const fs = require("fs");
const path = require("path");
const https = require("https");
const { spawn } = require("child_process");

const PACKAGE_NAME = "@whiskeysockets/baileys";
const REGISTRY_URL = "https://registry.npmjs.org/@whiskeysockets%2fbaileys";
const DEFAULT_UPDATE_SCRIPT = "/opt/menina/baileys-api/update-baileys-safe.sh";
const DEFAULT_STATUS_FILE = "/run/menina-baileys-update-status.json";

function exactVersion(value) {
    const version = String(value || "").trim();
    return /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(version) ? version : "";
}

function readJson(filePath, fallback = {}) {
    try { return JSON.parse(fs.readFileSync(filePath, "utf8")); }
    catch (_) { return fallback; }
}

function readVersionState(baseDir, options = {}) {
    const packageJson = readJson(path.join(baseDir, "package.json"));
    const approved = exactVersion((packageJson.dependencies || {})[PACKAGE_NAME]);
    const installedJson = readJson(path.join(baseDir, "node_modules", "@whiskeysockets", "baileys", "package.json"));
    const installed = exactVersion(installedJson.version);
    const updateStatus = readJson(options.statusFile || DEFAULT_STATUS_FILE, {});
    return {
        installed_version: installed || null,
        approved_version: approved || null,
        update_available: Boolean(approved && installed !== approved),
        can_update: Boolean(approved && installed !== approved),
        update_status: String(updateStatus.status || "idle"),
        update_detail: String(updateStatus.detail || "").slice(0, 300),
        update_started_at: updateStatus.started_at || null,
        update_finished_at: updateStatus.finished_at || null,
    };
}

function fetchRegistryVersions(options = {}) {
    const request = options.request || https.get;
    const timeoutMs = Number(options.timeoutMs || 5000);
    return new Promise((resolve) => {
        const req = request(REGISTRY_URL, { headers: { accept: "application/json", "user-agent": "menina-baileys" } }, (res) => {
            let body = "";
            res.setEncoding("utf8");
            res.on("data", (chunk) => { if (body.length < 100000) body += chunk; });
            res.on("end", () => {
                if (res.statusCode !== 200) return resolve({ latest: null, legacy: null });
                const tags = readJsonText(body)["dist-tags"] || {};
                resolve({
                    latest: exactVersion(tags.latest) || null,
                    legacy: exactVersion(tags.legacy) || null,
                });
            });
        });
        req.setTimeout(timeoutMs, () => req.destroy(new Error("registry_timeout")));
        req.on("error", () => resolve({ latest: null, legacy: null }));
    });
}

async function fetchLatestVersion(options = {}) {
    const versions = await fetchRegistryVersions(options);
    return versions.latest;
}

function readJsonText(text) {
    try { return JSON.parse(text); }
    catch (_) { return {}; }
}

function validateUpdateScript(scriptPath, options = {}) {
    const stat = (options.lstat || fs.lstatSync)(scriptPath);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error("update_script_invalido");
    if (process.platform !== "win32" && (stat.uid !== 0 || (stat.mode & 0o022) !== 0)) {
        throw new Error("update_script_permissoes_inseguras");
    }
    return true;
}

function launchApprovedUpdate(options = {}) {
    const scriptPath = options.scriptPath || DEFAULT_UPDATE_SCRIPT;
    validateUpdateScript(scriptPath, options);
    const unit = `menina-baileys-update-${Date.now()}`;
    const runner = options.spawn || spawn;
    const child = runner("/usr/bin/systemd-run", [
        `--unit=${unit}`, "--collect", "--property=Type=oneshot",
        "/bin/bash", scriptPath,
    ], { detached: true, stdio: "ignore" });
    child.unref();
    return { accepted: true, unit };
}

module.exports = {
    DEFAULT_STATUS_FILE,
    DEFAULT_UPDATE_SCRIPT,
    PACKAGE_NAME,
    REGISTRY_URL,
    exactVersion,
    fetchLatestVersion,
    fetchRegistryVersions,
    launchApprovedUpdate,
    readVersionState,
    validateUpdateScript,
};
