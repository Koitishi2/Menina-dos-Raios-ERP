(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ClientWhatsAppFoundation = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";
  let conversations = [], suggestions = [], status = {}, currentBatch = null;
  let batchRequestSignature = "", batchRequestId = "";

  function createRequestId() {
    if (root.crypto && typeof root.crypto.randomUUID === "function") return root.crypto.randomUUID();
    return "batch-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
  }

  function batchRequestFor(signature) {
    const next = String(signature || "");
    if (!batchRequestId || batchRequestSignature !== next) {
      batchRequestSignature = next;
      batchRequestId = createRequestId();
    }
    return batchRequestId;
  }

  function resetBatchRequest() { batchRequestSignature = ""; batchRequestId = ""; }

  function normalizePhone(value) {
    let digits = String(value || "").replace(/\D/g, "");
    if (digits.startsWith("00")) digits = digits.slice(2);
    if (digits.length === 10 || digits.length === 11) digits = "55" + digits;
    const valid = digits.startsWith("55") && (digits.length === 12 || digits.length === 13)
      && digits.slice(2, 4)[0] !== "0" && !["0", "1"].includes(digits.slice(4, 5));
    return { digits, valid, e164: valid ? "+" + digits : "", reason: !digits ? "Telefone ausente" : (valid ? "" : "Telefone invalido") };
  }

  function createSelectionModel() {
    let revision = "";
    const ids = new Set();
    return {
      reset(nextRevision) { revision = String(nextRevision || ""); ids.clear(); },
      toggle(id, checked, currentRevision) {
        if (String(currentRevision || "") !== revision) this.reset(currentRevision);
        if (checked) ids.add(String(id)); else ids.delete(String(id));
      },
      select(items, currentRevision) {
        if (String(currentRevision || "") !== revision) this.reset(currentRevision);
        (items || []).filter((item) => item.selectable).forEach((item) => ids.add(String(item.client_id)));
      },
      remove(id) { ids.delete(String(id)); },
      values() { return Array.from(ids); },
      size() { return ids.size; },
      revision() { return revision; }
    };
  }

  const selection = createSelectionModel();
  function escapeHtml(value) { return String(value == null ? "" : value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); }
  function maskPhone(value) { const text = String(value || ""); return text.length > 7 ? text.slice(0, 5) + "****" + text.slice(-4) : text; }

  function showNotice(message, type) {
    const notice = root.document && root.document.getElementById("client-wa-notice");
    if (!notice) return;
    notice.style.display = "flex";
    notice.className = "client-wa-notice" + (type === "info" ? " is-info" : "");
    notice.innerHTML = '<span>' + escapeHtml(message || "Nao foi possivel concluir a operacao.") + '</span><button type="button" data-wa-dismiss-notice aria-label="Fechar aviso">Fechar</button>';
  }

  function hideNotice() {
    const notice = root.document && root.document.getElementById("client-wa-notice");
    if (notice) notice.style.display = "none";
  }

  function batchResultRows(batch) {
    return ((batch && batch.items) || []).map(function (item) {
      const statusValue = String(item.status || "pendente").toLowerCase();
      const statusClass = statusValue === "enviado" ? "is-success" : (statusValue === "falhou" ? "is-error" : "is-attention");
      return {
        id: String(item.id || "").slice(-8), client: String(item.client_name || "Cliente"), phone: maskPhone(item.phone_e164 || ""),
        status: statusValue, statusClass: statusClass, reason: String(item.result_detail || item.result_code || item.suggestion_reason || "Sem detalhe"),
        sentAt: String(item.sent_at || item.updated_at || "")
      };
    });
  }

  function renderBatchPreview(batch, heading) {
    const preview = root.document && root.document.getElementById("client-wa-batch-preview");
    if (!preview) return;
    const rows = batchResultRows(batch);
    preview.style.display = "block";
    preview.innerHTML = '<div class="client-wa-detail-head"><strong>' + escapeHtml(heading || "Resultado individual") + ' · ' + rows.length + ' cliente(s)</strong></div>' + rows.map(function (row) {
      return '<div class="client-wa-result"><span><strong>' + escapeHtml(row.client) + '</strong><small>' + escapeHtml(row.phone) + ' · ID ' + escapeHtml(row.id) + '</small></span>'
        + '<span class="client-wa-result-status ' + row.statusClass + '">' + escapeHtml(row.status) + '</span><span><small>' + escapeHtml(row.reason) + '</small><small>' + escapeHtml(row.sentAt) + '</small></span></div>';
    }).join("");
  }

  function buildRows(clients, conversationRows) {
    const byClient = {};
    (conversationRows || []).forEach(function (item) { if (!byClient[item.client_id]) byClient[item.client_id] = item; });
    return (Array.isArray(clients) ? clients : []).map(function (client) {
      const phone = normalizePhone(client.phone), conversation = byClient[String(client.id || "")] || null;
      return {
        id: String(client.id || ""), name: String(client.name || "Cliente"), originalPhone: String(client.phone || ""),
        normalizedPhone: phone.e164, phoneValid: phone.valid, phoneReason: phone.reason,
        consent: conversation && conversation.consent_status ? conversation.consent_status : "nao_configurado",
        conversation: conversation ? conversation.status : "sem_conversa",
        conversationId: conversation ? conversation.id : "", pendingOrder: false
      };
    });
  }

  function render(clients, conversationRows) {
    const body = root.document && root.document.getElementById("client-whatsapp-list");
    const summary = root.document && root.document.getElementById("client-whatsapp-summary");
    if (!body) return;
    const rows = buildRows(clients, conversationRows || conversations), valid = rows.filter((row) => row.phoneValid);
    if (summary) summary.textContent = valid.length + " cliente(s) com telefone valido de " + rows.length + " cadastrado(s)";
    if (!rows.length) { body.innerHTML = '<div class="client-wa-empty">Nenhum cliente cadastrado nesta empresa.</div>'; return; }
    body.innerHTML = rows.map(function (row) {
      const phone = row.phoneValid ? row.normalizedPhone : (row.phoneReason || "Telefone invalido");
      return '<div class="client-wa-row"><div class="client-wa-identity"><strong>' + escapeHtml(row.name) + '</strong><span>' + escapeHtml(phone) + '</span></div>'
        + '<span class="client-wa-tag ' + (row.phoneValid ? "is-ready" : "is-warning") + '">' + (row.phoneValid ? "Telefone pronto" : "Revisar telefone") + '</span>'
        + '<span class="client-wa-tag">' + escapeHtml(row.consent.replace(/_/g, " ")) + '</span><span class="client-wa-muted">' + escapeHtml(row.conversation.replace(/_/g, " ")) + '</span>'
        + '<button type="button" class="btn btn-secondary btn-sm" data-wa-conversation="' + escapeHtml(row.conversationId) + '" ' + (row.conversationId ? "" : "disabled") + '>Abrir conversa</button></div>';
    }).join("");
  }

  function suggestionRevision() {
    const days = root.document.getElementById("client-wa-min-days"), blocked = root.document.getElementById("client-wa-include-blocked");
    return JSON.stringify({ days: days ? days.value : "8", blocked: !!(blocked && blocked.checked), ids: suggestions.map((row) => row.client_id) });
  }
  function updateSelectedCount() { const el = root.document.getElementById("client-wa-selected-count"); if (el) el.textContent = selection.size() + " selecionado(s)"; }

  function renderSuggestions() {
    const body = root.document.getElementById("client-wa-suggestions");
    if (!body) return;
    if (!suggestions.length) { body.innerHTML = '<div class="client-wa-empty">Nenhum cliente encontrado para estes filtros.</div>'; updateSelectedCount(); return; }
    body.innerHTML = suggestions.map(function (row) {
      const reasons = row.selectable ? row.suggestion_reason : (row.block_reasons || []).join(", ");
      return '<label class="client-wa-suggestion ' + (row.selectable ? "" : "is-blocked") + '"><input type="checkbox" data-wa-select="' + escapeHtml(row.client_id) + '" '
        + (selection.values().includes(String(row.client_id)) ? "checked " : "") + (row.selectable ? "" : "disabled") + '><span><strong>' + escapeHtml(row.client_name) + '</strong><small>'
        + escapeHtml(maskPhone(row.phone_e164 || "Telefone invalido")) + ' · ' + escapeHtml(row.consent) + '</small></span><span><strong>'
        + escapeHtml(row.days_without_purchase == null ? "Sem historico" : row.days_without_purchase + " dias") + '</strong><small>' + escapeHtml(reasons || "") + '</small></span></label>';
    }).join("");
    updateSelectedCount();
  }

  function renderInboundEvents(events) {
    const body = root.document.getElementById("client-wa-inbound-events");
    if (!body) return;
    if (!events.length) { body.innerHTML = '<div class="client-wa-empty">Nenhum evento recebido.</div>'; return; }
    body.innerHTML = events.map(function (event) {
      return '<div class="client-wa-event"><span class="client-wa-tag ' + (event.processing_status === "processado" ? "is-ready" : "is-warning") + '">' + escapeHtml(event.processing_status) + '</span><div><strong>'
        + escapeHtml(event.client_name || "Cliente nao identificado") + '</strong><small>' + escapeHtml(maskPhone(event.phone_e164 || event.jid)) + ' · ' + escapeHtml(event.message_type) + '</small></div><div><span>'
        + escapeHtml(event.body_preview || event.error_code || "Sem conteudo") + '</span><small>Duplicidades bloqueadas: ' + Number(event.duplicate_count || 0) + '</small></div></div>';
    }).join("");
  }

  function renderIntegration() {
    const mode = root.document.getElementById("client-whatsapp-mode"), detail = root.document.getElementById("client-whatsapp-integration");
    if (mode) mode.textContent = status.inbound_enabled ? "Recebimento WhatsApp ativo" : "Recebimento WhatsApp desativado";
    if (detail) detail.textContent = "Entrada: " + (status.inbound_enabled ? "ativa" : "desativada") + " · Saida: " + (status.outbound_mode || "disabled");
    const send = root.document.getElementById("client-wa-send-selected");
    const outboundAvailable = !!(status.outbound_enabled && status.outbound_mode !== "disabled");
    if (send) {
      send.disabled = !(currentBatch && outboundAvailable && status.capabilities && status.capabilities.send_manual);
      send.textContent = outboundAvailable ? "Enviar para clientes selecionados" : "Envio desativado neste ambiente";
    }
    const batchStatus = root.document.getElementById("client-wa-batch-status");
    if (batchStatus && !outboundAvailable) batchStatus.textContent = "Envio desativado neste ambiente.";
    const campaign = root.document.getElementById("client-wa-manual-campaign");
    if (campaign) campaign.style.display = status.capabilities && status.capabilities.view_suggestions ? "" : "none";
  }

  async function reloadSuggestions() {
    const days = root.document.getElementById("client-wa-min-days"), blocked = root.document.getElementById("client-wa-include-blocked");
    const query = "?minimum_days=" + encodeURIComponent(days ? days.value : "8") + "&include_blocked=" + (!!(blocked && blocked.checked));
    suggestions = await root.api("/api/whatsapp/suggestions" + query);
    selection.reset(suggestionRevision()); currentBatch = null; resetBatchRequest(); renderSuggestions(); renderIntegration();
  }

  async function load(clients) {
    try {
      status = await root.api("/api/whatsapp/status");
      const requests = [root.api("/api/whatsapp/conversations"), root.api("/api/whatsapp/inbound-events")];
      if (status.capabilities && status.capabilities.view_suggestions) requests.push(root.api("/api/whatsapp/suggestions?minimum_days=8&include_blocked=false"));
      const result = await Promise.all(requests);
      conversations = result[0]; suggestions = result[2] || []; selection.reset(suggestionRevision()); currentBatch = null; resetBatchRequest();
      render(clients, conversations); renderInboundEvents(result[1]); renderSuggestions(); renderIntegration();
    } catch (error) {
      conversations = []; render(clients, []); const summary = root.document.getElementById("client-whatsapp-summary"); if (summary) summary.textContent = error.message;
    }
  }

  function selectFiltered() { selection.select(suggestions, suggestionRevision()); renderSuggestions(); currentBatch = null; resetBatchRequest(); renderIntegration(); }
  function clearSelection() { selection.reset(suggestionRevision()); renderSuggestions(); currentBatch = null; resetBatchRequest(); renderIntegration(); }

  async function prepareBatch() {
    hideNotice();
    try {
      const message = root.document.getElementById("client-wa-message");
      if (!selection.size()) throw new Error("Selecione ao menos um cliente.");
      const payload = { client_ids: selection.values(), message: message ? message.value : "", filters: { revision: suggestionRevision() } };
      payload.request_id = batchRequestFor(JSON.stringify(payload));
      currentBatch = await root.api("/api/whatsapp/manual-batches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      renderBatchPreview(currentBatch, "Previa do lote");
      const batchStatus = root.document.getElementById("client-wa-batch-status");
      if (batchStatus) batchStatus.textContent = "Lote preparado. Revise antes da confirmacao explicita.";
      renderIntegration();
      return currentBatch;
    } catch (error) {
      currentBatch = null; renderIntegration(); showNotice(error && error.message, "error"); return null;
    }
  }

  async function confirmAndSend() {
    if (!currentBatch || !root.confirm("Confirmar envio somente para os clientes selecionados neste lote?")) return;
    hideNotice();
    try {
      await root.api("/api/whatsapp/manual-batches/" + encodeURIComponent(currentBatch.id) + "/confirm", { method: "POST" });
      const result = await root.api("/api/whatsapp/manual-batches/" + encodeURIComponent(currentBatch.id) + "/send", { method: "POST" });
      currentBatch = result.batch;
      renderBatchPreview(currentBatch, "Resultado individual do lote");
      const batchStatus = root.document.getElementById("client-wa-batch-status"); if (batchStatus) batchStatus.textContent = "Lote concluido. Confira cada resultado abaixo.";
      showNotice("Processamento concluido sem repeticao automatica.", "info"); renderIntegration(); return result;
    } catch (error) {
      showNotice(error && error.message, "error"); renderIntegration(); return null;
    }
  }

  async function openConversation(id) {
    if (!id) return;
    const detail = root.document.getElementById("client-whatsapp-detail"); if (!detail) return;
    try {
      const item = await root.api("/api/whatsapp/conversations/" + encodeURIComponent(id)); detail.style.display = "block";
      detail.innerHTML = '<div class="client-wa-detail-head"><strong>' + escapeHtml(item.client_name || "Conversa") + '</strong><button class="btn btn-secondary btn-sm" data-wa-close>Fechar</button></div>' + ((item.messages || []).length ? item.messages.map(function (message) { return '<div class="client-wa-message"><strong>Mensagem ' + escapeHtml(message.direction) + '</strong><span>' + escapeHtml(message.created_at || "") + ' · ' + escapeHtml(message.status || "") + '</span><div>' + escapeHtml(message.body || "") + '</div></div>'; }).join("") : '<div class="client-wa-empty">Nenhuma mensagem registrada.</div>');
    } catch (error) { detail.style.display = "block"; detail.textContent = error.message; }
  }

  if (root.document) root.document.addEventListener("change", function (event) {
    const input = event.target.closest && event.target.closest("[data-wa-select]");
    if (input) { selection.toggle(input.dataset.waSelect, input.checked, suggestionRevision()); currentBatch = null; resetBatchRequest(); updateSelectedCount(); renderIntegration(); }
  });
  if (root.document) root.document.addEventListener("click", function (event) {
    const open = event.target.closest && event.target.closest("[data-wa-conversation]"); if (open) openConversation(open.dataset.waConversation);
    if (event.target.closest && event.target.closest("[data-wa-close]")) root.document.getElementById("client-whatsapp-detail").style.display = "none";
    if (event.target.closest && event.target.closest("[data-wa-dismiss-notice]")) hideNotice();
  });

  return { normalizePhone, createSelectionModel, buildRows, batchResultRows, batchRequestFor, resetBatchRequest, renderBatchPreview, showNotice, hideNotice, render, load, openConversation, reloadSuggestions, selectFiltered, clearSelection, prepareBatch, confirmAndSend };
});
