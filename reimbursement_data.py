"""
Reimbursement Data Model
========================
Unified 4-state model: pending_receipt, pending_submit, submitted, error.
All legacy status fields (ai_check_result, sync_status, etc.) are derived
from the canonical `status` field.
Independent data model and mock data for phone UI records.
"""

import copy


# =============================================================================
# Unified Status Model
# =============================================================================

# The 4 canonical states
STATUS_PENDING_RECEIPT = "pending_receipt"   # 待补票
STATUS_PENDING_SUBMIT = "pending_submit"     # 待提交
STATUS_SUBMITTED = "submitted"               # 已提交
STATUS_ERROR = "error"                       # 异常

ALL_STATUSES = [STATUS_PENDING_RECEIPT, STATUS_PENDING_SUBMIT, STATUS_SUBMITTED, STATUS_ERROR]

STATUS_LABELS = {
    STATUS_PENDING_RECEIPT: "待补票",
    STATUS_PENDING_SUBMIT: "待提交",
    STATUS_SUBMITTED: "已提交",
    STATUS_ERROR: "异常",
}

STATUS_COLORS = {
    STATUS_PENDING_RECEIPT: "#E65100",  # orange
    STATUS_PENDING_SUBMIT: "#1565C0",   # blue
    STATUS_SUBMITTED: "#12B76A",        # green
    STATUS_ERROR: "#E5484D",            # red
}

STATUS_PILL_CLASS = {
    STATUS_PENDING_RECEIPT: "pill-warning",
    STATUS_PENDING_SUBMIT: "pill-info",
    STATUS_SUBMITTED: "pill-success",
    STATUS_ERROR: "pill-danger",
}


def get_status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def get_status_color(status: str) -> str:
    return STATUS_COLORS.get(status, "#999")


def get_pill_class(status: str) -> str:
    return STATUS_PILL_CLASS.get(status, "pill-neutral")


def format_amount(amount, currency: str) -> str:
    if currency == "CNY":
        return f"¥{amount:,}"
    elif currency == "HKD":
        return f"HK${amount:,}"
    elif currency == "USD":
        return f"${amount:,}"
    elif currency == "JPY":
        return f"¥{amount:,}"
    return f"{amount} {currency}"


# =============================================================================
# Backward compatibility: derive legacy fields from status
# =============================================================================

def derive_ai_check_result(status: str) -> str:
    """Map unified status to legacy ai_check_result for display."""
    mapping = {
        STATUS_PENDING_RECEIPT: "need_supplement",
        STATUS_PENDING_SUBMIT: "passed",
        STATUS_SUBMITTED: "passed",
        STATUS_ERROR: "failed",
    }
    return mapping.get(status, "pending")


def derive_sync_status(status: str) -> str:
    """Map unified status to legacy sync_status for display."""
    mapping = {
        STATUS_PENDING_RECEIPT: "not_synced",
        STATUS_PENDING_SUBMIT: "not_synced",
        STATUS_SUBMITTED: "synced",
        STATUS_ERROR: "not_synced",
    }
    return mapping.get(status, "not_synced")


# =============================================================================
# CTA Controller
# =============================================================================

def get_cta_action(status: str) -> dict:
    """Return the single CTA button config for a given status.
    
    Returns dict with keys: label, action, style
    """
    mapping = {
        STATUS_PENDING_RECEIPT: {
            "label": "上传收据",
            "action": "upload_receipt",
            "style": "btn-primary",
        },
        STATUS_PENDING_SUBMIT: {
            "label": "提交报销",
            "action": "confirm_submit",
            "style": "btn-primary",
        },
        STATUS_SUBMITTED: {
            "label": "查看记录",
            "action": "open_records",
            "style": "btn-secondary",
        },
        STATUS_ERROR: {
            "label": "重新处理",
            "action": "retry_process",
            "style": "btn-primary",
        },
    }
    return mapping.get(status, {"label": "查看详情", "action": "open_detail", "style": "btn-secondary"})


# =============================================================================
# Mock Data (6 records covering all 4 states)
# =============================================================================

