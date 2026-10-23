from dataclasses import dataclass, field
from typing import Optional


CONVERSATION_STATES = (
    "nova",
    "aguardando_resposta",
    "identificando_produto",
    "coletando_quantidade",
    "coletando_avaria",
    "calculando_reposicao",
    "aguardando_confirmacao",
    "pedido_rascunho",
    "aguardando_aprovacao",
    "concluida",
    "cancelada",
    "atendimento_humano",
    "opt_out",
)

ORDER_STATES = (
    "rascunho",
    "aguardando_confirmacao",
    "aguardando_aprovacao",
    "aprovado",
    "cancelado",
    "convertido_em_venda",
    "erro",
    "duplicado_suspeito",
)

CONSENT_STATES = ("desconhecido", "opt_in", "opt_out", "pausado")

WHATSAPP_PERMISSIONS = (
    "whatsapp.view",
    "whatsapp.view_messages",
    "whatsapp.view_suggestions",
    "whatsapp.create_manual_batch",
    "whatsapp.send_manual",
    "whatsapp.manage_connection",
    "whatsapp.send",
    "whatsapp.manage_consent",
    "whatsapp.manage_consumption",
    "whatsapp.manage_damage",
    "whatsapp.view_orders",
    "whatsapp.approve_order",
    "whatsapp.convert_order",
    "whatsapp.view_audit",
)


@dataclass(frozen=True)
class IncomingMessageContract:
    company_key: str
    external_message_id: str
    jid: str
    received_at: str
    text: str
    event_hash: str


@dataclass(frozen=True)
class ConversationContract:
    id: str
    company_key: str
    client_id: str
    contact_id: str
    state: str = "nova"
    assigned_user_id: Optional[str] = None


@dataclass(frozen=True)
class OrderDraftContract:
    id: str
    company_key: str
    client_id: str
    conversation_id: str
    source_message_id: str
    idempotency_key: str
    state: str = "rascunho"
    flags: tuple[str, ...] = field(default_factory=tuple)


def is_conversation_state(value: str) -> bool:
    return value in CONVERSATION_STATES


def is_order_state(value: str) -> bool:
    return value in ORDER_STATES
