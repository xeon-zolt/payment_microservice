from typing import Optional, List
from sqlmodel import Relationship, SQLModel, Field, TIMESTAMP
from sqlalchemy import Column, TEXT, JSON
from datetime import datetime
from payment_app.models.timestampsmixin import TimeStampMixin


class DisputeBase(SQLModel):
    dispute_id: str = Field(nullable=False, sa_column=Column(unique=True))
    entity: str = Field(nullable=False)
    payment_id: str = Field(nullable=False)
    amount: int = Field(nullable=False)
    currency: str = Field(nullable=False, max_length=3)
    comments: str = Field(sa_column=Column(TEXT), nullable=True)
    gateway_dispute_id: str = Field(nullable=True)
    amount_deducted: int = Field(nullable=False)
    reason_code: str = Field(nullable=False)
    respond_by: datetime = Field(sa_column=Column(TIMESTAMP), nullable=False)
    status: str = Field(nullable=False)
    phase: str = Field(nullable=False)
    driver_created_at: datetime = Field(sa_column=Column(TIMESTAMP), nullable=False)
    # for connecting with transactions
    driver_id: int = Field(nullable=False)
    dispute_evidence_id: int = Field(default=None, foreign_key="dispute_evidence.id")


class Dispute(DisputeBase, TimeStampMixin, table=True):
    __tablename__ = "disputes"
    id: int = Field(default=None, primary_key=True, nullable=False)
    dispute_evidence: Optional["DisputeEvidence"] = Relationship(back_populates="dispute")


class DisputeEvidenceBase(SQLModel):
    amount: int = Field(nullable=True)
    summary: str = Field(sa_column=Column(TEXT), nullable=True)
    shipping_proof: list = Field(sa_column=Column(JSON, nullable=True))
    billing_proof: list = Field(sa_column=Column(JSON), nullable=True)
    cancellation_proof: list = Field(sa_column=Column(JSON), nullable=True)
    customer_communication: list = Field(sa_column=Column(JSON), nullable=True)
    proof_of_service: list = Field(sa_column=Column(JSON), nullable=True)
    explanation_letter: list = Field(sa_column=Column(JSON), nullable=True)
    refund_confirmation: list = Field(sa_column=Column(JSON), nullable=True)
    access_activity_log: list = Field(sa_column=Column(JSON), nullable=True)
    refund_cancellation_policy: list = Field(sa_column=Column(JSON), nullable=True)
    term_and_conditions: list = Field(sa_column=Column(JSON), nullable=True)
    others: list = Field(sa_column=Column(JSON), nullable=True)
    submitted_at: datetime = Field(sa_column=Column(TIMESTAMP), nullable=False)


class DisputeEvidence(DisputeEvidenceBase, TimeStampMixin, table=True):
    __tablename__ = "dispute_evidence"
    id: int = Field(default=None, primary_key=True, nullable=False)
    dispute: Optional["Dispute"] = Relationship(back_populates="dispute_evidence")
    dispute_documents: List["DisputDocuments"] = Relationship(back_populates="dispute_evidence")


class DisputDocumentsBase(SQLModel):
    dispute_evidence_id: int = Field(default=None, foreign_key="dispute_evidence.id")
    rzp_created_at: datetime = Field(nullable=False)
    display_name: str = Field(nullable=True)
    entity: str = Field(nullable=True)
    document_id: str = Field(nullable=True)
    mime_type: str = Field(nullable=True)
    size: str = Field(nullable=True)
    url: str = Field(sa_column=Column(TEXT), nullable=True)

class DisputDocuments(DisputDocumentsBase, TimeStampMixin, table=True):
    __tablename__ = "dispute_document"
    id: int = Field(default=None, primary_key=True, nullable=False)
    dispute_evidence: Optional["DisputeEvidence"] = Relationship(back_populates="dispute_documents")