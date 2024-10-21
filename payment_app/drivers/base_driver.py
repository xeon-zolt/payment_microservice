"""Module for payment drivers"""
from abc import abstractmethod
from typing import Union
from fastapi import UploadFile
from typing import List

from fastapi import Request, Body
from payment_app.models.dispute import Dispute, DisputeEvidence
from payment_app.models.qr_codes import QRCode
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.models.transaction import Transaction
from payment_app.schemas.requests.v1.create_payment_link_in import NotifyMedium
from payment_app.schemas.requests.v1.make_payment_in import MakePaymentInRazorpay, MakePaymentInPaytm
from payment_app.schemas.requests.v1.refund_payment_in import RefundPaymentIn


class BaseDriver:
    """Abstract class for payment drivers"""

    @abstractmethod
    def make_payment(
        self,
        transaction: Transaction,
        make_payment_in: Union[MakePaymentInRazorpay, MakePaymentInPaytm],
        client,
        client_version,
    ) -> Transaction:
        """Start payment."""

    @abstractmethod
    def refund_payment(
        self,
        transaction: Transaction,
        refund_transaction: RefundTransaction,
        refund_payment_in: RefundPaymentIn,
        client,
    ) -> RefundTransaction:
        """Start payment refund."""

    @abstractmethod
    def set_payment_status(self, request: Request):
        """Change payment status."""

    @abstractmethod
    def get_refund_status(self, refund: RefundTransaction, send_callback: bool):
        """Get refund transaction status."""

    @abstractmethod
    def get_payment_status(self, transaction: Transaction, send_callback: bool):
        """Get transaction status."""

    @abstractmethod
    def process_callback(self, request: dict, callback_type: str):
        """Handles callback for all payment events."""

    @abstractmethod
    def send_payment_link(self):
        """Sends payment link."""

    @abstractmethod
    def retry_refund(self, refund_transaction: RefundTransaction):
        """Retries refund in case refund didn't happen the first time."""

    @abstractmethod
    def create_payment_link(self, create_payment_link_in: dict, client, client_version) -> dict:
        """Create payment link to start payment."""

    @abstractmethod
    def resend_payment_link(self, plink_id: str, medium: NotifyMedium, transaction_id: str):
        """Resends payment link in case first one didn't work."""

    @abstractmethod
    def cancel_payment_link(self, plink_id: str, transaction: Transaction):
        """Cancels payment link."""

    @abstractmethod
    def get_payment_link_status(self, plink_id: str, transaction: Transaction):
        """Get payment link status."""

    @abstractmethod
    def create_qr_code(self, qr_code_req: dict, qr_code: QRCode, client, client_version):
        pass
    
    @abstractmethod
    def close_qr_code(self, qr_code_id: str):
        """Close qrcode to after payment."""

    @abstractmethod
    def get_qr_code_status(self, qr_id: str):
        """Get payment status from qrcode."""
        
    @abstractmethod
    def payment_methods(self):
        pass
    
    @abstractmethod
    def payment_downtime(self):
        pass

    @abstractmethod
    def upload_dispute_document(self, file: bytes):
        pass

    @abstractmethod
    def get_dispute_document(self, _id: str, driver_id: str):
        pass

    @abstractmethod
    def send_dispute_documents_draft(self, dispute_id, dispute_evidence: DisputeEvidence, dispute_evidence_type: str, dispute_evidence_detail: dict):
        pass

    @abstractmethod
    def accept_dispute_by_id(self, dispute: Dispute):
        pass
    
    @abstractmethod
    def contest_dispute_by_id(self, dispute: Dispute):
        pass
    
    @abstractmethod
    def payment_methods(self):
        pass
    
    @abstractmethod
    def payment_downtime(self):
        pass

    @abstractmethod
    def get_transaction_by_payment_id(self, payment_id: str):
        pass
