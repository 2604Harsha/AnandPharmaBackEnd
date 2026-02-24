from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from middleware.middleware import auth_middleware
from api.routers.routes import auth
from api.routers.routes.product import router as product_router
from api.routers.routes.cart import router as cart 
from api.routers.routes.prescription import router as prescription
from api.routers.routes.checkout_router import router as checkout_router
from api.routers.routes.billing import router as billing
from api.routers.routes.payment import router as payment
from api.routers.routes.placeorder import router as placeorder
from api.routers.routes.pharmacist_profile import router as pharmacist_profile
from api.routers.routes.pharmacist_orders import router as pharmacist_orders
from api.routers.routes.delivery import router as delivery
from api.routers.routes.delivery_tracking import router as delivery_tracking 
from api.routers.routes.order_cancel import router as order_cancel 
from api.routers.routes.user_refund_router import router as user_refund_router
from api.routers.routes.pharmacist_notification_router import router as pharmacist_notification_router
from api.routers.routes.pharmacist_refund_router import router as pharmacist_refund_router
from api.routers.routes.admin_analytics import router as admin_analytics
from api.routers.routes.chat import router as chat 
from api.routers.routes.profile_router import router as profile_router
from api.routers.routes.delivery_agent_profile import router as delivery_agent_profile
from api.routers.routes.admin_surge import router as admin_surge
from api.routers.routes.campaign_router import router as campaign_router
from api.routers.routes.notification_router import router as notification_router
from api.routers.routes.promo_router import router as promo_router
from api.routers.routes.targeting_rule import router as targeting_rule
from api.routers.routes.marketing_router import router as marketing_router

from core.database import Base, engine

app = FastAPI(title="Anand Pharma API")

@app.middleware("http")
async def jwt_middleware(request: Request, call_next):
    return await auth_middleware(request, call_next)

app.include_router(auth.router)
app.include_router(profile_router)
app.include_router(pharmacist_profile)
app.include_router(delivery_agent_profile)
app.include_router(admin_surge)
app.include_router(product_router)
app.include_router(prescription)
app.include_router(cart)
app.include_router(checkout_router)
app.include_router(billing)
app.include_router(payment)
app.include_router(placeorder)
app.include_router(pharmacist_orders)
app.include_router(delivery)
app.include_router(delivery_tracking)
app.include_router(order_cancel)
app.include_router(user_refund_router)
app.include_router(pharmacist_notification_router)
app.include_router(pharmacist_refund_router)
app.include_router(admin_analytics)
app.include_router(campaign_router)
app.include_router(notification_router)
app.include_router(promo_router)
app.include_router(targeting_rule)
app.include_router(marketing_router)
app.include_router(chat)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 🔐 THIS ENABLES AUTHORIZE BUTTON
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Anand Pharma API",
        version="1.0.0",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
