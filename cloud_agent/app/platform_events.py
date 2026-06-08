from fastapi import BackgroundTasks

from .dispatcher import Dispatcher
from .models import Product, Supplier
from .schemas import NormalizedEvent


def supplier_created_event(supplier: Supplier) -> NormalizedEvent:
    return NormalizedEvent(
        source="platform",
        event_type="supplier.created",
        action="created",
        title=supplier.company_name,
        actor=supplier.contact_name or supplier.email,
        entity_id=supplier.id,
        url=f"/suppliers/{supplier.id}",
        payload={
            "supplier_id": supplier.id,
            "company_name": supplier.company_name,
            "email": supplier.email,
            "region": supplier.region,
            "city": supplier.city,
            "status": supplier.status.value,
        },
    )


def products_imported_event(supplier: Supplier, products: list[Product]) -> NormalizedEvent:
    imported_count = len(products)
    return NormalizedEvent(
        source="platform",
        event_type="products.imported",
        action="imported",
        title=f"{imported_count} products imported for {supplier.company_name}",
        actor=supplier.company_name,
        entity_id=supplier.id,
        url=f"/products?supplier_id={supplier.id}",
        payload={
            "supplier_id": supplier.id,
            "company_name": supplier.company_name,
            "imported_count": imported_count,
            "product_ids": [product.id for product in products],
            "skus": [product.sku for product in products],
        },
    )


def enqueue_event_actions(
    *,
    dispatcher: Dispatcher,
    background_tasks: BackgroundTasks,
    event: NormalizedEvent,
) -> int:
    actions = dispatcher.plan_actions(event)
    if actions:
        background_tasks.add_task(dispatcher.execute, actions)
    return len(actions)
