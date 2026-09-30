import json
from typing import Any, Dict, Iterable


FEE_NAME_MAP = {
    "unit_price": ("transport_fee", "中港运输费"),
    "delivery_fee": ("delivery_fee", "香港派送费"),
}


def _detail_dict(detail: Any) -> Dict[str, Any]:
    if hasattr(detail, "model_dump"):
        return detail.model_dump()
    if isinstance(detail, dict):
        return detail
    return {}


def build_customer_fee_summary(
    fee_details: Iterable[Any],
    total_price: float,
    minimum_charge: float | None,
) -> Dict[str, Any]:
    customer_details = []
    calculated_subtotal = 0.0
    for detail in fee_details:
        item = _detail_dict(detail)
        amount = round(float(item.get("amount") or 0), 2)
        calculated_subtotal += amount
        source_name = str(item.get("name") or "")
        code, display_name = FEE_NAME_MAP.get(
            source_name,
            (source_name or "additional_fee", item.get("cn_name") or "附加费"),
        )
        customer_details.append({"code": code, "name": display_name, "amount": amount})

    calculated_subtotal = round(calculated_subtotal, 2)
    total_price = round(float(total_price), 2)
    minimum_applied = bool(
        minimum_charge is not None
        and total_price > calculated_subtotal
        and abs(total_price - float(minimum_charge)) < 0.01
    )
    return {
        "customer_fee_details": customer_details,
        "calculated_subtotal": calculated_subtotal,
        "minimum_charge": round(float(minimum_charge), 2) if minimum_charge is not None else None,
        "minimum_applied": minimum_applied,
    }


def parse_customer_quote_config(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}


def parse_customer_price_tiers(value: Any) -> list[Dict[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value) if value else []
        except (TypeError, ValueError):
            return []
    if not isinstance(value, list):
        return []

    tiers = []
    for item in value:
        if not isinstance(item, dict):
            continue
        try:
            min_quantity = float(item.get("min_quantity") or 0)
            max_value = item.get("max_quantity")
            max_quantity = None if max_value in (None, "") else float(max_value)
            min_price = float(item["min_price"])
            max_price = float(item.get("max_price", min_price))
        except (KeyError, TypeError, ValueError):
            continue
        if min_quantity < 0 or min_price < 0 or max_price < min_price:
            continue
        if max_quantity is not None and max_quantity <= min_quantity:
            continue
        tiers.append(
            {
                "min_quantity": min_quantity,
                "max_quantity": max_quantity,
                "min_price": min_price,
                "max_price": max_price,
                "unit": str(item.get("unit") or "kg"),
            }
        )
    return tiers
