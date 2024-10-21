"""Module contains apis."""
from loguru import logger
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from payment_app.configs.db import get_session
from payment_app.models import ClientGateway

from payment_app.dependencies.verify_api_key import verify_api_key
from payment_app.models.qr_codes import QRCode
from payment_app.schemas.requests.v1.qr_code_in import QRCodeIn

from payment_app.services.payment_service import PaymentService
from payment_app.lib.errors import NotFoundException, UnprocessableEntity

router_qr_code_v1 = APIRouter(
    prefix="/v1",
    tags=["QR Code"],
    responses={
        403: {"description": "Not Allowed"},
        200: {"description": "Everything is ok"},
        422: {"description": "Unprocessable Entity"},
        409: {"description": "conflict in request params"},
    },
)

@router_qr_code_v1.post("/create_qr_code")
async def create_qr_code(
    background_tasks: BackgroundTasks,
    create_qr_code_in: QRCodeIn,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    """Create qr code to start payment."""
    statement = (
        select(ClientGateway)
        .where(ClientGateway.active == True)
        .where(ClientGateway.client_id == commons["client"].id)
        .where(ClientGateway.driver_id == create_qr_code_in.driver)
    )
    results = session.exec(statement)
    gateway = results.first()
    if gateway:
        gateway_id = create_qr_code_in.driver
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
            logger.critical(f"driver_id is not registered: {create_qr_code_in.driver}")
            raise NotFoundException(message="gateway id provided by client not found")
    create_qr_code_in.driver = gateway_id
    payment_service = PaymentService(session, background_tasks, gateway_id=gateway_id)
    result = payment_service.create_qr_code(
        create_qr_code_in=create_qr_code_in,
        client=commons["client"],
        client_version=commons["client_version"]
    )
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )

@router_qr_code_v1.put("/close_qr_code/{id}")
async def close_qr_code(
    background_tasks: BackgroundTasks,
    id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    """Close qr code to after payment."""
    statement = (
        select(QRCode)
        .where(QRCode.id == id)
    )
    results = session.exec(statement)
    qr_code = results.first()

    if not qr_code:
        logger.critical(f"QR code not found: {id}")
        raise NotFoundException(message="QR code not found")

    if qr_code.status != "active":
        raise UnprocessableEntity("Already closed!")

    payment_service = PaymentService(session, background_tasks, gateway_id=qr_code.driver)
    result = payment_service.close_qr_code(
            qr_code.qr_id
        )
    logger.debug(f"result: {result}")
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )


@router_qr_code_v1.get("/get_qr_code_status/{qr_id}")
async def get_qr_code_status(
    background_tasks: BackgroundTasks,
    qr_id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    """Get qr code status."""
    statement = (
        select(QRCode)
        .where(QRCode.id == qr_id)
    )
    results = session.exec(statement)
    qr_code = results.first()
    if not qr_code:
        logger.critical(f"QR code not found: {id}")
        raise NotFoundException(message="QR code not found")
    payment_service = PaymentService(session, background_tasks, gateway_id=qr_code.driver)
    qr_details = payment_service.get_qr_code_status(qr_code.qr_id)
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": qr_details,
        }
    )

