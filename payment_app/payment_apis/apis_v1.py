"""Module with payment apis."""
import json
from typing import Union

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from loguru import logger

from payment_app.configs.db import get_session
from payment_app.dependencies.verify_api_key import verify_api_key
from payment_app.lib.errors.error_handler import (
    UnprocessableEntity,NotFoundException,ForbiddenException
)
from payment_app.models import RefundTransaction
from payment_app.models.client_gateways import ClientGateway
from payment_app.models.transaction import Transaction
from payment_app.schemas.requests.v1.make_payment_in import (
    MakePaymentInRazorpay, MakePaymentInPaytm
)
from payment_app.schemas.requests.v1.refund_payment_in import RefundPaymentIn
from payment_app.services.payment_service import PaymentService
from payment_app.models.transaction import STATUS_PENDING


router_v1 = APIRouter(
    prefix="/v1",
    tags=["Version 1 Apis"],
    responses={
        403: {"description": "Not Allowed"},
        200: {"description": "Everything is ok"},
        422: {"description": "Unprocessable Entity"},
        409: {"description": "conflict in request params"},
    },
)


class SourceID(BaseModel):
    """Base model for source id"""
    source_id: str

@router_v1.post("/get_payment_status_by_source_id")
async def get_payment_status_by_order_id(
    background_tasks: BackgroundTasks,
    source_id: SourceID,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
    ):
    """Get payment status using source id."""
    source_id = source_id.source_id
    statement = select(Transaction).where(Transaction.source_id == source_id).where(
        Transaction.status != STATUS_PENDING
    )
    results = session.exec(statement).first()
    if results:
        return JSONResponse(
        content={
            "event": "transaction",
            "transaction": json.loads(results.json()),
            "driver": "razorpay",
        }
    )
    statement = select(Transaction).where(Transaction.source_id == source_id)
    results = session.exec(statement).first()
    if results:
        return JSONResponse(
            content={
                "event": "transaction",
                "transaction": json.loads(results.json()),
                "driver": "razorpay",
            }
        )
    raise HTTPException(status_code=404, detail="Transaction not found")



@router_v1.post("/make_payment")
async def make_payment(
        background_tasks: BackgroundTasks,
        make_payment_in: Union[MakePaymentInRazorpay, MakePaymentInPaytm] = Body(
            ..., discriminator='driver_id'
        ),
        session: Session = Depends(get_session),
        commons: dict = Depends(verify_api_key),
):
    """Start payment."""
    logger.debug(f"make_payment_in: {make_payment_in}")
    if make_payment_in.total_amount < make_payment_in.amount_to_pay:
        logger.critical(
            f"amount to pay is greater than total amount: {make_payment_in.total_amount}"
        )
        raise UnprocessableEntity(message="total amount cannot be greater than amount to pay")

    if make_payment_in.driver_id:
        statement = (
            select(ClientGateway)
                .where(ClientGateway.active == True)
                .where(ClientGateway.client_id == commons["client"].id)
                .where(ClientGateway.driver_id == make_payment_in.driver_id)
        )
        results = session.exec(statement)
        gateway = results.first()
        if gateway:
            logger.debug(f"gateway: {gateway}")
            gateway_id = make_payment_in.driver_id
        else:
            logger.critical(f"driver_id is not registered: {make_payment_in.driver_id}")
            raise NotFoundException(message="gateway id provided by client not found")
    else:
        statement = (
            select(ClientGateway)
                .where(ClientGateway.active == True)
                .where(ClientGateway.client_id == commons["client"].id)
                .where(ClientGateway.default == True)
        )
        results = session.exec(statement)
        gateway = results.first()
        if gateway:
            logger.debug(f"gateway: {gateway}")
            gateway_id = gateway.driver_id
        else:
            logger.critical(
                f"default gateway not found for client: {commons['client'].id}"
            )
            raise NotFoundException(message="No default gateway found for client")
    logger.debug(f"gateway_id: {gateway_id}")

    payment_service = PaymentService(session, background_tasks, gateway_id)
    result = payment_service.make_payment(
        make_payment_in=make_payment_in,
        client=commons["client"],
        client_version=commons["client_version"],
    )
    logger.debug(f"result: {result}")

    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )


@router_v1.post("/refund_payment")
async def refund_payment(
    background_tasks: BackgroundTasks,
    refund_payment_in: RefundPaymentIn,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    """Start payment refund."""
    logger.debug(f"refund_payment_in: {refund_payment_in}")
    transaction = session.get(Transaction, refund_payment_in.payment_transaction_id)
    if not transaction:
        logger.critical(
            f"transaction not found: {refund_payment_in.payment_transaction_id}"
        )
        raise NotFoundException(message="Transaction not found")
    if transaction.status != "success":
        logger.critical(
            f"transaction not successful: {refund_payment_in.payment_transaction_id}"
        )
        raise UnprocessableEntity(
            message=f"Refund can not be processed for {transaction.status} transaction."
        )

    if (
        refund_payment_in.amount_to_refund
        and refund_payment_in.amount_to_refund > transaction.amount
    ):
        logger.critical(
            f"amount to refund is greater than amount: {refund_payment_in.payment_transaction_id}"
        )
        raise ForbiddenException(
            message="The total refund amount is greater than the refund payment amount"
        )

    logger.debug(f"transaction: {transaction}")

    if not refund_payment_in.amount_to_refund:
        refund_payment_in.amount_to_refund = transaction.amount

    payment_service = PaymentService(
        session, background_tasks, gateway_id=transaction.driver
    )
    result = payment_service.refund_payment(
        transaction=transaction,
        refund_payment_in=refund_payment_in,
        client=commons["client"],
    )
    logger.debug(f"result: {result}")
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )


# TODO move to admin apis
@router_v1.get("/get_payment_status")
async def get_payment_status(
    background_tasks: BackgroundTasks,
    transaction_id: str = Query(..., description="Transaction id"),
    recheck: bool = Query(False, description="Recheck payment status"),
    entity: str = Query("transaction", description="Entity eg transaction or refund"),
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    """Get payment status from transaction id."""
    data = {}
    if entity == "transaction":
        data["entity"] = ["transaction"]
        data["event"] = "transaction"
        statement = select(Transaction).where(Transaction.id == transaction_id)

        transactions = session.exec(statement)
        transaction = transactions.first()

        if not transaction:
            logger.critical(f"transaction not found: {transaction_id}")
            raise NotFoundException(message="Transaction not found")

        driver_id = transaction.driver
        data["driver"] = driver_id
        if not recheck:
            data["transaction"] = json.loads(transaction.json())
        else:
            payment_service = PaymentService(session, background_tasks, driver_id)
            transaction = payment_service.get_payment_status(transaction, send_callback=False)
            data["transaction"] = json.loads(transaction.json())
    elif entity == "refund":
        data["entity"] = ["refund"]
        data["event"] = "refund"
        statement = select(RefundTransaction).where(RefundTransaction.refund_id == transaction_id)

        refund_transactions = session.exec(statement)
        refund_transaction = refund_transactions.first()

        if not refund_transaction:
            logger.critical(f"Refund not found for transaction: {transaction_id}")
            raise NotFoundException(
                message=f"Refund not found for transaction {transaction_id}"
            )

        if not recheck:
            data["refund"] = json.loads(refund_transaction.json())
        else:
            payment_service = PaymentService(
                session, background_tasks, refund_transaction.transaction.driver
            )
            refund_transaction = payment_service.get_refund_status(
                refund_transaction, send_callback=False
            )
            data["refund"] = json.loads(refund_transaction.json())
    return JSONResponse(data)


@router_v1.post("/retry_payment")
async def retry_payment():
    """Retry payment."""
    return


@router_v1.post("/register_callback_url")
async def register_callback_url():
    """Register callback url from razorpay."""
    return

@router_v1.get("/get_transaction_by_payment_id")
async def get_transaction_by_payment_id(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
    payment_id: str=Query(..., description="Payment id"),
    driver_id: str=Query(..., description="driver id"),
):
    try:
        payment_service = PaymentService(session, background_tasks, driver_id)
        transaction = payment_service.get_transaction_by_payment_id(payment_id=payment_id)
        return JSONResponse(json.loads(transaction))
    except Exception as ex:
        raise NotFoundException(message=f"{str(ex)}")









