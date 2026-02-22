"""
Domain models package.
Import all models here to ensure SQLAlchemy can resolve relationships.
"""

from app.domain.models.base import Base
from app.domain.models.audit_log import AuditLog
from app.domain.models.category import Category
from app.domain.models.product import Product
from app.domain.models.product_price import ProductPrice
from app.domain.models.offer import Offer
from app.domain.models.offer_item import OfferItem
from app.domain.models.sale import Sale
from app.domain.models.sale_item import SaleItem
from app.domain.models.sale_item_offer_product import SaleItemOfferProduct
from app.domain.models.user import User
from app.domain.models.expense_category import ExpenseCategory
from app.domain.models.expense import Expense

__all__ = [
    "Base",
    "AuditLog",
    "Category",
    "Product",
    "ProductPrice",
    "Offer",
    "OfferItem",
    "Sale",
    "SaleItem",
    "SaleItemOfferProduct",
    "User",
    "ExpenseCategory",
    "Expense",
]
