import json
from datetime import date, datetime
from langchain_core.tools import tool


def _normalize_identifier(value: str) -> str:
    return value.strip().upper()


def _load_crm() -> dict:
    with open("data/crm_mock.json", "r") as f:
        return json.load(f)


def _find_customer(customer_id: str, data: dict) -> dict | None:
    normalized_customer_id = _normalize_identifier(customer_id)
    for customer in data.get("customers", []):
        if _normalize_identifier(customer["customer_id"]) == normalized_customer_id:
            return customer
    return None


@tool
def fetch_customer_profile(customer_id: str) -> str:
    """Retrieves customer details, purchase history, tier, fraud flags, and active order dates from the CRM database."""
    try:
        normalized_customer_id = _normalize_identifier(customer_id)
        customer = _find_customer(normalized_customer_id, _load_crm())
        if customer:
            return json.dumps(customer)
        return f"Error: Customer ID {normalized_customer_id} not found."
    except Exception as e:
        return f"Error accessing CRM database: {str(e)}"

@tool
def read_refund_policy() -> str:
    """Returns the strict corporate refund rules, category exemptions, and escalation protocols."""
    try:
        with open("data/refund_policy.md", "r") as f:
            return f.read()
    except Exception as e:
        return f"Error accessing policy engine: {str(e)}"

@tool
def execute_refund(order_id: str, customer_id: str, amount: float) -> str:
    """Executes a transaction refund back to the original payment method after policy verification passes."""
    try:
        normalized_customer_id = _normalize_identifier(customer_id)
        normalized_order_id = _normalize_identifier(order_id)
        data = _load_crm()
        customer = _find_customer(normalized_customer_id, data)
        if not customer:
            return f"Denied: Customer ID {normalized_customer_id} was not found."

        if customer.get("is_fraud_flagged"):
            return (
                f"Denied: Customer {normalized_customer_id} is fraud-flagged. "
                "Refunds are blocked and must be escalated to human support."
            )

        matched_order = None
        for order in customer.get("orders", []):
            if _normalize_identifier(order.get("order_id", "")) == normalized_order_id:
                matched_order = order
                break
        if not matched_order:
            return (
                f"Denied: Order {normalized_order_id} was not found under customer "
                f"{normalized_customer_id}."
            )

        order_amount = float(matched_order.get("amount", 0))
        if round(float(amount), 2) != round(order_amount, 2):
            return (
                f"Denied: Requested refund amount ${amount:.2f} does not match "
                f"order total ${order_amount:.2f}."
            )

        purchase_date = datetime.strptime(matched_order["purchase_date"], "%Y-%m-%d").date()
        days_since_purchase = (date.today() - purchase_date).days
        if days_since_purchase < 0:
            return "Denied: Invalid order purchase date. Please escalate to human support."

        item_category = str(matched_order.get("item_category", "")).strip().lower()
        if item_category == "electronics":
            return (
                f"Denied: Order {normalized_order_id} is Electronics and is non-refundable "
                "per policy."
            )

        if days_since_purchase <= 14:
            return (
                f"Success: Refund of ${order_amount:.2f} successfully processed for "
                f"Order {normalized_order_id} (Customer: {normalized_customer_id})."
            )

        if item_category in {"apparel", "clothing"} and days_since_purchase <= 30:
            return (
                f"Denied: Order {normalized_order_id} is outside the 14-day refund window. "
                "Apparel can receive store credit only between days 15-30."
            )

        return (
            f"Denied: Order {normalized_order_id} is outside the eligible refund window "
            "per policy."
        )
    except Exception as e:
        return f"Error executing refund policy check: {str(e)}"

@tool
def escalate_to_human(reason: str) -> str:
    """Routes the active conversation immediately to a live human supervisor for manual review or high-risk handling."""
    return f"System Notice: Request escalated to human support queue. Reason: {reason}"