"""Module for payment drivers"""
from abc import ABC
from http import HTTPStatus
import json
import datetime
from typing import Union
import requests
import razorpay
import ulid
import io
from fastapi import BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger
from razorpay.errors import (
    BadRequestError, GatewayError, ServerError, SignatureVerificationError
)
from sqlmodel import Session, select, col
from fastapi import UploadFile
from typing import List
from requests.auth import HTTPBasicAuth

from payment_app.drivers.base_driver import BaseDriver
from payment_app.drivers.helpers.callback_event_handler import CallbackEventHandler
from payment_app.drivers.helpers.razorpay_helper import RazorpayHelper
from payment_app.handlers.client_callback_handler import (
    client_callback_transaction_handler,
)
from payment_app.models import TransactionCallbacks
from payment_app.models.dispute import DisputeEvidence
from payment_app.models.dispute import Dispute
from payment_app.models.payment_links import PaymentLink
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.models.transaction import (
    CONVERT_IN_PAISE,
    IN_COUNTRY_CODE,
    IN_CURRENCY_SHORT_CODE,
    PAYMENT_TYPE,
    STATUS_CANCEL,
    STATUS_PENDING,
    Transaction,
    STATUS_FAILED,
    STATUS_SUCCESS,
)

from payment_app.schemas.requests.v1.qr_code_in import QRCodeIn
from payment_app.models import (
    Client, QRCode
)
from payment_app.schemas.requests.v1.create_payment_link_in import (
    CreatePaymentLinkIn, NotifyMedium, PaymentLinkStatus
)
from payment_app.schemas.requests.v1.make_payment_in import MakePaymentInRazorpay
from payment_app.schemas.requests.v1.refund_payment_in import RefundPaymentIn
from payment_app.lib.errors import (
    ForbiddenException,InternalServerException,NotFoundException,UnprocessableEntity
)
from payment_app.utils import upload_file_to_s3


