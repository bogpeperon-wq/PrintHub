"""Print Hub Database Models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    DateTime,
    Numeric,
    ForeignKey,
    Enum,
    Text,
    Boolean,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    declarative_base,
)

Base = declarative_base()


class User(Base):
    """Telegram user model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    building: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entrance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_free_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id"),
    )
    
    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Order(Base):
    """Order model - represents business order from user."""
    
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    
    # File info
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)  # Path to original file
    prepared_file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # Path to normalized PDF
    
    # Document analysis
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, docx, jpg, etc.
    page_count: Mapped[int] = mapped_column(Integer, nullable=True)  # Determined by system
    
    # Print parameters
    print_mode: Mapped[str] = mapped_column(String(50), nullable=True)  # black_white or color
    copies: Mapped[int] = mapped_column(Integer, nullable=True)
    total_physical_pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # pages * copies + service pages
    
    # Pricing
    price_per_page: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    is_free_order: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # State
    status: Mapped[str] = mapped_column(String(50), default="created", index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    file_cleanup_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When file should be deleted
    
    # Error info
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    print_jobs: Mapped[List["PrintJob"]] = relationship("PrintJob", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_orders_telegram_id_status", "telegram_id", "status"),
        Index("ix_orders_created_at", "created_at"),
        Index("ix_orders_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, telegram_id={self.telegram_id}, status={self.status})>"


class Payment(Base):
    """Payment model."""
    
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    
    # Payment provider info
    provider: Mapped[str] = mapped_column(String(100), nullable=False)  # yookassa, cloudpayments, etc.
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)  # External payment ID
    
    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    
    # Webhook info
    webhook_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Raw webhook data for debugging
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationship
    order: Mapped["Order"] = relationship("Order", back_populates="payment")
    
    __table_args__ = (
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_provider_payment_id", "provider_payment_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, order_id={self.order_id}, status={self.status})>"


class PrintJob(Base):
    """Print job model - represents physical printing task."""
    
    __tablename__ = "print_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    
    # Unique identifier for idempotency
    print_job_uuid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Print artifact path (immutable prepared PDF with service page)
    print_artifact_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Print settings snapshot
    print_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    copies: Mapped[int] = mapped_column(Integer, nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, default=1)  # For resume functionality
    end_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Agent assignment
    agent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("print_agents.id"), nullable=True)
    
    # State
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    
    # Physical print tracking
    pages_printed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Reported by agent
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_to_agent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    printing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Retry count
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="print_jobs")
    agent: Mapped[Optional["PrintAgent"]] = relationship("PrintAgent", back_populates="print_jobs")
    
    __table_args__ = (
        Index("ix_print_jobs_order_id_status", "order_id", "status"),
        Index("ix_print_jobs_agent_id", "agent_id"),
    )
    
    def __repr__(self) -> str:
        return f"<PrintJob(id={self.id}, order_id={self.order_id}, status={self.status})>"


class PrintAgent(Base):
    """Print Agent model - represents MacBook agent instance."""
    
    __tablename__ = "print_agents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Agent identification
    agent_uuid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Printer info
    printer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    printer_model: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Connection state
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Printer status (from CUPS/Canon)
    printer_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    paper_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # OK, OUT, UNKNOWN
    ink_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # OK, LOW, EMPTY, UNKNOWN
    current_job_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    print_jobs: Mapped[List["PrintJob"]] = relationship("PrintJob", back_populates="agent", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_print_agents_uuid", "agent_uuid"),
        Index("ix_print_agents_is_online", "is_online"),
    )
    
    def __repr__(self) -> str:
        return f"<PrintAgent(uuid={self.agent_uuid}, hostname={self.hostname}, online={self.is_online})>"


class PricingRule(Base):
    """Pricing rules configuration."""
    
    __tablename__ = "pricing_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Rule scope
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, photo, etc.
    print_mode: Mapped[str] = mapped_column(String(50), nullable=False)  # black_white, color
    
    # Price
    price_per_page: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Validity
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("document_type", "print_mode", "valid_from", name="uq_pricing_rule_unique"),
        Index("ix_pricing_rules_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<PricingRule(document_type={self.document_type}, mode={self.print_mode}, price={self.price_per_page})>"


class AdminAction(Base):
    """Admin action audit log."""
    
    __tablename__ = "admin_actions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Admin info
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    # Action info
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # order, print_job, user, etc.
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # State change
    old_state: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    new_state: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy reservation)
    action_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_admin_actions_admin_id", "admin_telegram_id"),
        Index("ix_admin_actions_created_at", "created_at"),
        Index("ix_admin_actions_action_type", "action_type"),
    )
    
    def __repr__(self) -> str:
        return f"<AdminAction(admin_id={self.admin_telegram_id}, action={self.action_type})>"


class FileCleanupLog(Base):
    """Log of file cleanup operations."""
    
    __tablename__ = "file_cleanup_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    
    # File paths that were deleted
    original_file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    prepared_file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    print_artifact_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Deletion reason
    reason: Mapped[str] = mapped_column(String(100), default="retention_policy")  # retention_policy, manual, error
    
    # Timestamp
    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_file_cleanup_log_order_id", "order_id"),
        Index("ix_file_cleanup_log_deleted_at", "deleted_at"),
    )
    
    def __repr__(self) -> str:
        return f"<FileCleanupLog(order_id={self.order_id}, deleted_at={self.deleted_at})>"
