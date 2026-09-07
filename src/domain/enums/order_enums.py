# Print Hub Enums

from enum import Enum, auto


class OrderStatus(str, Enum):
    """Order state machine states."""
    CREATED = "created"
    FILE_RECEIVED = "file_received"
    ANALYZING = "analyzing"
    WAITING_FOR_PARAMETERS = "waiting_for_parameters"
    WAITING_FOR_PAYMENT = "waiting_for_payment"
    PAID = "paid"
    PREPARING = "preparing"
    QUEUED = "queued"
    PRINTING = "printing"
    PAUSED = "paused"
    NEEDS_ADMIN_ACTION = "needs_admin_action"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PaymentStatus(str, Enum):
    """Payment status states."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PrintJobStatus(str, Enum):
    """Print job status states."""
    PENDING = "pending"
    SENT_TO_AGENT = "sent_to_agent"
    ACKNOWLEDGED = "acknowledged"
    PRINTING = "printing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PrinterStatus(str, Enum):
    """Physical printer status."""
    ONLINE = "online"
    OFFLINE = "offline"
    READY = "ready"
    PRINTING = "printing"
    PAPER_OUT = "paper_out"
    PAPER_JAM = "paper_jam"
    INK_LOW = "ink_low"
    INK_EMPTY = "ink_empty"
    ERROR = "error"
    UNKNOWN = "unknown"


class PrintMode(str, Enum):
    """Print mode options."""
    BLACK_WHITE = "black_white"
    COLOR = "color"


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    PHOTO = "photo"  # Special case for photo printing


class AdminActionType(str, Enum):
    """Admin action types for audit log."""
    RESUME_FROM_PAGE = "resume_from_page"
    RESUME_CURRENT = "resume_current"
    RESUME_NEXT = "resume_next"
    CANCEL_JOB = "cancel_job"
    PAUSE_JOB = "pause_job"
    MARK_COMPLETED = "mark_completed"
    ADD_FREE_USER = "add_free_user"
    REMOVE_FREE_USER = "remove_free_user"
    UPDATE_PRICING = "update_pricing"
    RESTART_AGENT = "restart_agent"
