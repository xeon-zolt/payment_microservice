from loguru import logger
from fastapi import APIRouter, BackgroundTasks, Depends, Body
from fastapi.responses import JSONResponse
from fastapi import File, UploadFile, Form

from payment_app.configs.db import get_session
from sqlmodel import Session, select

from payment_app.dependencies.verify_api_key import verify_api_key

from payment_app.lib.errors import NotFoundException, UnprocessableEntity
from payment_app.lib.errors.error_handler import ForbiddenException, InternalServerException
from payment_app.models.dispute import Dispute, DisputeEvidence
from payment_app.services.payment_service import PaymentService
from payment_app.utils import update_dispute_evidence

router_dispute_document_v1 = APIRouter(
    prefix="/v1",
    tags=["Dispute Documents"],
    responses={
        403: {"description": "Not Allowed"},
        200: {"description": "Everything is ok"},
        422: {"description": "Unprocessable Entity"},
        409: {"description": "conflict in request params"},
    },
)

@router_dispute_document_v1.post("/documents")
async def save_documents(
    background_tasks: BackgroundTasks,
    file: bytes =  File(...),
    dispute_id: str = Form(...),
    dispute_evidence_type: str= Form(...),
    amount: int= Form(...),
    summary: str= Form(...),
    content_type: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        statement = select(Dispute).where(Dispute.id == dispute_id)
        dispute = session.exec(statement).first()
        if not dispute:
            raise NotFoundException
        if content_type not in ["image/jpg", "image/jpeg", "image/png", "application/pdf"]:
            raise UnprocessableEntity(
                message="Only 'jpg', 'jpeg', 'png' and 'pdf' formats are accepted."
            )
        if dispute.amount < amount:
            raise UnprocessableEntity(
                message="Amount can not be more than dispute amount."
            )
        payment_service = PaymentService(session, background_tasks, gateway_id=dispute.driver_id)
        dispute_evidence_detail = payment_service.upload_dispute_document(file=file, dispute_id=dispute_id)
        if not dispute.dispute_evidence_id:
            updated_dispute_evidence = DisputeEvidence(amount=amount, summary=summary)
        else:
            updated_dispute_evidence = dispute.dispute_evidence
        data = {
            "amount": updated_dispute_evidence.amount,
            "summary": updated_dispute_evidence.summary,
            "action": "draft"
        }
        updated_dispute_evidence = update_dispute_evidence(
                dispute_evidence_type=dispute_evidence_type, 
                dispute_evidence_detail=dispute_evidence_detail, 
                dispute_evidence=dispute.dispute_evidence,
                data=data
            )
        send_dispute_draft_response = payment_service.send_dispute_documents_draft(
            dispute_id=dispute_id, 
            data=data
        )
        session.add(updated_dispute_evidence)
        session.commit()
        return JSONResponse({
            "submission_detail": send_dispute_draft_response
        })
    except UnprocessableEntity as ex:
        raise UnprocessableEntity(message=ex.message)
    except ForbiddenException as ex:
        raise ForbiddenException(message=ex.message)
    except Exception as ex:
        raise InternalServerException(message=f"Error while Uploading file: {ex}")

@router_dispute_document_v1.get("/documents/{_id}/{driver_id}")
async def get_dispute_document(
    background_tasks: BackgroundTasks,
    _id: str,
    driver_id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key),
):
    try:
        payment_service = PaymentService(session, background_tasks, gateway_id=driver_id)
        document = payment_service.get_dispute_document(_id=_id)
        return({
            "result": document
        })
    except Exception as ex:
        raise InternalServerException(message=f"Error while fetching files.: {ex}")


