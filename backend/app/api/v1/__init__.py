from fastapi import APIRouter
from .agents import router as agents_router
from .payments import router as payments_router
from .stats import router as stats_router
from .negotiations import router as negotiations_router
from .toolkit import router as toolkit_router
from .arbitrage import router as arbitrage_router
from .security import router as security_router
from .mcp import router as mcp_router
from .webhooks import router as webhooks_router
from .escrow import router as escrow_router
from .vault import router as vault_router
from .credit import router as credit_router
from .telegram import router as telegram_router
from .roi import router as roi_router
from .tenants import router as tenants_router
from .identity import router as identity_router
from .disputes import router as disputes_router
from .fee_optimizer import router as fee_optimizer_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_v1_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_v1_router.include_router(stats_router, prefix="/stats", tags=["Statistics & Overview"])
api_v1_router.include_router(negotiations_router, prefix="/negotiations", tags=["Budget Negotiations"])
api_v1_router.include_router(toolkit_router, prefix="/toolkit", tags=["PayPal AI Toolkit & MCP"])
api_v1_router.include_router(arbitrage_router, prefix="/arbitrage", tags=["Spot Bidding & Arbitrage"])
api_v1_router.include_router(security_router)
api_v1_router.include_router(mcp_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(escrow_router)
api_v1_router.include_router(vault_router)
api_v1_router.include_router(credit_router)
api_v1_router.include_router(telegram_router)
api_v1_router.include_router(roi_router)
api_v1_router.include_router(tenants_router)
api_v1_router.include_router(identity_router)
api_v1_router.include_router(disputes_router)
api_v1_router.include_router(fee_optimizer_router)




