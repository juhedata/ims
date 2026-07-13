from fastapi import APIRouter

from app.api import auth, user, dashboard, inventory, product, partner, customer, inbound, outbound, snapshot, audit, settings

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(dashboard.router)
api_router.include_router(inventory.router)
api_router.include_router(product.router)
api_router.include_router(partner.router)
api_router.include_router(customer.router)
api_router.include_router(inbound.router)
api_router.include_router(outbound.router)
api_router.include_router(snapshot.router)
api_router.include_router(audit.router)
api_router.include_router(settings.router)
