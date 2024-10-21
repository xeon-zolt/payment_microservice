from http import HTTPStatus
import ulid
from fastapi import BackgroundTasks, Request
from payment_app.lib.errors.error_handler import ForbiddenException, InternalServerException, NotFoundException
from payment_app.models.transaction_callbacks import TransactionCallbacks
from paytmpg import MerchantProperty, LibraryConstants, Payment, PaymentStatusDetailBuilder
from sqlmodel import Session, select
from fastapi.responses import JSONResponse

from payment_app.drivers.base_driver import BaseDriver
from payment_app.handlers.client_callback_handler import client_callback_transaction_handler
from payment_app.models.transaction import (
    STATUS_PENDING, Transaction, STATUS_FAILED, STATUS_SUCCESS,
)
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.schemas.requests.v1.make_payment_in import MakePaymentInPaytm
from loguru import logger
import json
import requests
import paytmchecksum

from payment_app.schemas.requests.v1.refund_payment_in import RefundPaymentIn


class PaytmDriver(BaseDriver):

    def __init__(
            self,
            session: Session,
            background_tasks: BackgroundTasks,
            client_id,
            mid,
            key,
            website,
            callback_url
    ):
        super().__init__()
        self.client_id = client_id
        self.session = session
        self.background_tasks = background_tasks
        self.environment = LibraryConstants.PRODUCTION_ENVIRONMENT
        self.mid = mid
        self.key = key
        self.website = website
        self.callback_url = callback_url
        # MerchantProperty.set_callback_url(callback_url)

    def make_payment(self,
                     transaction: Transaction,
                     make_payment_in: MakePaymentInPaytm,
                     client,
                     client_version
                     ) -> Transaction:
        additional_info = make_payment_in.additional_info
        additional_info["payment_type"] = make_payment_in.payment_type
        additional_info["client"] = client.name
        additional_info["store_id"] = make_payment_in.store_id
        paytm_params = dict()
        paytm_params["body"] = {
            "requestType": make_payment_in.payment_type,
            "mid": self.mid,
            "websiteName": self.website,
            "orderId": make_payment_in.source_id,
            "callbackUrl": f"{self.callback_url}/payment",#{make_payment_in.source_id}",
            "txnAmount": {
                "value": str(make_payment_in.amount_to_pay),
                "currency": "INR",
            },
            "userInfo": {
                "custId": make_payment_in.customer_id,
            },
            "extendInfo": make_payment_in.additional_info
        }
        try:
            checksum = paytmchecksum.generateSignature(json.dumps(paytm_params["body"]), self.key)

            paytm_params["head"] = {
                "signature": checksum
            }
            transaction.api_request = paytm_params
            post_data = json.dumps(paytm_params)

            url = f"https://securegw.paytm.in/theia/api/v1/initiateTransaction?mid={self.mid}&orderId={make_payment_in.source_id}"
            response = requests.post(url, data=post_data, headers={"Content-type": "application/json"}).json()
            logger.info(response)
        except Exception as ex:
            transaction.api_status = HTTPStatus.INTERNAL_SERVER_ERROR.value
            transaction.status = STATUS_FAILED
            transaction.api_response = str(ex)
            self.session.add(transaction)
            self.session.commit()
            raise ForbiddenException(message=f"{str(ex)}")
        
        if response["body"]["resultInfo"]["resultStatus"] == "F":
            transaction.api_status = HTTPStatus.FORBIDDEN.value
            transaction.status = STATUS_FAILED

        if response["body"]["resultInfo"]["resultStatus"] == 'S':
            transaction.api_status = HTTPStatus.OK.value
            transaction.gateway_order_id = response["body"]["txnToken"]

        transaction.api_response = response
        transaction.gateway_order_id = response["body"]["txnToken"]
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction


    def refund_payment(self,
                       transaction: Transaction,
                       refund_transaction: RefundTransaction,
                       refund_payment_in: RefundPaymentIn,
                       client,
                       ) -> RefundTransaction:
        refund_transaction_id = ulid.ulid()
        paytm_params = dict()
        logger.info(transaction.api_response)

        paytm_params["body"] = {}
        paytm_params["body"]["mid"] = self.mid
        paytm_params["body"]["txnType"] = "REFUND"
        paytm_params["body"]["orderId"] = transaction.source_id
        paytm_params["body"]["txnId"] = transaction.callback_response['TXNID']
        paytm_params["body"]["refId"] = refund_transaction_id
        paytm_params["body"]["refundAmount"] = float(refund_payment_in.amount_to_refund)
        #paytm_params["body"]["callbackUrl"] = f"{self.callback_url}refund",

        refund_transaction.id = refund_transaction_id
        refund_transaction.api_request = paytm_params
        refund_transaction.additional_info = refund_payment_in.notes
        self.session.add(refund_transaction)
        self.session.commit()
        self.session.refresh(refund_transaction)
        try:
            checksum = paytmchecksum.generateSignature(json.dumps(paytm_params["body"]), self.key)
            paytm_params["head"] = {
                "signature": checksum
            }
            logger.info(paytm_params["head"])
            post_data = json.dumps(paytm_params)
            logger.info(post_data)
            url = "https://securegw.paytm.in/refund/apply"
            response = requests.post(url, data=post_data, headers={"Content-type": "application/json"}).json()
            logger.debug(f"refund response  **** {response}")
        except Exception as ex:
            logger.critical(f"{str(ex)}")
            refund_transaction.status = STATUS_FAILED
            refund_transaction.api_status = HTTPStatus.INTERNAL_SERVER_ERROR.value
            refund_transaction.api_response = str(ex)
            self.session.add(refund_transaction)
            self.session.commit()
            raise ForbiddenException(message=f"{str(ex)}")

        if response["body"]["resultInfo"]["resultStatus"] == "TXN_FAILURE":
            refund_transaction.api_status = HTTPStatus.FORBIDDEN.value
            refund_transaction.status = STATUS_FAILED

        if response["body"]["resultInfo"]["resultStatus"] == 'PENDING':
            refund_transaction.api_status = HTTPStatus.OK.value
            refund_transaction.refund_id = response["body"]["refundId"]
            
        refund_transaction.api_response = response
        self.session.add(refund_transaction)
        self.session.commit()
        self.session.refresh(refund_transaction)
        return refund_transaction


    def set_payment_status(self, request: Request):
        pass

    def get_payment_status(self, transaction: Transaction):
        order_id = transaction.source_id
        read_timeout = 25000  # 25 seconds

        payment_status_builder = PaymentStatusDetailBuilder(order_id).set_read_timeout(read_timeout)
        payment_status_detail = payment_status_builder.build()

        response = Payment.getPaymentStatus(payment_status_detail)
        # todo

    def process_callback(self, request: dict, callback_type: str):
        if callback_type == "payment":
            webhook_body = request["request_body"]
            webhook_signature = webhook_body.pop('CHECKSUMHASH')
            checksum_valid = self.verify_signature(webhook_body, webhook_signature)
            if not checksum_valid:
                return JSONResponse(
                    content={
                        "success": True,
                    }
                )

            transaction = self.get_transaction_by_order_id(webhook_body["ORDERID"])
            if not transaction:
                logger.info("Transaction not found!")
                return JSONResponse(
                    content={
                        "success": True,
                    }
                )
            
            transaction_callback = TransactionCallbacks(
                transaction_id=transaction.id,
                callback=request["request_body"],
                type=callback_type,
                event="payment.paid"
            )
            self.session.add(transaction_callback)
            self.session.commit()
            self.session.refresh(transaction_callback)

            if webhook_body["STATUS"] == "TXN_SUCCESS":
                transaction.status = STATUS_SUCCESS
                transaction.callback_response = webhook_body
                transaction.gateway_payment_id = webhook_body['TXNID']
                self.session.add(transaction)
                self.session.commit()
                self.session.refresh(transaction)
                self.background_tasks.add_task(
                    client_callback_transaction_handler,
                    self.session,
                    {
                        "event": "transaction",
                        "transaction": transaction,
                        "driver": "paytm",
                    },
                )
            else:
                logger.error("Payment failed")
                transaction.status = STATUS_FAILED
                transaction.callback_response = webhook_body
                transaction.gateway_payment_id = webhook_body['TXNID']
                self.session.add(transaction)
                self.session.commit()
                self.session.refresh(transaction)
                self.background_tasks.add_task(
                    client_callback_transaction_handler,
                    self.session,
                    {
                        "event": "transaction",
                        "transaction": transaction,
                        "driver": "paytm",
                    },
                )

        elif callback_type == "refund":
            webhook_body = request["request_body"]['body']
            webhook_signature = json.loads(request["raw_request"].decode())["head"]["signature"]
            # we do not remove all white spaces because it will affect date strings too changing checksums
            webhook_body = json.dumps(webhook_body, separators=(",", ":"))
            checksum_valid = self.verify_signature(webhook_body, webhook_signature)
            if not checksum_valid:
                return JSONResponse(
                    content={
                        "success": True,
                    }
                )

            webhook_body = json.loads(webhook_body)
            transaction = self.get_transaction_by_txn_id(webhook_body["txnId"])
            if not transaction:
                logger.info("Transaction not found!")
                return JSONResponse(
                    content={
                        "success": True,
                    }
                )
            
            transaction_callback = TransactionCallbacks(
                transaction_id=transaction.id,
                callback=request["request_body"],
                type=callback_type,
                event="payment.refunded"
            )
            self.session.add(transaction_callback)
            self.session.commit()
            self.session.refresh(transaction_callback)

            if 'status' in webhook_body.keys():
                logger.error(f"Refund failed: refund status is {webhook_body['status']}")
                raise InternalServerException(message=f"Refund failed: refund status is {webhook_body['status']}")

            if 'status' not in webhook_body.keys():
                refund_transaction = self.get_refund_transaction_by_refund_id(webhook_body["refundId"])
                if not refund_transaction:
                    raise NotFoundException(message=f"refund transaction not found")
                
                transaction = refund_transaction.transaction
                refund_transaction.status = STATUS_SUCCESS
                refund_transaction.api_response = webhook_body
                refund_transaction.callback_response = webhook_body
                self.session.add(refund_transaction)
                self.session.commit()
                self.session.refresh(refund_transaction)
                self.background_tasks.add_task(
                    client_callback_transaction_handler,
                    self.session,
                    {
                        "event": "refund",
                        "transaction": transaction,
                        "driver": "paytm",
                    },
                )

        return JSONResponse(
            content={
                "success": True,
            }
        )


    def verify_signature(self, webhook_body: dict, webhook_signature) -> bool:
        checksum_valid = paytmchecksum.verifySignature(webhook_body, self.key, webhook_signature)
        if checksum_valid:
            logger.info("Checksum is valid")
            return True
        logger.info("Checksum is invalid")
        return False

    def get_transaction_by_txn_id(self, param):
        statement = select(Transaction).where(Transaction.gateway_payment_id == param)
        transaction = self.session.exec(statement).first()
        return transaction

    def get_transaction_by_order_id(self, order_id: str):
        statement = select(Transaction).where(Transaction.source_id == order_id)
        transaction = self.session.exec(statement).first()
        return transaction

    #TODO: Refund
    def get_refund_transaction_by_source_id(self, param):
        statement = select(RefundTransaction).where(RefundTransaction.refund_id == param)
        refund_transaction = self.session.exec(statement).first()
        return refund_transaction

    def get_refund_transaction_by_refund_id(self, param):
        statement = select(RefundTransaction).where(RefundTransaction.refund_id == param)
        refund_transaction = self.session.exec(statement).first()
        return refund_transaction

    def _create_refund(self, transaction, param):
        refund_transaction = RefundTransaction(
            refund_id=param["id"], transaction_id=transaction.id, response=param
        )
        self.session.add(refund_transaction)
        self.session.commit()
        self.session.refresh(refund_transaction)
        return refund_transaction