_MOCK_RECORDS = [
    {
        "id": "record_001",
        "merchant_name": "东京希尔顿酒店",
        "amount": 55964,
        "currency": "JPY",
        "transaction_time": "2026-06-12 19:42",
        "expense_type": "差旅住宿",
        "status": STATUS_PENDING_RECEIPT,
        "ai_check_message": "请上传收据，完成补票后方可继续报销流程。",
        "sync_time": None,
        "sync_order_no": "",
        "attachments": [],
        "expense_description": "东京出差住宿费用",
        "tax_rate": "10%（标准税率）",
        "note": "日本东京出差",
    },
    {
        "id": "record_002",
        "merchant_name": "新加坡航空 SQ637",
        "amount": 428.00,
        "currency": "SGD",
        "transaction_time": "2026-06-11 16:25",
        "expense_type": "国际机票",
        "status": STATUS_PENDING_SUBMIT,
        "ai_check_message": "AI 校验通过，待提交报销。",
        "sync_time": None,
        "sync_order_no": "",
        "attachments": ["收据"],
        "expense_description": "新加坡往返差旅行程机票",
        "tax_rate": "0%（国际航空服务）",
        "note": "新加坡客户拜访行程",
    },
    {
        "id": "record_007",
        "merchant_name": "OpenAI Subscription",
        "amount": 20.00,
        "currency": "USD",
        "transaction_time": "2026-06-10 10:24",
        "expense_type": "软件订阅",
        "status": STATUS_PENDING_SUBMIT,
        "ai_check_message": "AI 校验通过，待提交报销。",
        "sync_time": None,
        "sync_order_no": "",
        "attachments": ["OpenAI_Invoice_202606.pdf"],
        "expense_description": "AI 工具订阅费用",
        "tax_rate": "0%（境外服务）",
        "note": "用于差旅期间文档处理与效率工具",
    },
    {
        "id": "record_003",
        "merchant_name": "Starbucks Shibuya",
        "amount": 780,
        "currency": "JPY",
        "transaction_time": "2026-06-10 09:18",
        "expense_type": "餐饮",
        "status": STATUS_SUBMITTED,
        "ai_check_message": "AI 校验通过，费用已提交至报销系统。",
        "sync_time": "2026-06-12 10:30",
        "sync_order_no": "BX202606121030",
        "attachments": ["收据"],
        "expense_description": "东京出差餐饮费用",
        "tax_rate": "10%（标准税率）",
        "note": "日本东京出差午餐",
    },
    {
        "id": "record_004",
        "merchant_name": "Grab Singapore",
        "amount": 26.80,
        "currency": "SGD",
        "transaction_time": "2026-06-10 13:47",
        "expense_type": "交通出行",
        "status": STATUS_PENDING_RECEIPT,
        "ai_check_message": "请上传收据，完成补票后方可继续报销流程。",
        "sync_time": None,
        "sync_order_no": "",
        "attachments": [],
        "expense_description": "新加坡出差交通费用",
        "tax_rate": "0%（海外交通）",
        "note": "新加坡客户拜访行程",
    },
    {
        "id": "record_005",
        "merchant_name": "Hilton Times Square New York",
        "amount": 318.50,
        "currency": "USD",
        "transaction_time": "2026-06-09 22:31",
        "expense_type": "差旅住宿",
        "status": STATUS_ERROR,
        "ai_check_message": "MCC Code：消费商户类型不符合公司政策",
        "sync_time": None,
        "sync_order_no": "",
        "attachments": ["收据"],
        "expense_description": "纽约出差住宿费用",
        "tax_rate": "0%（境外酒店）",
        "note": "美国纽约出差",
    },
    {
        "id": "record_006",
        "merchant_name": "Heathrow Express",
        "amount": 25.00,
        "currency": "GBP",
        "transaction_time": "2026-06-09 08:05",
        "expense_type": "交通出行",
        "status": STATUS_PENDING_SUBMIT,
        "ai_check_message": "AI 校验通过，待提交报销。",
        "sync_time": None,
        "sync_order_no": "",
        "attachments": ["收据"],
        "expense_description": "伦敦出差交通费用",
        "tax_rate": "0%（海外交通）",
        "note": "英国伦敦出差",
    },
]


def get_default_records() -> list:
    """Return a fresh deep copy of mock reimbursement records."""
    return copy.deepcopy(_MOCK_RECORDS)


# =============================================================================
# Record Helpers
# =============================================================================

def find_record(records: list, record_id: str):
    for r in records:
        if r["id"] == record_id:
            return r
    return None


def update_record_fields(records: list, record_id: str, updates: dict) -> bool:
    rec = find_record(records, record_id)
    if rec:
        rec.update(updates)
        return True
    return False


def filter_records(records: list, filter_key: str = "all") -> list:
    if filter_key == "all":
        return records
    return [r for r in records if r.get("status") == filter_key]


def format_sync_time(sync_time) -> str:
    if not sync_time:
        return "--"
    return str(sync_time)


# =============================================================================
# Backward compatibility aliases
# =============================================================================

# Keep old function names working for any code that still references them
AI_CHECK_LABELS = {k: v for k, v in [
    ("pending", "待校验"), ("passed", "已通过"),
    ("need_supplement", "待补充"), ("failed", "未通过"),
]}

def get_ai_check_label(status: str) -> str:
    return AI_CHECK_LABELS.get(status, STATUS_LABELS.get(status, status))
