"""Module contains apis."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from loguru import logger

from payment_app.configs.db import get_session
from payment_app.dependencies.verify_api_key import verify_api_key
from payment_app.models.client_gateways import ClientGateway
from payment_app.models.transaction import Transaction, PAYMENT_TYPE, STATUS_SUCCESS
from payment_app.schemas.requests.v1.create_payment_link_in import (
    CreatePaymentLinkIn, ResendNotifyPaymentLinkIn
)
from payment_app.services.payment_service import PaymentService
from payment_app.lib.errors import NotFoundException,UnprocessableEntity

router_payment_link_v1 = APIRouter(
    prefix="/v1",
    tags=["Payment Link"],
    responses={
        403: {"description": "Not Allowed"},
        200: {"description": "Everything is ok"},
        422: {"description": "Unprocessable Entity"},
        409: {"description": "conflict in request params"},
    },
)


@router_payment_link_v1.post("/create_payment_link")
async def create_payment_link(
    background_tasks: BackgroundTasks,
    create_payment_link_in: CreatePaymentLinkIn,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    """Create payment link."""
    statement = (
        select(ClientGateway)
        .where(ClientGateway.active == True)
        .where(ClientGateway.client_id == commons["client"].id)
        .where(ClientGateway.driver_id == create_payment_link_in.driver_id)
    )
    results = session.exec(statement)
    gateway = results.first()
    if gateway:
        gateway_id = create_payment_link_in.driver_id
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
            logger.critical(f"driver_id is not registered: {create_payment_link_in.driver_id}")
            raise NotFoundException(message=f"gateway id provided by client not found")
        
    create_payment_link_in.driver_id = gateway_id
    payment_service = PaymentService(session, background_tasks, gateway_id=gateway_id)

    result = payment_service.create_payment_link(
        create_payment_link_in=create_payment_link_in,
        client=commons["client"],
        client_version=commons["client_version"],
    )
    logger.debug(f"result:  =====> {result}")
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )

@router_payment_link_v1.put("/cancel_payment_link/{transaction_id}")
async def cancel_payment_link(
    background_tasks: BackgroundTasks,
    transaction_id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    """Cancel payment link."""
    logger.debug(f"cancel_payment_link: {transaction_id}")
    statement = (
        select(Transaction)
        .where(Transaction.id == transaction_id)
        .where(Transaction.payment_type == PAYMENT_TYPE)
    )
    results = session.exec(statement)
    transaction = results.first()

    if not transaction:
        logger.critical(f"transaction not found: {transaction_id}")
        raise NotFoundException(message="transaction id not found")

    if transaction.status != "pending":
        logger.critical(f"transaction not issud: {transaction_id}")
        raise UnprocessableEntity("transaction not issued")

    payment_service = PaymentService(session, background_tasks, gateway_id=transaction.driver)
    result = payment_service.cancel_payment_link(
            transaction.api_response["id"],
            transaction
        )
    logger.debug(f"result: {result}")
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )


@router_payment_link_v1.post("/resend_payment_link")
async def resend_payment_link(
    background_tasks: BackgroundTasks,
    resend_notify_payment_link_in: ResendNotifyPaymentLinkIn,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    """Resend payment link."""
    logger.debug(f"resend_payment_link: {resend_notify_payment_link_in}")
    statement = (
        select(Transaction)
        .where(Transaction.id == resend_notify_payment_link_in.transaction_id)
        .where(Transaction.payment_type == PAYMENT_TYPE)
    )
    results = session.exec(statement)
    transaction = results.first()

    if not transaction:
        logger.critical(f"transaction not found: {resend_notify_payment_link_in.transaction_id}")
        raise HTTPException(
                status_code=404,
                detail={
                    "headers": commons["request_headers"],
                    "error": "transaction id not found",
                },
            )

    if transaction.status == STATUS_SUCCESS:
        raise UnprocessableEntity("transaction already paid!")

    payment_service = PaymentService(session, background_tasks, gateway_id=transaction.driver)
    result = payment_service.resend_payment_link(
            transaction.api_response["id"],
            resend_notify_payment_link_in.medium._name_,
            resend_notify_payment_link_in.transaction_id
        )
    logger.debug(f"result: {result}")
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )

@router_payment_link_v1.get("/get_payment_link_status/{transaction_id}")
async def get_payment_link_status(
    background_tasks: BackgroundTasks,
    transaction_id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    """Get payment link status."""
    statement = (
        select(Transaction)
        .where(Transaction.id == transaction_id)
        .where(Transaction.payment_type == PAYMENT_TYPE)
    )
    results = session.exec(statement)
    transaction = results.first()

    if not transaction:
        logger.critical(f"transaction not found: {transaction_id}")
        raise NotFoundException(message=f"transaction not found {transaction_id}")

    payment_service = PaymentService(session, background_tasks, gateway_id=transaction.driver)
    result = payment_service.get_payment_link_status(transaction.api_response["id"], transaction)
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )
