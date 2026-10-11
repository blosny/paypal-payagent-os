"""
PayAgent OS - Cross-Agent Liquidity Pool API Routes
Enables idle balance sweeps, zero-interest peer liquidity advances, and automated repayments.
"""

from fastapi import APIRouter, HTTPException
from ...models.liquidity_pool import (
    PoolStatus,
    PoolContribution,
    PoolDrawdown,
    DepositRequest,
    DrawdownRequest,
    RepayRequest,
)
from ...services.liquidity_pool_service import liquidity_pool_service

router = APIRouter(prefix="/liquidity-pool", tags=["Cross-Agent Liquidity Pool"])


@router.get("/status", response_model=PoolStatus)
def get_pool_status():
    """
    Returns current pool metrics, available liquidity, and active drawdowns.
    """
    return liquidity_pool_service.get_status()


@router.post("/deposit", response_model=PoolContribution)
def deposit_idle_liquidity(req: DepositRequest):
    """
    Sweeps idle surplus daily budget from an agent into the internal liquidity pool.
    """
    try:
        return liquidity_pool_service.deposit_liquidity(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/drawdown", response_model=PoolDrawdown)
def request_liquidity_drawdown(req: DrawdownRequest):
    """
    Requests an instant zero-interest micro-loan from the pool.
    Requires credit verification (FICO >= 650) and sufficient liquidity.
    """
    try:
        return liquidity_pool_service.request_drawdown(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repay", response_model=PoolDrawdown)
def repay_loan(req: RepayRequest):
    """
    Repays an active drawdown back into the pool.
    """
    try:
        return liquidity_pool_service.repay_loan(req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
