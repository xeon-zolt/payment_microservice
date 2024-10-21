"""Module with admin apis."""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
import json
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy import desc
from sqlmodel import Session, select
from sqlalchemy.sql import text
from fastapi.responses import JSONResponse
from payment_app.models.client_gateways import ClientGateway

from payment_app.dependencies.verify_api_key import verify_api_key
from payment_app.configs.db import get_session
from payment_app.lib.errors.error_handler import NotFoundException
from payment_app.models.client_gateways import ClientGateway
from payment_app.lib.errors.error_handler import InternalServerException, NotFoundException
from payment_app.models.access_client_relation import AccessClientMapper
from payment_app.models.access_points import AccessPoint
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.models.qr_codes import QRCode
from payment_app.models.transaction import Transaction
from payment_app.services.payment_service import PaymentService

from payment_app.services.payment_service import PaymentService
from payment_app.utils import custom_json_serializer

router_v1 = APIRouter(
    prefix="/admin/v1",
    tags=["Admin APIs"],
    responses={
        403: {"description": "Not Allowed"},
        200: {"description": "Everything is ok"},
        422: {"description": "Unprocessable Entity"},
        409: {"description": "conflict in request parms"},
    },
)

@router_v1.get("/get_transaction/{transaction_id}")
@router_v1.get("/get_transactions")
async def get_transactions(
    transaction_id: Optional[str] = None,
    page: int = 0,
    limit: int = Query(default=10, lte=100),
    ordering: str = Query(default="-created_at"),
    qr_id: str = Query(default=""),
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    """
    Get transactions
    """
    if transaction_id:
        transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
        if transaction:
            results = json.loads(transaction.json())
        else:
            raise NotFoundException(message="Transaction not found!")
    elif qr_id:
        _number_of_transactions = session.query(Transaction).where(Transaction.gateway_order_id == qr_id).count()
        if '-' == ordering[0]:
            ordering = ordering[1:]
            transactions = session.exec(
                select(Transaction).where(Transaction.gateway_order_id == qr_id).order_by(desc(ordering)).offset((page-1)*limit).limit(limit)
            ).all()
        else:
            transactions = session.exec(
                select(Transaction).where(Transaction.gateway_order_id == qr_id).order_by(ordering).offset((page-1)*limit).limit(limit)
            ).all()
        results = {
            "results": [json.loads(transaction.json()) for transaction in transactions],
            "total": _number_of_transactions
        }
    else:
        _number_of_transactions = session.query(Transaction).count()
        if '-' == ordering[0]:
            ordering = ordering[1:]
            transactions = session.exec(
                select(Transaction).order_by(desc(ordering)).offset((page-1)*limit).limit(limit)
            ).all()
        else:
            transactions = session.exec(
                select(Transaction).order_by(ordering).offset((page-1)*limit).limit(limit)
            ).all()
        results = {
            "results": [json.loads(transaction.json()) for transaction in transactions],
            "total": _number_of_transactions
        }

    return JSONResponse(results)

@router_v1.get("/get_refund_transactions/{refund_transaction_id}")
@router_v1.get("/get_refund_transactions")
async def get_refund_transactions(
    refund_transaction_id: Optional[str] = None,
    page: int = 0,
    limit: int = Query(default=10, lte=100),
    ordering: str = Query(default="-created_at"),
    filters: str = Query(default=""),
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    """
    Get refund transactions
    """
    if refund_transaction_id:
        refund_transaction = session.query(RefundTransaction).filter(
            RefundTransaction.id == refund_transaction_id
        ).first()
        if refund_transaction:
            results = json.loads(refund_transaction.json())
        else:
            raise NotFoundException(message="Refund Transaction not found!")
    else:
        _number_of_refund_transactions = session.query(RefundTransaction).count()
        if '-' == ordering[0]:
            ordering = ordering[1:]
            refund_transactions = session.exec(
                select(RefundTransaction).order_by(desc(ordering)).offset((page-1)*limit).limit(limit)
            ).all()
        else:
            refund_transactions = session.exec(
                select(RefundTransaction).order_by(ordering).offset((page-1)*limit).limit(limit)
            ).all()
        results = {
            "results": [json.loads(
                refund_transaction.json()
            ) for refund_transaction in refund_transactions],
            "total": _number_of_refund_transactions
        }

    return JSONResponse(results)


@router_v1.get("/get_qr_store_codes/{store_id}")
@router_v1.get("/get_qr_codes/{qr_code_id}")
@router_v1.get("/get_qr_codes")
async def get_qr_codes(
    qr_code_id: Optional[str] = None,
    store_id: Optional[str] = None,
    page: int = 0,
    limit: int = Query(default=10, lte=100),
    ordering: str = Query(default="-created_at"),
    filters: str = Query(default=""),
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    """
    Get QR Codes
    """
    if qr_code_id:
        qr_code = session.query(QRCode).filter(
            QRCode.id == qr_code_id
        ).first()
        if qr_code:
            results = json.loads(qr_code.json())
        else:
            raise NotFoundException(message="QR Code not found!")
    elif store_id:
        query = text(f"""select * from qr_codes where JSON_EXTRACT(notes,'$.store_id') = '{store_id}' AND status <> 'failed'""")
        qr_codes = session.execute(query).all()
        if qr_codes:
            results = {
                    "results": [json.loads(json.dumps(dict(qr_code), default=custom_json_serializer)) for qr_code in qr_codes],
                }
        else:
            raise NotFoundException(message="QR Code not found!")
    else:
        _number_of_qr_codes = session.query(QRCode).count()
        if '-' == ordering[0]:
            ordering = ordering[1:]
            qr_codes = session.exec(
                select(QRCode).where(QRCode.status != 'failed').order_by(desc(ordering)).offset((page-1)*limit).limit(limit)
            ).all()
        else:
            qr_codes = session.exec(
                select(QRCode).where(QRCode.status != 'failed').order_by(ordering).offset((page-1)*limit).limit(limit)
            ).all()
        results = {
            "results": [json.loads(
                qr_code.json()
            ) for qr_code in qr_codes],
            "total": _number_of_qr_codes
        }

    return JSONResponse(results)

@router_v1.get("/get_endpoints")
async def get_Endpoints(
    session: Session = Depends(get_session)
):
    """
    Return all endpoints
    """
    try:
        statement = select(AccessPoint)
        endpoints = session.exec(statement).all()
        number_of_endpoints = session.query(AccessPoint).count()
        results = {
            "endpoints": [json.loads(endpoint.json()) for endpoint in endpoints],
            "total": number_of_endpoints
        }
        return JSONResponse(results)
    except Exception as e:
        raise InternalServerException(message=f"{str(e)}")

@router_v1.get("/get_client_endpoints/{client_id}")
async def get_client_endpoints(
    client_id: str,
    session: Session = Depends(get_session),
):
    """
    Return client endpoints relation
    """
    try:
        endpoints = []
        statement = select(AccessPoint).join(AccessClientMapper).where(AccessClientMapper.client_id == client_id)
        related_endpoints = session.exec(statement)
        for related_endpoint in related_endpoints:
            endpoints.append(json.loads(related_endpoint.json()))
        return JSONResponse({
            "client_id": client_id,
            "endpoints": endpoints
        })
    except Exception as e:
        raise InternalServerException(message=f"{str(e)}")
    
@router_v1.get("/get_payment_methods/{driver_id}")
async def get_payment_methods(
    background_tasks: BackgroundTasks,
    driver_id: Literal[1,2,'1','2'],
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    statement = (
        select(ClientGateway)
        .where(ClientGateway.active == True)
        .where(ClientGateway.client_id == commons["client"].id)
        .where(ClientGateway.driver_id == driver_id)
    )
    results = session.exec(statement)
    gateway = results.first()
    if gateway:
        gateway_id = driver_id
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
            gateway_id = gateway.driver_id
        else:
            raise NotFoundException(message=f"gateway id provided by client not found")
            
    payment_service = PaymentService(session, background_tasks, gateway_id=gateway_id)
    result = payment_service.get_payment_methods()
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )
    
@router_v1.get("/payment_downtime/{driver_id}")
async def get_payment_downtime(
    background_tasks: BackgroundTasks,
    driver_id: Literal[1,2,'1','2'],
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    statement = (
        select(ClientGateway)
        .where(ClientGateway.active == True)
        .where(ClientGateway.client_id == commons["client"].id)
        .where(ClientGateway.driver_id == driver_id)
    )
    results = session.exec(statement)
    gateway = results.first()
    if gateway:
        gateway_id = driver_id
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
            gateway_id = gateway.driver_id
        else:
            raise NotFoundException(message=f"gateway id provided by client not found")
            
    payment_service = PaymentService(session, background_tasks, gateway_id=gateway_id)
    result = payment_service.get_payment_downtime()
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )
