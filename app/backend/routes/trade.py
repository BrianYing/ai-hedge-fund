from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio

from app.backend.trade.alpaca_client.order import Alpaca
from app.backend.models.schemas import ErrorResponse, OrderRequest

router = APIRouter(prefix="/trade")

@router.get("/account/position")
async def get_account_position():
    try:
        alpaca_client = Alpaca()
        return {
            "account": alpaca_client.account,
            "buying_power": alpaca_client.get_buying_power(),
            "all_position": alpaca_client.get_all_position()
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the request: {str(e)}")

@router.post(
    path="/buy",
    responses={
        200: {"description": "Successful response with streaming updates"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def run_buy(request: OrderRequest):
    try:
        alpaca_client = Alpaca()
        alpaca_client.market_order(request.ticker, request.qty, True)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the request: {str(e)}")

@router.post(
    path="/sell",
    responses={
        200: {"description": "Successful response with streaming updates"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def run_sell(request: OrderRequest):
    try:
        alpaca_client = Alpaca()
        alpaca_client.market_order(request.ticker, request.qty, False)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the request: {str(e)}")
