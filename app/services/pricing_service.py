# services/pricing_service.py

FREE_DELIVERY_MIN = 99
DELIVERY_FEE = 30
HANDLING_FEE = 10

CGST_PERCENT = 9
SGST_PERCENT = 9


def calculate_pricing(subtotal: float, surge_fee: float = 0):
    cgst = round(subtotal * CGST_PERCENT / 100, 2)
    sgst = round(subtotal * SGST_PERCENT / 100, 2)

    if subtotal >= FREE_DELIVERY_MIN:
        delivery_fee = 0
        free_delivery_applied = True
    else:
        delivery_fee = DELIVERY_FEE
        free_delivery_applied = False

    total = round(
        subtotal
        + cgst
        + sgst
        + HANDLING_FEE
        + delivery_fee
        + surge_fee,
        2
    )

    return {
        "cgst": cgst,
        "sgst": sgst,
        "handling_fee": HANDLING_FEE,
        "delivery_fee": delivery_fee,
        "free_delivery_applied": free_delivery_applied,
        "surge_fee": surge_fee,
        "total": total,
    }
