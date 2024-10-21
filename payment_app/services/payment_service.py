
"""Module with payment services."""
import json
import os
from typing import Union

import toml

from fastapi import BackgroundTasks
from loguru import logger
from sqlmodel import Session, select
from fastapi import File, UploadFile
from typing import List

from payment_app.drivers.base_driver import BaseDriver
from payment_app.drivers.paytm_driver import PaytmDriver
from payment_app.drivers.razorpay_driver import RazorpayDriver
from payment_app.lib.errors.error_handler import InternalServerException, NotFoundException
from payment_app.models import Transaction
from payment_app.models.dispute import DisputeEvidence
from payment_app.models.dispute import Dispute
from payment_app.models.payment_links import PaymentLink
from payment_app.models.qr_codes import QRCode
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.schemas.requests.v1.create_payment_link_in import CreatePaymentLinkIn, NotifyMedium
from payment_app.schemas.requests.v1.make_payment_in import (
    MakePaymentInRazorpay, MakePaymentInPaytm
)
from payment_app.schemas.requests.v1.refund_payment_in import RefundPaymentIn
from payment_app.schemas.requests.v1.qr_code_in import QRCodeIn
from payment_app.utils import get_driver_name


class PaymentService:
    """Payment service class."""
    __driver_name: str = None
    __driver: BaseDriver = None

    def __init__(
            self, session: Session, background_tasks: BackgroundTasks, gateway_id=None
    ):
        """Class constructor."""
        super().__init__()
        self.session = session
        self.background_task = background_tasks
        try:
            payment_config = toml.load(os.environ.get("PAYMENT_CONFIG_PATH", "config.toml"))
        except Exception as ex:
            logger.error(f"Request failed: {ex}")
            raise InternalServerException(message="Toml file not found or readable")

        if not gateway_id:
            self.gateway_id = payment_config["default"]["id"]
        else:
            self.gateway_id = int(gateway_id)

        payment_driver = None

        for gateway in payment_config["gateway"]:
            if self.gateway_id == gateway["id"]:
                payment_driver = gateway

        if not payment_driver:
            logger.error("Request failed: Gateway not found")
            raise NotFoundException(message="payment driver not found")

        self.__driver_name = payment_driver["driver"]

        if payment_driver["driver"] == "razorpay":
            logger.info("Initializing razorpay driver")
            self.__driver: BaseDriver = RazorpayDriver(
                session,
                background_tasks,
                payment_driver["key_id"],
                payment_driver["key_secret"],
                payment_driver["webhook_secret"],
            )

        if payment_driver["driver"] == "paytm":
            self.__driver: BaseDriver = PaytmDriver(
                session,
                background_tasks,
                payment_driver["client_id"],
                payment_driver["mid"],
                payment_driver["key"],
                payment_driver["website"],
                payment_driver["callback_url"]
            )

    def make_payment(
        self,
        make_payment_in: Union[MakePaymentInRazorpay, MakePaymentInPaytm],
        client,
        client_version
    ):
        """Start payment."""
        if get_driver_name(self.gateway_id) == "paytm":
            statement = select(Transaction).where(
                Transaction.source_id == make_payment_in.source_id
            )
            transaction = self.session.exec(statement).first()
            if transaction:
                logger.info("transaction already exists")
                return {
                    "entity": "transaction",
                    "transaction": json.loads(transaction.json()),
                    "driver": self.__driver_name,
                }
        if make_payment_in.payment_type == 'link':
            store_type = 'bd_store_id'
        else:
            store_type = 'pos_store_id'
        transaction = Transaction(
            total_amount=make_payment_in.total_amount,
            amount=make_payment_in.amount_to_pay,
            source_id=make_payment_in.source_id,
            payment_type=make_payment_in.payment_type,
            store_id=make_payment_in.store_id,
            client_id=client.id,
            additional_info=make_payment_in.additional_info,
            api_version=1.1,
            client_version=client_version,
            driver=self.gateway_id,
            store_type=store_type,
        )
        logger.info(f"saving transaction {transaction}")
        self.session.add(transaction)
        self.session.commit()

        transaction = self.__driver.make_payment(
            transaction, make_payment_in, client, client_version
        )

        return {
            "entity": "transaction",
            "transaction": json.loads(transaction.json()),
            "driver": self.__driver_name,
        }


    def get_payment_status(self, transaction, send_callback=False):
        """Return payment status."""
        return self.__driver.get_payment_status(transaction, send_callback)

    def get_refund_status(self, refund, send_callback=True):
        """Return refund status."""
        return self.__driver.get_refund_status(refund, send_callback)

    def retry_refund(self, refund):
        """Retry refund."""
        return self.__driver.retry_refund(refund)

    def process_callback(self, request: dict, callback_type: str):
        """Process callback from razorpay."""
        logger.info("processing callback")
        return self.__driver.process_callback(request, callback_type)

    def refund_payment(self, transaction, refund_payment_in: RefundPaymentIn, client):
        """Start payment refund."""
        logger.info("refunding payment")
        refund_transaction = RefundTransaction(transaction_id=transaction.id,
                                               amount=refund_payment_in.amount_to_refund)
        self.session.add(refund_transaction)
        self.session.commit()
        self.session.refresh(refund_transaction)
        refund = self.__driver.refund_payment(
            transaction,
            refund_transaction,
            refund_payment_in,
            client,
        )

        return json.loads(refund.json())

    def create_payment_link(
        self, create_payment_link_in: CreatePaymentLinkIn, client, client_version
    ):
        """Create payment link."""
        return self.__driver.create_payment_link(create_payment_link_in, client, client_version)

    def cancel_payment_link(self, plink_id: str, transaction: Transaction):
        """Cancel payment link."""
        return self.__driver.cancel_payment_link(plink_id, transaction)

    def resend_payment_link(self, plink_id: str, medium: NotifyMedium, transaction_id: str):
        """Resend payment link."""
        return self.__driver.resend_payment_link(plink_id, medium, transaction_id)

    def get_payment_link_status(self, plink_id: str, transaction: Transaction):
        """Return payment link status."""
        return self.__driver.get_payment_link_status(plink_id, transaction)

    def create_qr_code(self, create_qr_code_in: QRCodeIn, client, client_version):
        qr_code = QRCode(
            usage=create_qr_code_in.usage,
            type=create_qr_code_in.type,
            payment_amount=create_qr_code_in.payment_amount,
            is_fixed_amount=create_qr_code_in.is_fixed_amount,
            driver=self.gateway_id
        )
        self.session.add(qr_code)
        self.session.commit()
        self.session.refresh(qr_code)
        
        return self.__driver.create_qr_code(create_qr_code_in, qr_code, client, client_version)

    def close_qr_code(self, qr_code_id: str):
        """Close qr code after payment."""
        return self.__driver.close_qr_code(qr_code_id)

    def get_qr_code_status(self, qr_code_id: str):
        """Get qr code status."""
        return self.__driver.get_qr_code_status(qr_code_id)

    def upload_dispute_document(self, file: bytes, dispute_id: str):
        return self.__driver.upload_dispute_document(file, dispute_id)
    
    def get_dispute_document(self, _id: str):
        return self.__driver.get_dispute_document(_id)
    
    def send_dispute_documents_draft(self, dispute_id, dispute_evidence: DisputeEvidence, dispute_evidence_type: str, dispute_evidence_detail: dict):
        return self.__driver.send_dispute_documents_draft(dispute_id, dispute_evidence, dispute_evidence_type, dispute_evidence_detail)
    
    def accept_dispute(self, dispute: Dispute):
        return self.__driver.accept_dispute_by_id(dispute)
    
    def contest_dispute(self, dispute: Dispute):
        return self.__driver.contest_dispute_by_id(dispute)

    
    def get_payment_methods(self):
        return self.__driver.payment_methods()
    
    def get_payment_downtime(self):
        return self.__driver.payment_downtime()
    
    def get_transaction_by_payment_id(self, payment_id: str):
        return self.__driver.get_transaction_by_payment_id(payment_id)

