"""
Pricing Service - calculates document printing costs.
"""
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional

from src.domain.enums.order_enums import PrintMode, DocumentType


@dataclass
class PriceBreakdown:
    """Detailed price breakdown for an order."""
    base_price_per_page: Decimal
    pages: int
    copies: int
    mode_multiplier: Decimal
    total_original_pages: int
    service_pages: int
    total_physical_pages: int
    subtotal: Decimal
    discount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")

    def format(self) -> str:
        """Format price breakdown for user display."""
        lines = [
            f"📄 Страниц в документе: {self.pages}",
            f"🔢 Копии: {self.copies}",
            f"📋 Всего оригинальных страниц: {self.total_original_pages}",
            f"ℹ️ Служебных страниц: {self.service_pages}",
            f"📏 Всего физических страниц: {self.total_physical_pages}",
            f"💰 Стоимость: {self.total:.2f} ₽",
        ]
        return "\n".join(lines)


class PricingService:
    """Service for calculating printing costs."""
    
    def __init__(self):
        self.base_price_bw = Decimal("10.00")
        self.base_price_color = Decimal("15.00")
        self.base_price_photo = Decimal("25.00")
        self.service_page_price_bw = Decimal("5.00")
        self.service_page_price_color = Decimal("5.00")
    
    async def calculate_price(
        self,
        document_type: DocumentType,
        pages: int,
        copies: int,
        print_mode: PrintMode,
        is_free_user: bool = False,
    ) -> PriceBreakdown:
        """Calculate total price for an order."""
        if is_free_user:
            return PriceBreakdown(
                base_price_per_page=Decimal("0"),
                pages=pages,
                copies=copies,
                mode_multiplier=Decimal("1"),
                total_original_pages=pages * copies,
                service_pages=copies,
                total_physical_pages=(pages * copies) + copies,
                subtotal=Decimal("0"),
                total=Decimal("0"),
            )
        
        if document_type == DocumentType.PHOTO:
            base_price = self.base_price_photo
        elif print_mode == PrintMode.COLOR:
            base_price = self.base_price_color
        else:
            base_price = self.base_price_bw
        
        mode_multiplier = Decimal("1.0")
        total_original_pages = pages * copies
        service_pages = copies
        total_physical_pages = total_original_pages + service_pages
        
        service_price = (
            self.service_page_price_color 
            if print_mode == PrintMode.COLOR 
            else self.service_page_price_bw
        )
        
        subtotal = (base_price * total_original_pages) + (service_price * service_pages)
        discount = Decimal("0")
        total = subtotal - discount
        
        return PriceBreakdown(
            base_price_per_page=base_price,
            pages=pages,
            copies=copies,
            mode_multiplier=mode_multiplier,
            total_original_pages=total_original_pages,
            service_pages=service_pages,
            total_physical_pages=total_physical_pages,
            subtotal=subtotal,
            discount=discount,
            total=total,
        )
    
    async def get_base_prices(self) -> dict:
        """Get current base prices for display."""
        return {
            "bw_per_page": self.base_price_bw,
            "color_per_page": self.base_price_color,
            "photo_per_page": self.base_price_photo,
            "service_page_bw": self.service_page_price_bw,
            "service_page_color": self.service_page_price_color,
        }