class RazorpayDriver(BaseDriver, ABC):
    def __init__(
        self,
        session: Session,
        background_tasks: BackgroundTasks,
        key_id,
        key_secret,
        webhook_secret,
    ):
        super().__init__()
        self.session = session
        self.background_tasks = background_tasks
        self.webhook_secret = webhook_secret
        self.key_id = key_id
        self.key_secret = key_secret
        self.client = razorpay.Client(auth=(key_id, key_secret))
        self.callback_event_handler = CallbackEventHandler(session)

    def make_payment(
        self,
        transaction: Transaction,
        make_payment_in: MakePaymentInRazorpay,
        client,
        client_version,
    ) -> Transaction:
        razorpay_helper = RazorpayHelper()
        if make_payment_in.payment_type == 'link':
            store_type = 'bd_store_id'
        else:
            store_type = 'pos_store_id'
        razorpay_helper.add_notes(make_payment_in.additional_info).set_notes(
            "payment_type", make_payment_in.payment_type
        ).set_notes("client", client.name).set_notes(
            "store_id", make_payment_in.store_id
        ).set_notes(
            "transaction_id", transaction.id
        ).set_notes(
            "store_type", store_type
        )
        razorpay_helper.set_data(
            "amount", int(float(make_payment_in.amount_to_pay) * 100)
        ).set_data("currency", "INR").set_data(
            "receipt", make_payment_in.source_id
        ).set_data(
            "notes", razorpay_helper.get_notes()
        ).set_data(
            "payment_capture", True
        )

        transaction.api_request = razorpay_helper.get_data()
        # modify notes to include transaction_id, store_id, client, payment_type for future use
        transaction.additional_info = razorpay_helper.get_notes()
        self.session.add(transaction)
        self.session.commit()

        try:
            payment = self.client.order.create(data=razorpay_helper.get_data())
        except (BadRequestError, GatewayError, ServerError) as ex:
            logger.error(f"Error while making payment: {ex}")
            if isinstance(ex, GatewayError) or isinstance(ex, BadRequestError):
                transaction.api_status = HTTPStatus.BAD_GATEWAY.value
            elif isinstance(ex, ServerError):
                transaction.api_status = HTTPStatus.INTERNAL_SERVER_ERROR.value
            transaction.status = STATUS_FAILED
            transaction.api_response = str(ex)
            self.session.add(transaction)
            self.session.commit()
            raise ForbiddenException(message=f"{str(ex)}")
        except Exception as ex:
            logger.error(f"Error while making payment: {ex}")
            transaction.api_status = 500
            self.session.add(transaction)
            self.session.commit()
            raise ForbiddenException(message=f"{str(ex)}")

        transaction.gateway_order_id = payment["id"]
        transaction.api_response = payment
        transaction.api_status = HTTPStatus.OK.value

        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return transaction

    def refund_payment(
        self,
        transaction: Transaction,
        refund_transaction: RefundTransaction,
        refund_payment_in: RefundPaymentIn,
        client,
    ) -> RefundTransaction:

        refund_transaction_id = ulid.ulid()
        razorpay_helper = RazorpayHelper()
        razorpay_helper.add_notes(refund_payment_in.notes)
        razorpay_helper.set_notes("transaction_id", transaction.id)
        razorpay_helper.set_notes("refund_transaction_id", refund_transaction_id)
        if not refund_payment_in.receipt:
            receipt = transaction.source_id
        else:
            receipt = refund_payment_in.receipt
        razorpay_helper.set_data("receipt", receipt)
        razorpay_helper.set_data("notes", razorpay_helper.get_notes())

        if transaction.gateway_payment_id:
            payment_id = transaction.gateway_payment_id
        else:
            payment_id = transaction.api_response["id"]

        if not str(payment_id).startswith('pay_'):
            raise UnprocessableEntity(message="invalid payment id!")

        request_data = {
            "payment_id": payment_id,
            "amount":int(float(refund_payment_in.amount_to_refund) * 100),
            "notes":razorpay_helper.get_notes(),
            "receipt":receipt
        }
        refund_transaction.additional_info = razorpay_helper.get_notes()
        refund_transaction.id = refund_transaction_id
        refund_transaction.api_request = request_data

        self.session.add(refund_transaction)
        self.session.commit()
        self.session.refresh(refund_transaction)

        try:
            refund = self.client.payment.refund(
                payment_id,{
                "amount":int(float(refund_payment_in.amount_to_refund) * 100),
                "notes":razorpay_helper.get_notes(),
                "receipt":receipt
            })
            logger.info(refund)
            refund_transaction.refund_id = refund["id"]
            refund_transaction.api_response = refund
            refund_transaction.amount = refund["amount"] / 100
            refund_transaction.api_status = HTTPStatus.OK.value
            self.session.add(refund_transaction)
            self.session.commit()
            self.session.refresh(refund_transaction)

            return refund_transaction
        # in case like payment is already refunded
        except (BadRequestError, GatewayError, ServerError) as ex:
            logger.error(f"Error while refunding payment: {ex}")
            if isinstance(ex, GatewayError) or isinstance(ex, BadRequestError):
                refund_transaction.api_status = HTTPStatus.BAD_GATEWAY.value
            elif isinstance(ex, ServerError):
                refund_transaction.api_status = HTTPStatus.INTERNAL_SERVER_ERROR.value
            refund_transaction.status = STATUS_FAILED
            refund_transaction.api_response = str(ex)
            self.session.add(refund_transaction)
            self.session.commit()
            raise ForbiddenException(message=f"{str(ex)}")
        except Exception as ex:
            logger.error(f"Error while refunding payment: {ex}")
            refund_transaction.api_status = HTTPStatus.INTERNAL_SERVER_ERROR.value
            self.session.add(refund_transaction)
            self.session.commit()
            raise ForbiddenException(message=f"Error while refunding payment:{str(ex)}")

    def set_payment_status(self, request: Request):
        raise NotImplementedError

    def retry_refund(self, refund_transaction: RefundTransaction):
        try:
            logger.info("xeon")
            resp = self.client.payment.refund(
                refund_transaction.api_request["payment_id"],
                amount=refund_transaction.api_request["amount"],
                data=refund_transaction.api_request["data"],
            )
            logger.info(resp)
            refund_transaction.api_response = resp
            refund_transaction.refund_id = resp["id"]
            refund_transaction.amount = resp["amount"] / 100
            self.session.add(refund_transaction)
            self.session.commit()
            self.session.refresh(refund_transaction)
            return refund_transaction

        except Exception as ex:
            logger.error(f"Error while trying to redo refund: {ex}")
            #raise HTTPException(
            #    status_code=403,
            #    detail=str(ex),
            #)



    def get_payment_status(self, transaction, send_callback):
        order_id = transaction.gateway_order_id
        try:
            if order_id is None:
                raise ForbiddenException(message="gateway order id not provided")
            resp = self.client.order.payments(order_id)
            logger.debug(f"Payment status: {resp}")
            resp["items"].reverse()
            if not resp["items"] and send_callback is not True:
                return transaction
            for item in resp["items"]:
                if item["status"] not in ("created", "authorized"):
                    transaction = self._update_payment_transaction(
                        item["order_id"], item["id"], item, force_update=True
                    )
                    if send_callback:
                        client_callback_transaction_handler(
                            self.session,
                            {
                                "event": "transaction",
                                "transaction": transaction,
                                "driver": "razorpay",
                            },
                        )
                        if item["status"] == "captured":
                            break
                    return transaction

        except Exception as ex:
            logger.error(f"Error while getting payment status: {ex}")
            if not send_callback:
                raise HTTPException(
                    status_code=403,
                    detail=str(ex),
                )


    def process_callback(self, request: dict, callback_type: str):
        webhook_body = request["request_body"]
        webhook_signature = request["request_headers"]["x-razorpay-signature"]
        raw_request = request["raw_request"]
        logger.info(webhook_body)
        gateway_order_id = None
        try:
            if 'payment' in webhook_body["contains"]:
                gateway_order_id = webhook_body["payload"]["payment"]["entity"]["order_id"]
            elif 'payment_link' in webhook_body["contains"]:
                gateway_order_id = webhook_body["payload"]["payment_link"]["entity"]["order_id"]
            if not gateway_order_id:
                logger.critical("gateway order id not found!")
                raise UnprocessableEntity(message="gateway order id not found!")

            statement = (
                select(Transaction)
                .where(Transaction.gateway_order_id == gateway_order_id)
                .where(col(Transaction.gateway_order_id) is not None)
            )
            transaction = self.session.exec(statement).first()

            if not transaction:
                return JSONResponse(content={ "success": True })
            else:
                transaction_callback = TransactionCallbacks(
                    transaction_id=transaction.id,
                    callback=json.dumps(raw_request),
                )
                self.session.add(transaction_callback)
                self.session.commit()
                self.session.refresh(transaction_callback)

            if not self._verify_webhook_signature(raw_request, webhook_signature, request):
                return JSONResponse(content={ "success": True })

            if not callback_type:
                transaction_callback.event = webhook_body["event"]
                self.session.add(transaction_callback)
                self.session.commit()
                self.session.refresh(transaction_callback)
                match webhook_body["event"]:
                    case "payment.captured" | "payment.failed" | "payment.authorized" | "payment_link.paid":
                        transaction = self.callback_event_handler.handle_payment_callback(
                            transaction_callback=transaction_callback, 
                            webhook_body=webhook_body
                        )
                        self.background_tasks.add_task(
                            client_callback_transaction_handler,
                            self.session,
                            {
                                "event": "transaction",
                                "transaction": transaction,
                                "driver": "razorpay",
                            },
                        )

                    case "refund.created" | "refund.processed" | "refund.failed":
                        transaction = self.callback_event_handler.handle_refund_callback(
                            transaction_callback=transaction_callback, 
                            webhook_body=webhook_body
                        )
                        self.background_tasks.add_task(
                            client_callback_transaction_handler,
                            self.session,
                            {
                                "event": "refund",  # it was event in callback though
                                "transaction": transaction,
                                "driver": "razorpay",
                            },
                        )
                    case "payment_link.cancelled":
                        transaction_callback.type = "payment"
                        transaction_callback.callback = webhook_body
                        self.session.add(transaction_callback)
                        self.session.commit()
                        self.session.refresh(transaction_callback)
                    case _:
                        logger.error(f"unknown callback event received {webhook_body}")
                        transaction_callback.type = "unknown"
                        transaction_callback.callback = webhook_body
                        self.session.add(transaction_callback)
                        self.session.commit()
                        self.session.refresh(transaction_callback)
        except UnprocessableEntity:
            if not self._verify_webhook_signature(raw_request, webhook_signature, request):
                return JSONResponse(content={ "success": True })
            self.callback_event_handler.handle_qr_code_callback(webhook_body)
        return JSONResponse(content={"success": True})
    
    def _verify_webhook_signature(self, raw_request, webhook_signature, request):
        try:
            self.client.utility.verify_webhook_signature(
                raw_request,
                webhook_signature,
                self.webhook_secret,
            )
            return True
        except SignatureVerificationError as exception:
            logger.info(f"SignatureVerificationError: {repr(request)}.")
            logger.info(f"Webhook signature verification failed: {exception}.")
            return False
        
    def _update_payment_transaction(
        self,
        gateway_order_id,
        gateway_payment_id,
        data,
        force_update=False
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
        self, refund_transaction, data, force_update=False
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


    def get_refund_status(self, refund: RefundTransaction, send_callback: bool):
        refund_id = refund.refund_id
        try:
            if refund_id is None:
                raise ForbiddenException(message="refund id not provided")
            gateway_res = self.client.refund.fetch(refund_id)
            statement = (
                select(RefundTransaction)
                    .where(
                        RefundTransaction.transaction_id == gateway_res['notes']['transaction_id']
                    )
                    .where(RefundTransaction.refund_id == gateway_res['id'])
            )

            results = self.session.exec(statement)
            refund_transaction = results.first()
            updated_refund_transaction = self._update_refund_transaction(
                refund_transaction, gateway_res, True
            )
            return updated_refund_transaction

        except Exception as ex:
            logger.error(f"Error while getting refund status: {ex}")
            if not send_callback:
                raise InternalServerException(
                    message=f"Error while getting refund status:{str(ex)}"
                )


    #Payment link methods
    def create_payment_link(
        self, create_payment_link_in: CreatePaymentLinkIn, client, client_version
    ):
        try:
            notify_email_count = 0
            is_notify_email = False
            if create_payment_link_in.customer_email:
                notify_email_count = 1
                is_notify_email = True

            request_data = {
                "customer": {
                    "name": create_payment_link_in.customer_name,
                    "email": create_payment_link_in.customer_email or "",
                    "contact": IN_COUNTRY_CODE + create_payment_link_in.customer_phone,
                },
                "amount": float(create_payment_link_in.amount) * CONVERT_IN_PAISE,
                "currency": IN_CURRENCY_SHORT_CODE,
                "description": create_payment_link_in.description,
                "notify": {
                    "sms": True,
                    "email": is_notify_email
                }
            }
            gateway_res = self.client.payment_link.create(request_data)
            try:
                # to get order_id hack
                link = gateway_res["short_url"]
                requests.get(link, timeout = 10)
                # order_id hack end
                plink_info  = self.client.payment_link.fetch(gateway_res["id"])
                gateway_order_id = plink_info["order_id"]
                api_status = HTTPStatus.OK.value
            except Exception as e:
                logger.error(f'some ting failed due to {e}')
                raise NotFoundException(message="Order id not found")

            transaction = Transaction(
                total_amount=create_payment_link_in.amount,
                amount=create_payment_link_in.amount,
                source_id=create_payment_link_in.source_id,
                payment_type= PAYMENT_TYPE,
                driver=create_payment_link_in.driver_id,
                gateway_order_id = gateway_order_id,
                status = STATUS_PENDING,
                api_request=request_data,
                api_response=gateway_res,
                store_id=create_payment_link_in.store_id,
                client_id=client.id,
                additional_info=gateway_res['customer'],
                api_version=1,
                client_version=client_version,
                api_status=api_status
            )

            self.session.add(transaction)
            self.session.commit()
            self.session.refresh(transaction)
            transaction_response = transaction.json()

            payment_link_payload = PaymentLink(
                transaction_id=transaction.id,
                plink_id= gateway_res['id'],
                api_response= gateway_res,
                notify_email_count=notify_email_count,
                status = gateway_res['status']
            )
            self.session.add(payment_link_payload)
            self.session.commit()

            return json.loads(transaction_response)
        except NotFoundException as ex:
            raise NotFoundException(message=f"Error while create payment link: {ex.message}")
        except Exception as ex:
            raise InternalServerException(message=f"Error while create payment link: {ex}")

    def resend_payment_link(self, plink_id: str, medium: NotifyMedium, transaction_id: str):
        try:
            gateway_res = self.client.payment_link.notifyBy(plink_id, medium)
            if gateway_res['success']:
                statement = (
                    select(PaymentLink)
                    .where(PaymentLink.transaction_id == transaction_id)
                )
                results = self.session.exec(statement)
                payment_link: Union[PaymentLink, None] = results.first()

                if not payment_link:
                    raise NotFoundException(
                        message=f"Payment link not found for transaction {transaction_id}"
                    )

                payment_link.status = STATUS_PENDING
                payment_link.api_response = gateway_res
                payment_link.update_count += 1

                if medium == 'email':
                    payment_link.notify_email_count += 1

                if medium == 'sms':
                    payment_link.notify_sms_count += 1

                self.session.add(payment_link)
                self.session.commit()
                return gateway_res
            return {
                'success': False
            }
        except NotFoundException as ex:
            raise NotFoundException(message=f"Error while resend payment link: {ex.message}")
        except Exception as ex:
            raise InternalServerException(message=f"Error while resend payment link: {ex}")

    def cancel_payment_link(self, plink_id: str, transaction: Transaction):
        try:
            gateway_res = self.client.payment_link.cancel(plink_id)
            transaction.status = STATUS_CANCEL
            self.session.add(transaction)
            self.session.commit()
            self.session.refresh(transaction)

            statement = (
                select(PaymentLink)
                .where(PaymentLink.transaction_id == transaction.id)
            )
            results = self.session.exec(statement)
            payment_link: Union[PaymentLink, None] = results.first()

            if not payment_link:
                raise NotFoundException(
                    message=f"Payment link not found for transaction {transaction.id}"
                )

            payment_link.status = gateway_res['status']
            payment_link.api_response = gateway_res
            payment_link.update_count += 1
            self.session.add(payment_link)
            self.session.commit()
            return gateway_res
        except NotFoundException as ex:
            raise NotFoundException(message=f"Error while cancel payment link: {ex.message}")
        except Exception as ex:
            raise InternalServerException(message=f"Error while cancel payment link: {ex}")

    def modify_payment_link(self, plink_id: str, request: dict):
        response = self.client.invoice.edit(plink_id, request)
        return response


    def get_payment_link_status(self, plink_id: str, transaction: Transaction):
        try:
            gateway_res = self.client.payment_link.fetch(plink_id)
            transaction.status = self._payment_link_status_mapper(
                str(gateway_res["status"]).lower()
            )
            self.session.add(transaction)
            self.session.commit()
            self.session.refresh(transaction)

            statement = (
                select(PaymentLink)
                .where(PaymentLink.transaction_id == transaction.id)
            )
            results = self.session.exec(statement)
            payment_link: Union[PaymentLink, None] = results.first()

            if not payment_link:
                raise NotFoundException(
                    message=f"Payment link not found for transaction {transaction.id}"
                )

            payment_link.status = gateway_res["status"]
            payment_link.api_response = gateway_res
            payment_link.update_count += 1

            self.session.add(payment_link)
            self.session.commit()
            self.session.refresh(payment_link)
            return gateway_res
        except NotFoundException as ex:
            raise NotFoundException(message=f"Error while get payment link status: {ex.message}")
        except Exception as ex:
            raise InternalServerException(message=f"Error while get payment link status: {ex}")

    def _payment_link_status_mapper(self, gateway_status: str):
        if gateway_status == PaymentLinkStatus.created:
            return "pending"
        if gateway_status == PaymentLinkStatus.cancelled:
            return "cancelled"
        if gateway_status == PaymentLinkStatus.paid:
            return "success"
        return "failed"


    """
    Start QR Code
    """
    
    def create_qr_code(self, create_qr_code_in: QRCodeIn, qr_code: QRCode, client: Client, client_version: str | None):
        notes = create_qr_code_in.additional_info
        notes["store_id"] = create_qr_code_in.store_id
        notes["source_id"] = create_qr_code_in.source_id
        notes["store_type"] = create_qr_code_in.store_type
        notes["driver"] = qr_code.driver
        notes["qr_id"] = qr_code.id
        notes["client_id"] = client.id
        notes["client_version"] = client_version
        notes["payment_type"] = "store_order_payment"
        try:
            qr_request = {
                "type": qr_code.type,
                "usage": qr_code.usage,
                "fixed_amount": qr_code.is_fixed_amount,
                "notes": notes
            }
            if qr_code.is_fixed_amount:
                qr_request["payment_amount"] = float(qr_code.payment_amount) * CONVERT_IN_PAISE
                
            gateway_res = self.client.qrcode.create(qr_request)
            
            qr_code.api_request = qr_request
            qr_code.api_response = gateway_res
            qr_code.qr_id = gateway_res["id"]
            qr_code.notes = gateway_res["notes"]
            qr_code.image_url = gateway_res["image_url"]
            qr_code.close_by = None if not gateway_res["close_by"] else datetime.datetime.utcfromtimestamp(gateway_res["close_by"])
            qr_code.status = gateway_res["status"]
            
            self.session.add(qr_code)
            self.session.commit()
            self.session.refresh(qr_code)
            qr_code_res = qr_code.json()
            return json.loads(qr_code_res)
        
        except Exception as ex:
            qr_code.api_request = qr_request
            qr_code.status = STATUS_FAILED
            qr_code.api_response = str(ex)
            self.session.add(qr_code)
            self.session.commit()
            raise InternalServerException(message=f"Error while create QR Code: {ex}")

    def close_qr_code(self, qr_code_id: str):
        try:
            gateway_res = self.client.qrcode.close(qr_code_id)
            statement = (
                select(QRCode)
                .where(QRCode.qr_id == qr_code_id)
            )
            results = self.session.exec(statement)
            qr_detail: Union[QRCode, None] = results.first()

            if not qr_detail:
                raise NotFoundException(message="QR Code not found")

            qr_detail.status = gateway_res["status"]
            if gateway_res["close_by"]:
                qr_detail.close_by = datetime.datetime.utcfromtimestamp(gateway_res["close_by"])
            qr_detail.closed_at = datetime.datetime.utcfromtimestamp(gateway_res["closed_at"])
            qr_detail.close_reason = gateway_res["close_reason"]

            self.session.add(qr_detail)
            self.session.commit()
            self.session.refresh(qr_detail)
            return gateway_res
        except NotFoundException as ex:
            raise NotFoundException(message=f"Error while close QR Code: {ex.message}")
        except Exception as ex:
            raise InternalServerException(message=f"Error while close QR Code: {ex}")
    
    def upload_dispute_document(self, file: bytes, dispute_id: str):
        url = 'https://api.razorpay.com/v1/documents'
        file_Obj = io.BytesIO(file)
        response = requests.post(
            url, 
            files={'purpose': (None, 'dispute_evidence'), 'file': file_Obj},
            headers={},
            auth=(self.key_id, self.key_secret)
        )
        if not (response.status_code in (200,201)):
            raise ForbiddenException(message=f"{str(response.json()['error']['description'])}")
        dispute_document = response.json()
        
        """ upload file on s3 bucket """
        
        # upload_file_to_s3(file_Obj, f'disputes/{dispute_id}/{dispute_document["id"]}/{dispute_document["purpose"]}/{dispute_document["name"]}')
        
        return dispute_document
    
    def send_dispute_documents_draft(self, dispute_id: str, data: dict):
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.patch(
            f'https://api.razorpay.com/v1/disputes/{dispute_id}/contest', 
            headers=headers, 
            data=data, 
            auth=(self.key_id, self.key_secret)
        )
        if not (response.status_code in (200,201)):
            raise ForbiddenException(message=f"{str(response)}")
        return response

    def get_dispute_document(self, _id: str):
        url = f'https://api.razorpay.com/v1/documents/{_id}'
        response = requests.get(url, auth=(self.key_id, self.key_secret))
        if not (response.status_code in (200,201)):
            raise ForbiddenException(message=f"{str(response)}")
        return response.json()
        
    def accept_dispute_by_id(self, dispute: Dispute):
        try:
            gateway_res = requests.post(f'https://api.razorpay.com/v1/disputes/{dispute.dispute_id}/accept', auth=(self.key_id, self.key_secret))
            
            if not (gateway_res.status_code in (200,201)):
                res = gateway_res.json()
                raise ForbiddenException(message=f"{res['error']['description']}")
            
            accept_dispute_res = gateway_res.json()
            dispute.status = accept_dispute_res["status"]
            self.session.add(dispute)
            self.session.commit()
            self.session.refresh(dispute)
            return gateway_res
        except ForbiddenException as ex:
            raise ForbiddenException(message=f"Error while accept dispute: {ex.message}")
        except Exception as ex:
            raise InternalServerException(message=f"Error while accept dispute: {ex}")
    
    def contest_dispute_by_id(self, dispute: Dispute):
        try:
            payload = {
                "action": "submit"
            }
            gateway_res = requests.post(f'https://api.razorpay.com/v1/disputes/{dispute.dispute_id}/contest', data=payload, auth=(self.key_id, self.key_secret))
            
            if not (gateway_res.status_code in (200,201)):
                res = gateway_res.json()
                raise ForbiddenException(message=f"{res['error']['description']}")
            
            contest_dispute_res = gateway_res.json()
            dispute.status = contest_dispute_res["status"]
            self.session.add(dispute)
            self.session.commit()
            self.session.refresh(dispute)
            return gateway_res
        except ForbiddenException as ex:
            raise ForbiddenException(message=f"Error while accept dispute: {ex.message}")
        except Exception as ex:
            raise InternalServerException(message=f"Error while accept dispute: {ex}")

    def get_qr_code_status(self, qr_id: str):
        try:
            qr_details = self.client.qrcode.fetch(qr_id)
            return qr_details
        except Exception as ex:
            raise InternalServerException(message=f"Error while getting qr details: {ex}") 
    
    def payment_methods(self):
        try:
            gateway_res = requests.get(f'https://api.razorpay.com/v1/methods?key_id={self.key_id}')
            if not (gateway_res.status_code in (200,201)):
                res = gateway_res.json()
                raise ForbiddenException(message=f"{res['error']['description']}")
                raise ForbiddenException(message=f"{str(gateway_res)}")
            return gateway_res.json()
        except ForbiddenException as ex:
            raise ForbiddenException(message=f"Error while get payment methods: {ex.message}")  
        except Exception as ex:
            raise InternalServerException(message=f"Error while get payment methods: {ex}")
        
    def payment_downtime(self):
        try:
            gateway_res = requests.get(f'https://api.razorpay.com/v1/payments/downtimes', auth=(self.key_id, self.key_secret))
            if not (gateway_res.status_code in (200,201)):
                res = gateway_res.json()
                raise ForbiddenException(message=f"{res['error']['description']}")
            return gateway_res.json()
        except ForbiddenException as ex:
            raise ForbiddenException(message=f"Error while get payment downtime: {ex.message}")  
        except Exception as ex:
            raise InternalServerException(message=f"Error while get payment downtime: {ex}")
    
    def get_transaction_by_payment_id(self, payment_id:str):
        order = self.client.payment.fetch(payment_id)
        if not order:
            raise ForbiddenException(message=f"Can not fetch transaction for payment_id: {payment_id}")
        order_id = order["order_id"]
        statement = select(Transaction).where(Transaction.gateway_order_id == order_id)
        transaction = self.session.exec(statement).first()
        if not transaction:
            raise NotFoundException(message=f"Transaction does not exist for payment_id: {payment_id}")
        return transaction.json()
