from decimal import Decimal
from pathlib import Path

import pytest

from backend.domains.whatsapp_policies import (
    baileys_readiness,
    campaign_eligibility,
    conversation_control_intent,
    duplicate_order_reasons,
    message_idempotency_key,
    normalize_brazil_phone,
    order_contract_issues,
    user_can,
)
from backend.domains.whatsapp_states import (
    CONSENT_STATES,
    CONVERSATION_STATES,
    ORDER_STATES,
    WHATSAPP_PERMISSIONS,
    ConversationContract,
    IncomingMessageContract,
    OrderDraftContract,
    is_conversation_state,
    is_order_state,
)
from backend.services.whatsapp_calculation_service import calculate_replenishment


ROOT = Path(__file__).resolve().parents[1]


def test_contract_states_and_models_are_stable():
    assert "opt_out" in CONVERSATION_STATES
    assert "duplicado_suspeito" in ORDER_STATES
    assert CONSENT_STATES == ("desconhecido", "opt_in", "opt_out", "pausado")
    assert is_conversation_state("atendimento_humano")
    assert not is_conversation_state("enviando")
    assert is_order_state("aguardando_aprovacao")
    assert not is_order_state("vendido")

    message = IncomingMessageContract("raios", "msg-1", "5595999999999@s.whatsapp.net", "2026-09-14T10:00:00Z", "Oi", "hash")
    conversation = ConversationContract("conv-1", "raios", "client-1", "contact-1")
    order = OrderDraftContract("order-1", "raios", "client-1", "conv-1", message.external_message_id, "key")
    assert conversation.state == "nova"
    assert order.state == "rascunho"
    assert order.flags == ()


@pytest.mark.parametrize(
    ("raw", "valid", "reason", "e164"),
    [
        ("", False, "telefone_ausente", ""),
        ("123", False, "pais_nao_suportado", ""),
        ("(95) 99123-4567", True, "", "+5595991234567"),
        ("005595991234567", True, "", "+5595991234567"),
    ],
)
def test_phone_normalization(raw, valid, reason, e164):
    result = normalize_brazil_phone(raw)
    assert result.valid is valid
    assert result.reason == reason
    assert result.e164 == e164


def test_control_commands_and_baileys_readiness():
    assert conversation_control_intent("sair") == "opt_out"
    assert conversation_control_intent("STOP") == "opt_out"
    assert conversation_control_intent("Falar com atendente") == "atendimento_humano"
    assert conversation_control_intent("Quero falar com um atendente, por favor") == "atendimento_humano"
    assert conversation_control_intent("quero comprar") is None
    assert baileys_readiness(False, True) == (False, "baileys_desconectado")
    assert baileys_readiness(False, False) == (False, "credenciais_ausentes")
    assert baileys_readiness(True, True, "timeout") == (False, "erro_conexao")
    assert baileys_readiness(True, True) == (True, "disponivel")


def test_message_idempotency_is_stable_and_company_scoped():
    args = ("raios", "msg-1", "5595999999999@s.whatsapp.net", "2026-09-14T10:00:00Z", {"text": "pedido"})
    first = message_idempotency_key(*args)
    assert first == message_idempotency_key(*args)
    assert first != message_idempotency_key("estrada", *args[1:])
    assert first != message_idempotency_key("raios", "msg-2", *args[2:])


def test_duplicate_order_and_contract_guards():
    assert duplicate_order_reasons(True, True, True, True, ["recent-1"]) == (
        "mensagem_processada",
        "pedido_aberto_na_conversa",
        "idempotency_key_repetida",
        "pedido_ja_confirmado",
        "pedido_recente_do_cliente",
    )
    assert order_contract_issues("raios", "", "", "estrada") == (
        "cliente_ausente",
        "conversa_ausente",
        "empresa_divergente",
    )
    assert order_contract_issues("raios", "client-1", "conv-1", "RAIOS") == ()


def test_campaign_boundary_and_permission_contract():
    assert campaign_eligibility(7, "opt_in") == (False, "intervalo_insuficiente")
    assert campaign_eligibility(8, "opt_in") == (True, "mais_de_7_dias_sem_compra")
    assert campaign_eligibility(30, "opt_out") == (False, "sem_consentimento")
    assert campaign_eligibility(30, "opt_in", has_open_conversation=True) == (False, "conversa_aberta")
    assert campaign_eligibility(30, "opt_in", has_pending_order=True) == (False, "pedido_pendente")
    assert "whatsapp.send_manual" in WHATSAPP_PERMISSIONS
    assert user_can("whatsapp.view", {"whatsapp.view"})
    assert not user_can("whatsapp.send", {"whatsapp.view"})


def test_replenishment_without_and_with_damage_and_maximum():
    no_damage = calculate_replenishment(10, 0, 100, 2)
    assert no_damage.suggested_quantity == Decimal("8")
    assert no_damage.maximum_consumption is None

    with_damage = calculate_replenishment(10, 2, 50, 0, maximum_consumption=15, requested_quantity=16)
    assert with_damage.damage_replacement == Decimal("1")
    assert with_damage.suggested_quantity == Decimal("11")
    assert with_damage.above_maximum is True
    assert "Quantidade sugerida: 11" in with_damage.calculation_memory

    depleted = calculate_replenishment(5, 0, 0, 10)
    assert depleted.suggested_quantity == Decimal("0")


@pytest.mark.parametrize("percent", [-1, 101, "invalido"])
def test_replenishment_rejects_invalid_percent(percent):
    with pytest.raises(ValueError):
        calculate_replenishment(10, 2, percent, 1)


def test_client_subtabs_expose_manual_selection_without_automatic_send():
    index = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    whatsapp_js = (ROOT / "backend" / "static" / "js" / "client_whatsapp.js").read_text(encoding="utf-8")
    orders_js = (ROOT / "backend" / "static" / "js" / "client_orders.js").read_text(encoding="utf-8")

    for expected in ("cv-btn-whatsapp", "cv-btn-pedidos", "cv-whatsapp", "cv-pedidos"):
        assert expected in index
    assert "Nenhuma resposta ou campanha é executada automaticamente." in index
    assert "Envio desativado neste ambiente" in index
    assert "Enviar para clientes selecionados" in whatsapp_js
    assert "WHATSAPP_OUTBOUND" not in index
    assert "Nenhum pedido será enviado, aprovado ou convertido em venda" in index
    assert "/api/whatsapp/manual-batches" in whatsapp_js
    assert "/api/whatsapp/send" not in whatsapp_js
    assert "fetch(" not in whatsapp_js
    assert "fetch(" not in orders_js
    app_source = (ROOT / "backend" / "app.py").read_text(encoding="utf-8")
    assert "threading.Thread(target=motivation_scheduler" not in app_source
