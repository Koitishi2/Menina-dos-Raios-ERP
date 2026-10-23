from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


@dataclass(frozen=True)
class ReplenishmentResult:
    average_consumption: Decimal
    maximum_consumption: Optional[Decimal]
    confirmed_damage: Decimal
    damage_replacement_percent: Decimal
    damage_replacement: Decimal
    informed_stock: Decimal
    need: Decimal
    suggested_quantity: Decimal
    requested_quantity: Optional[Decimal]
    above_maximum: bool
    calculation_memory: str


def _decimal(value, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalido") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{field}_invalido")
    return result


def calculate_replenishment(
    average_consumption,
    confirmed_damage,
    damage_replacement_percent,
    informed_stock,
    maximum_consumption=None,
    requested_quantity=None,
) -> ReplenishmentResult:
    average = _decimal(average_consumption, "consumo_medio")
    damage = _decimal(confirmed_damage, "avaria_confirmada")
    percent = _decimal(damage_replacement_percent, "percentual_reposicao")
    stock = _decimal(informed_stock, "estoque_informado")
    maximum = None if maximum_consumption in (None, "") else _decimal(maximum_consumption, "consumo_maximo")
    requested = None if requested_quantity in (None, "") else _decimal(requested_quantity, "quantidade_solicitada")
    if percent > Decimal("100"):
        raise ValueError("percentual_reposicao_invalido")
    if maximum is not None and maximum < average:
        raise ValueError("consumo_maximo_menor_que_medio")

    replacement = damage * percent / Decimal("100")
    need = average + replacement - stock
    non_negative_need = max(Decimal("0"), need)
    suggested = min(non_negative_need, maximum) if maximum is not None else non_negative_need
    above_maximum = maximum is not None and requested is not None and requested > maximum
    maximum_text = str(maximum) if maximum is not None else "sem limite configurado"
    memory = (
        f"Reposicao de avaria: {damage} x {percent}% = {replacement}; "
        f"Necessidade: {average} + {replacement} - {stock} = {need}; "
        f"Limite: {maximum_text}; Quantidade sugerida: {suggested}."
    )
    return ReplenishmentResult(
        average_consumption=average,
        maximum_consumption=maximum,
        confirmed_damage=damage,
        damage_replacement_percent=percent,
        damage_replacement=replacement,
        informed_stock=stock,
        need=need,
        suggested_quantity=suggested,
        requested_quantity=requested,
        above_maximum=above_maximum,
        calculation_memory=memory,
    )
