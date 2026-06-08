from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import ProductStatus, SupplierStatus


class SupplierBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_name: str = ""
    email: str = Field(..., min_length=3, max_length=255)
    phone: str = ""
    website: str = ""
    region: str = ""
    city: str = ""
    address: str = ""
    status: SupplierStatus = SupplierStatus.PENDING


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_name: str | None = None
    email: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = None
    website: str | None = None
    region: str | None = None
    city: str | None = None
    address: str | None = None
    status: SupplierStatus | None = None


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    category: str = ""
    hs_code: str = ""
    unit_price: Decimal | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    minimum_order_quantity: int = Field(default=1, ge=1)
    status: ProductStatus = ProductStatus.DRAFT
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProductCreate(ProductBase):
    supplier_id: str


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=128)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    hs_code: str | None = None
    unit_price: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    minimum_order_quantity: int | None = Field(default=None, ge=1)
    status: ProductStatus | None = None
    attributes: dict[str, Any] | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    supplier_id: str
    created_at: datetime
    updated_at: datetime


class ProductImportItem(ProductBase):
    pass


class ProductImportRequest(BaseModel):
    supplier_id: str
    products: list[ProductImportItem] = Field(..., min_length=1)


class ProductImportResponse(BaseModel):
    supplier_id: str
    imported_count: int
    products: list[ProductRead]
