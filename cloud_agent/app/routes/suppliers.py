from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Supplier
from ..platform_events import enqueue_event_actions, supplier_created_event
from ..platform_schemas import SupplierCreate, SupplierRead, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _get_supplier_or_404(db: Session, supplier_id: str) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SupplierCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Supplier:
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier with the same company name or email already exists",
        ) from exc
    db.refresh(supplier)

    enqueue_event_actions(
        dispatcher=request.app.state.dispatcher,
        background_tasks=background_tasks,
        event=supplier_created_event(supplier),
    )
    return supplier


@router.get("", response_model=list[SupplierRead])
def list_suppliers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[Supplier]:
    statement = select(Supplier).order_by(Supplier.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement))


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: str, db: Session = Depends(get_db)) -> Supplier:
    return _get_supplier_or_404(db, supplier_id)


@router.patch("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: str,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
) -> Supplier:
    supplier = _get_supplier_or_404(db, supplier_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier with the same company name or email already exists",
        ) from exc
    db.refresh(supplier)
    return supplier
