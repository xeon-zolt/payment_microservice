"""Fast api app."""
import sys

import loguru
import ulid
import uvicorn
from fastapi import BackgroundTasks
from fastapi import Body, Depends, FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlmodel import Session

from payment_app.configs.db import get_session
from payment_app.payment_apis.apis_v1 import router_v1
from payment_app.payment_apis.payment_link_v1 import router_payment_link_v1
from payment_app.payment_apis.dispute_v1 import router_dispute_v1
from payment_app.payment_apis.document_v1 import router_dispute_document_v1
from payment_app.services.payment_service import PaymentService
from payment_app.payment_apis.qr_code_v1 import router_qr_code_v1
from payment_app.admin_apis.apis_v1 import router_v1 as router_v1_admin
from payment_app.utils import parse_body

from payment_app.lib.errors import CustomException

app = FastAPI()

logger = loguru.logger
logger.remove()
logger.add(
    sys.stdout,
    format="{time} - {level} - ({extra[request_id]}) {message} ",
    level="INFO",
    backtrace=True,
    diagnose=True,
)

logger.add(sys.stderr, backtrace=True, diagnose=True)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requersts."""
    request_id = str(ulid.ulid())
    with logger.contextualize(request_id=request_id):
        logger.info("Request started")
        return await call_next(request)


def init_listeners(app_: FastAPI) -> None:
    """Exception Handler."""
    @app_.exception_handler(CustomException)
    def custom_exception_handler(request: Request, exc: CustomException):
        try:
            return JSONResponse(
                status_code=exc.code,
                content={"error_code": exc.error_code, "message": exc.message},
            )
        except Exception as ex:
            logger.error(f"Request failed: {ex}")
            return JSONResponse(content={"success": False}, status_code=500)


def custom_openapi():
    """Custom open api."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Payments Microservice",
        version="0.0.1",
        description="Apis for Payments",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://www.1knetworks.com/assets/icons/1k-logo.svg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(router_v1)
app.include_router(router_payment_link_v1)
app.include_router(router_v1_admin)
app.include_router(router_qr_code_v1)
app.include_router(router_dispute_v1)
app.include_router(router_dispute_document_v1)
init_listeners(app_=app)


@app.get("/ping")
async def pong():
    """Get api for initial testing."""
    return {"ping": "pong!"}


@app.post("/callback/icici/cib")
async def pong1():
    """Get api for initial callback testing."""
    logger.info("cib callback  hit")
    return {"success": "true"}


@app.post("/callback/{payment_gateway}/{driver_id}/{_type}")
async def paytm_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    payment_gateway: str,
    driver_id: str,
    _type: str,
    session: Session = Depends(get_session),
    request_body: bytes = Depends(parse_body),
):
    """Post api for paytm callback handler."""
    logger.info("callback api hit")
    logger.info(request_body)
    # converting bytes str to dict
    paytm_params = None
    if _type == "payment":
        paytm_params = await request.form()
    elif _type == "refund":
        paytm_params = await request.json()
    logger.info(dict(paytm_params))
    payload = dict(paytm_params)
    request = {
        "request_body": payload,
        "request_headers": request.headers,
        "raw_request": request_body,
    }
    logger.debug(f"{payment_gateway} callback request: {request}")
    payment_service = PaymentService(session, background_tasks, driver_id)
    logger.debug(f"{payment_gateway} callback service: {payment_service}")
    callback_type = _type.lower()
    return payment_service.process_callback(request, callback_type)


@app.post("/callback/{payment_gateway}/{driver_id}")
async def gateway_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    payment_gateway: str,
    driver_id: int,
    session: Session = Depends(get_session),
    payload: dict = Body(...),
):
    """
    make entry in transaction_communications table
    and remove once client have responded in success
    """
    logger.info(f"{payment_gateway} callback hit")
    logger.info(f"callback payload: {payload}")
    callback_type = ""
    req_body = await request.body()
    raw_request = bytes.decode(req_body)
    request = {
        "request_body": payload,
        "request_headers": request.headers,
        "raw_request": raw_request,
    }
    logger.debug(f"{payment_gateway} callback request: {request}")
    payment_service = PaymentService(session, background_tasks, driver_id)
    logger.debug(f"{payment_gateway} callback service: {payment_service}")
    return payment_service.process_callback(request, callback_type)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
