"""
Payment Provider - abstract interface for payment processing.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentResult:
    """Result of a payment operation."""
    status: PaymentStatus
    provider_payment_id: Optional[str]
    error_message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class PaymentProvider(ABC):
    """Abstract base class for payment providers."""
    
    @abstractmethod
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        user_telegram_id: int,
    ) -> tuple[str, str]:
        """
        Create a new payment.
        
        Returns:
            Tuple of (payment_id, invoice_url or telegram_invoice_payload)
        """
        pass
    
    @abstractmethod
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Dict[str, Any],
    ) -> PaymentResult:
        """Verify payment from webhook data."""
        pass
    
    @abstractmethod
    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Refund a payment."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name for logging."""
        pass


class MockPaymentProvider(PaymentProvider):
    """
    Mock payment provider for testing.
    
    In production, replace with real provider (YooKassa, CloudPayments, etc.)
    """
    
    def __init__(self):
        self._payments: Dict[str, PaymentResult] = {}
    
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        user_telegram_id: int,
    ) -> tuple[str, str]:
        payment_id = f"mock_payment_{order_id}"
        # For Telegram native payments, return invoice payload
        # For web payments, return URL
        invoice_payload = f"order_{order_id}_user_{user_telegram_id}"
        return payment_id, invoice_payload
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Dict[str, Any],
    ) -> PaymentResult:
        # Simulate successful payment
        result = PaymentResult(
            status=PaymentStatus.PAID,
            provider_payment_id=payment_id,
            raw_data=webhook_data,
        )
        self._payments[payment_id] = result
        return result
    
    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> bool:
        if payment_id in self._payments:
            self._payments[payment_id] = PaymentResult(
                status=PaymentStatus.REFUNDED,
                provider_payment_id=payment_id,
            )
            return True
        return False
    
    def get_provider_name(self) -> str:
        return "MockProvider"


class YooKassaProvider(PaymentProvider):
    """
    YooKassa payment provider.
    
    NOTE: Requires proper configuration and credentials.
    Implementation placeholder - needs actual API integration.
    """
    
    def __init__(self, shop_id: str, secret_key: str):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.base_url = "https://api.yookassa.ru/v3"
    
    async def create_payment(
        self,
        order_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        user_telegram_id: int,
    ) -> tuple[str, str]:
        """Create YooKassa payment."""
        # TODO: Implement actual YooKassa API call
        # This is a placeholder structure
        raise NotImplementedError(
            "YooKassa provider not fully implemented. Use MockPaymentProvider for testing."
        )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Dict[str, Any],
    ) -> PaymentResult:
        """Verify YooKassa webhook."""
        # TODO: Implement actual verification with signature check
        raise NotImplementedError(
            "YooKassa provider not fully implemented. Use MockPaymentProvider for testing."
        )
    
    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Refund via YooKassa."""
        raise NotImplementedError(
            "YooKassa provider not fully implemented. Use MockPaymentProvider for testing."
        )
    
    def get_provider_name(self) -> str:
        return "YooKassa"
