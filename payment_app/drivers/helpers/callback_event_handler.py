"""Module for drivers's helper functions."""
from http import HTTPStatus
import datetime
from loguru import logger
from sqlmodel import Session, select, col
from payment_app.lib.errors.error_handler import NotFoundException

from payment_app.models import TransactionCallbacks
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.models.transaction import (
    Transaction,
    STATUS_FAILED,
    STATUS_SUCCESS,
)

from payment_app.models import QRCode

class CallbackEventHandler:
    """Payments event callback handler."""

    def __init__(self, session: Session) -> None:
        """Instantiate helper for callback events."""
        self.session = session

    def handle_payment_callback(self, transaction_callback: TransactionCallbacks, webhook_body: dict):
        """payment.captured, payment.failed, payment.authorized, payment_link.paid"""
        transaction_callback.type = "payment"
        transaction_callback.callback = webhook_body
        self.session.add(transaction_callback)
        self.session.commit()
        self.session.refresh(transaction_callback)
        logger.debug(f"Payment event: {webhook_body}")
        return self._update_payment_transaction(
            webhook_body["payload"]["payment"]["entity"]["order_id"],
            webhook_body["payload"]["payment"]["entity"]["id"],
            webhook_body["payload"]["payment"]["entity"]
        )

    def handle_refund_callback(self, transaction_callback: TransactionCallbacks, webhook_body: dict):
        """refund.created, refund.processed, refund.failed"""
        transaction_callback.type = "refund"
        transaction_callback.callback = webhook_body
        self.session.add(transaction_callback)
        self.session.commit()
        self.session.refresh(transaction_callback)
        logger.debug(f"Refund event: {webhook_body}")
        transaction = self._update_payment_transaction(
            webhook_body["payload"]["payment"]["entity"]["order_id"],
            # TODO check if this is correct
            webhook_body["payload"]["payment"]["entity"],
            webhook_body["payload"]["payment"]["entity"],
        )
        # if no refund is found, create one
        if (
            "refund_transaction_id"
            not in webhook_body["payload"]["refund"]["entity"]["notes"]
        ):
            refund_transaction = self._create_refund(
                transaction,
                webhook_body["payload"]["refund"]["entity"],
            )
        else:
            refund_transaction_id = webhook_body["payload"]["refund"][
                "entity"
            ]["notes"]["refund_transaction_id"]
            statement = select(RefundTransaction).where(
                RefundTransaction.id == refund_transaction_id
            )
            results = self.session.exec(statement)
            refund_transaction = results.first()
        # update refund response

        self._update_refund_transaction(
            refund_transaction,
            webhook_body["payload"]["refund"]["entity"],
        )
        return transaction

    def handle_qr_code_callback(self, webhook_body):
        """qr.created, qr.credited, qr.closed"""
        match webhook_body["event"]:
            case "qr_code.created":
                self._handle_qr_created_callback(webhook_body=webhook_body)
            case "qr_code.credited":
                self._handle_qr_credited_callback(webhook_body=webhook_body)
            case "qr_code.closed":
                self._handle_qr_closed_callback(webhook_body=webhook_body)
            case _:
                logger.error(f"unknown callback event received {webhook_body}")
                transaction_callback = TransactionCallbacks(
                    callback=webhook_body,
                    event=webhook_body["event"],
                    type="unknown"
                )
                self.session.add(transaction_callback)
                self.session.commit()
                self.session.refresh(transaction_callback)

    def _handle_qr_created_callback(self, webhook_body: dict):
        transaction_callback = TransactionCallbacks(
            callback=webhook_body,
            event=webhook_body["event"],
            type="qr_code"
        )
        self.session.add(transaction_callback)
        self.session.commit()
        self.session.refresh(transaction_callback)

    def _handle_qr_credited_callback(self, webhook_body:dict):
        statement = (
            select(Transaction)
                .where(Transaction.gateway_payment_id == webhook_body["payload"]["payment"]["entity"]["id"])
        )
        transaction = self.session.exec(statement).first()
        if not transaction:
            notes = {
                    'source_id': webhook_body["payload"]["qr_code"]["entity"]["id"] if not "source_id" in webhook_body["payload"]["qr_code"]["entity"]["notes"] else webhook_body["payload"]["qr_code"]["entity"]["notes"]["source_id"],
                    'store_id': webhook_body["payload"]["qr_code"]["entity"]["notes"]["store_id"],
                    'store_type': webhook_body["payload"]["qr_code"]["entity"]["notes"]["store_type"],
                    'driver' : '1' if not "driver" in webhook_body["payload"]["qr_code"]["entity"]["notes"] else webhook_body["payload"]["qr_code"]["entity"]["notes"]["driver"],
                    'client_id': None if not "client_id" in webhook_body["payload"]["qr_code"]["entity"]["notes"] else webhook_body["payload"]["qr_code"]["entity"]["notes"]["client_id"],
                    'client_version':'1.0' if not "client_version" in webhook_body["payload"]["qr_code"]["entity"]["notes"] else webhook_body["payload"]["qr_code"]["entity"]["notes"]["client_version"],
                    'payment_type': 'store_order_payment' if not "payment_type" in webhook_body["payload"]["qr_code"]["entity"]["notes"] else webhook_body["payload"]["qr_code"]["entity"]["notes"]["payment_type"],
                }
            transaction = Transaction(
                total_amount=webhook_body["payload"]["payment"]["entity"]["amount"] / 100,
                amount=webhook_body["payload"]["payment"]["entity"]["amount"] / 100,
                gateway_payment_id=webhook_body["payload"]["payment"]["entity"]["id"],
                gateway_order_id=webhook_body["payload"]["qr_code"]["entity"]["id"],
                source_id = notes["source_id"],
                store_id=notes["store_id"],
                driver=notes["driver"],
                client_id=notes["client_id"],
                store_type=notes["store_type"],
                client_version=notes["client_version"],
                payment_type=notes["payment_type"],
                api_version='1',
                status=STATUS_SUCCESS,
                callback_response=webhook_body,
                api_status=HTTPStatus.OK.value
            )
            self.session.add(transaction)
            self.session.commit()
            self.session.refresh(transaction)
        statement = (
            select(QRCode)
            .where(QRCode.qr_id == webhook_body["payload"]["qr_code"]["entity"]["id"])
        )
        qr_code = self.session.exec(statement).first()
        if not qr_code:
            qr_code = QRCode(
                qr_id=webhook_body["payload"]["qr_code"]["entity"]["id"],
                usage=webhook_body["payload"]["qr_code"]["entity"]["usage"],
                type=webhook_body["payload"]["qr_code"]["entity"]["type"],
                payment_amount=webhook_body["payload"]["payment"]["entity"]["amount"]/100,
                is_fixed_amount=webhook_body["payload"]["qr_code"]["entity"]["fixed_amount"],
                notes=webhook_body["payload"]["qr_code"]["entity"]["notes"],
                image_url=webhook_body["payload"]["qr_code"]["entity"]["image_url"],
                close_by=None if not webhook_body["payload"]["qr_code"]["entity"]["close_by"] else datetime.datetime.utcfromtimestamp(webhook_body["payload"]["qr_code"]["entity"]["close_by"]),
                closed_at= None if not webhook_body["payload"]["qr_code"]["entity"]["closed_at"] else datetime.datetime.utcfromtimestamp(webhook_body["payload"]["qr_code"]["entity"]["closed_at"]),
                close_reason=webhook_body["payload"]["qr_code"]["entity"]["close_reason"],
                status=webhook_body["payload"]["qr_code"]["entity"]["status"],
            )
            self.session.add(qr_code)
            self.session.commit()
            self.session.refresh(qr_code)
        transaction_callback = TransactionCallbacks(
            transaction_id=transaction.id,
            callback=webhook_body,
            event=webhook_body["event"],
            type="qr_code"
        )
        self.session.add(transaction_callback)
        self.session.commit()
        self.session.refresh(transaction_callback)

    def _handle_qr_closed_callback(self, webhook_body:dict):
        statement = (
            select(QRCode)
                .where(QRCode.qr_id == webhook_body["payload"]["qr_code"]["entity"]["id"])
        )
        qr_code = self.session.exec(statement).first()
        if qr_code:
            qr_code.status = webhook_body["payload"]["qr_code"]["entity"]["status"]
            self.session.add(qr_code)
            self.session.commit()
        
        transaction_callback = TransactionCallbacks(
            callback=webhook_body,
            event=webhook_body["event"],
            type="qr_code"
        )
        self.session.add(transaction_callback)
        self.session.commit()
        self.session.refresh(transaction_callback)
    
    def _update_payment_transaction(
        self,
        gateway_order_id: str,
        gateway_payment_id: str,
        data: dict,
        force_update:bool = False
    ) -> Transaction:
        logger.debug(f"Updating payment transaction: {gateway_order_id}")
        statement = (
            select(Transaction)
            .where(Transaction.gateway_order_id == gateway_order_id)
            .where(col(Transaction.gateway_order_id) is not None)
        )
        results = self.session.exec(statement)
        transaction = results.first()
        if not transaction:
            logger.error(f"no transaction for gateway order id {gateway_order_id}")
            raise NotFoundException(
                message=f"no transaction for gateway order id {gateway_order_id}"
            )

        if not force_update:
            if transaction.status == STATUS_SUCCESS:
                return transaction

        transaction.callback_response = data
        transaction.gateway_payment_id = gateway_payment_id
        logger.info(data)
        match data["captured"]:
            case False:
                transaction.status = STATUS_FAILED
            case True:
                transaction.status = STATUS_SUCCESS

        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def _update_refund_transaction(
        self, refund_transaction: RefundTransaction, data: dict, force_update: bool = False
    ) -> RefundTransaction:
        logger.debug(f"try update ================> {data}")
        if not force_update:
            logger.debug(f"refund status: {refund_transaction.status}")
            if refund_transaction.status == STATUS_SUCCESS:
                return refund_transaction

        refund_transaction.refund_id = data["id"]
        refund_transaction.api_response = data
        refund_transaction.callback_response = data
        match data["status"]:
            case "failed":
                refund_transaction.status = STATUS_FAILED
            case "processed":
                refund_transaction.status = STATUS_SUCCESS

        refund_transaction.amount = data["amount"] / 100
        self.session.add(refund_transaction)
        self.session.commit()
        self.session.refresh(refund_transaction)
        return refund_transaction
    
    def _create_refund(self, transaction, param):
        refund_transaction = RefundTransaction(
            refund_id=param["id"], transaction_id=transaction.id, response=param
        )
        self.session.add(refund_transaction)
        self.session.commit()
        self.session.refresh(refund_transaction)
        return refund_transaction