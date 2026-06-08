from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return str(uuid4())


class SupplierStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"


class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISCONTINUED = "discontinued"


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    company_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    contact_name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(64), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    region: Mapped[str] = mapped_column(String(128), default="")
    city: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[SupplierStatus] = mapped_column(
        SqlEnum(
            SupplierStatus,
            values_callable=lambda values: [item.value for item in values],
            native_enum=False,
        ),
        default=SupplierStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
    )


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("supplier_id", "sku", name="uq_supplier_product_sku"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), index=True)
    sku: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(128), default="", index=True)
    hs_code: Mapped[str] = mapped_column(String(32), default="")
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    minimum_order_quantity: Mapped[int] = mapped_column(default=1)
    status: Mapped[ProductStatus] = mapped_column(
        SqlEnum(
            ProductStatus,
            values_callable=lambda values: [item.value for item in values],
            native_enum=False,
        ),
        default=ProductStatus.DRAFT,
        index=True,
    )
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    supplier: Mapped[Supplier] = relationship(back_populates="products")
