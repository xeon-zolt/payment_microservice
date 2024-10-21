import json
from loguru import logger
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
import datetime
from payment_app.configs.db import get_session
from sqlmodel import Session, select
from sqlalchemy import desc

from payment_app.dependencies.verify_api_key import verify_api_key

from payment_app.lib.errors import NotFoundException, UnprocessableEntity
from payment_app.models import Dispute, DisputeEvidence, ClientGateway
from typing import  Literal
from payment_app.models.dispute import DisputDocuments

from payment_app.services.payment_service import PaymentService

router_dispute_v1 = APIRouter(
    prefix="/v1",
    tags=["Disputes"],
    responses={
        403: {"description": "Not Allowed"},
        200: {"description": "Everything is ok"},
        422: {"description": "Unprocessable Entity"},
        409: {"description": "conflict in request params"},
    },
)

@router_dispute_v1.get("/disputes")
async def get_disputes(
    page: int = 0,
    limit: int = Query(default=10, lte=100),
    ordering: str = Query(default="-created_at"),
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    _number_of_disputes = session.query(Dispute).count()
    if '-' == ordering[0]:
        ordering = ordering[1:]
        disputes = session.exec(select(Dispute).order_by(desc(ordering)).offset((page-1)*limit).limit(limit)).all()
    else:
        disputes = session.exec(select(Dispute).order_by(ordering).offset((page-1)*limit).limit(limit)).all()
    results = {
        "results": [json.loads(dispute.json()) for dispute in disputes],
        "total": _number_of_disputes
    }
    return JSONResponse(results)

@router_dispute_v1.get("/disputes/{dispute_id}")
async def get_dispute(
    dispute_id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    results = {}
    query = select(Dispute).where(Dispute.id == dispute_id)
    dispute = session.exec(query).first()
    
    if not dispute:
        raise NotFoundException(message="Dispute not found!")
    
    results = json.loads(dispute.json())
    results["dispute_evidence"] = {}
    if dispute.dispute_evidence:
        results["dispute_evidence"]["amount"]= dispute.dispute_evidence.amount
        results["dispute_evidence"]["summary"]= dispute.dispute_evidence.summary
        results["dispute_evidence"]["submitted_at"] = str(dispute.dispute_evidence.submitted_at)
        
        if dispute.dispute_evidence.billing_proof:
            results["dispute_evidence"]["billing_proof"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.billing_proof]
        if dispute.dispute_evidence.cancellation_proof:
            results["dispute_evidence"]["cancellation_proof"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.cancellation_proof]
        if dispute.dispute_evidence.shipping_proof:
            results["dispute_evidence"]["shipping_proof"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.shipping_proof]
        if dispute.dispute_evidence.explanation_letter:
            results["dispute_evidence"]["explanation_letter"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.explanation_letter]
        if dispute.dispute_evidence.refund_confirmation:
            results["dispute_evidence"]["refund_confirmation"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.refund_confirmation]
        if dispute.dispute_evidence.customer_communication:
            results["dispute_evidence"]["customer_communication"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.customer_communication]
        if dispute.dispute_evidence.proof_of_service:
            results["dispute_evidence"]["proof_of_service"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.proof_of_service]
        if dispute.dispute_evidence.refund_confirmation:
            results["dispute_evidence"]["refund_confirmation"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.refund_confirmation]
        if dispute.dispute_evidence.access_activity_log:
            results["dispute_evidence"]["access_activity_log"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.access_activity_log]
        if dispute.dispute_evidence.refund_cancellation_policy:
            results["dispute_evidence"]["refund_cancellation_policy"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.refund_cancellation_policy]
        if dispute.dispute_evidence.term_and_conditions:
            results["dispute_evidence"]["term_and_conditions"] = [get_document(document_id, session) for document_id in dispute.dispute_evidence.term_and_conditions]
        
        if dispute.dispute_evidence.others:
            for document in dispute.dispute_evidence.others:
                results["dispute_evidence"]["others"] = []
                doc = {
                    "type": document["type"],
                    "document_ids": [get_document(document_id, session) for document_id in document["document_ids"]]
                }
                results["dispute_evidence"]["others"].append(doc)
    
    return JSONResponse({"results": results})

def get_document(document_id: str, session: Session):
    query = select(DisputDocuments).where(DisputDocuments.document_id == document_id)
    document = session.exec(query).first()
    return json.loads(document.json())

@router_dispute_v1.post("/disputes/accept/{dispute_id}")
async def accept_dispute(
    background_tasks: BackgroundTasks,
    dispute_id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    statement = (
        select(Dispute)
        .where(Dispute.id == dispute_id)
    )
    results = session.exec(statement)
    dispute = results.first()
    
    if not dispute:
        logger.critical(f"Dispute not found: {id}")
        raise NotFoundException(message=f"Dispute not found")
    
    payment_service = PaymentService(session, background_tasks, gateway_id=dispute.driver_id)
    result = payment_service.accept_dispute(dispute)
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )
    
@router_dispute_v1.post("/disputes/contest/{dispute_id}")
async def contest_dispute(
    background_tasks: BackgroundTasks,
    dispute_id: str,
    session: Session = Depends(get_session),
    commons: dict = Depends(verify_api_key)
):
    statement = (
        select(Dispute)
        .where(Dispute.id == dispute_id)
    )
    results = session.exec(statement)
    dispute = results.first()
    
    if not dispute:
        logger.critical(f"Dispute not found: {dispute_id}")
        raise NotFoundException(message=f"Dispute not found")
    
    payment_service = PaymentService(session, background_tasks, gateway_id=dispute.driver_id)
    result = payment_service.contest_dispute(dispute)
    return JSONResponse(
        content={
            "client_version": commons["client_version"],
            "response": result,
        }
    )
