from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, ProductStatus, Supplier
from ..platform_events import enqueue_event_actions, products_imported_event
from ..platform_schemas import (
    ProductCreate,
    ProductImportRequest,
    ProductImportResponse,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


def _get_product_or_404(db: Session, product_id: str) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def _get_supplier_or_404(db: Session, supplier_id: str) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    _get_supplier_or_404(db, payload.supplier_id)
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product SKU already exists for this supplier",
        ) from exc
    db.refresh(product)
    return product


@router.get("", response_model=list[ProductRead])
def list_products(
    supplier_id: str | None = None,
    product_status: ProductStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[Product]:
    statement = select(Product).order_by(Product.created_at.desc()).offset(skip).limit(limit)
    if supplier_id:
        statement = statement.where(Product.supplier_id == supplier_id)
    if product_status:
        statement = statement.where(Product.status == product_status)
    return list(db.scalars(statement))


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: str, db: Session = Depends(get_db)) -> Product:
    return _get_product_or_404(db, product_id)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> Product:
    product = _get_product_or_404(db, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product SKU already exists for this supplier",
        ) from exc
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, db: Session = Depends(get_db)) -> None:
    product = _get_product_or_404(db, product_id)
    db.delete(product)
    db.commit()


@router.post("/import", response_model=ProductImportResponse, status_code=status.HTTP_201_CREATED)
async def import_products(
    payload: ProductImportRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ProductImportResponse:
    supplier = _get_supplier_or_404(db, payload.supplier_id)
    products = [
        Product(supplier_id=payload.supplier_id, **product_payload.model_dump())
        for product_payload in payload.products
    ]
    db.add_all(products)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more product SKUs already exist for this supplier",
        ) from exc

    for product in products:
        db.refresh(product)

    enqueue_event_actions(
        dispatcher=request.app.state.dispatcher,
        background_tasks=background_tasks,
        event=products_imported_event(supplier, products),
    )
    return ProductImportResponse(
        supplier_id=supplier.id,
        imported_count=len(products),
        products=products,
    )
