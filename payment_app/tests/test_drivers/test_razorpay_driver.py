import json
import unittest
from unittest.mock import patch
from fastapi.responses import JSONResponse
from sqlmodel import select

from payment_app.drivers.base_driver import BaseDriver
from payment_app.drivers.razorpay_driver import RazorpayDriver
from payment_app.lib.errors.error_handler import InternalServerException, NotFoundException, UnprocessableEntity
from razorpay.errors import (BadRequestError, GatewayError, ServerError, SignatureVerificationError)
from payment_app.models import ClientGateway, Client, Transaction, AllowedIP
from payment_app.models.qr_codes import QRCode
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.models.payment_links import PaymentLink
from payment_app.models.transaction_callbacks import TransactionCallbacks
from payment_app.schemas.requests.v1.create_payment_link_in import CreatePaymentLinkIn, NotifyMedium
from payment_app.schemas.requests.v1.make_payment_in import MakePaymentInRazorpay
from payment_app.schemas.requests.v1.qr_code_in import QRCodeIn, QRType, QRUsage
from payment_app.schemas.requests.v1.refund_payment_in import RefundPaymentIn
from payment_app.tests.conftest import session, x_api_key
from payment_app.models.transaction import Transaction
from payment_app.utils import get_api_key_hash
from payment_app.lib.errors import ForbiddenException
from payment_app.schemas.requests.v1.make_payment_in import StoreType
from payment_app.models.transaction import (
    STATUS_SUCCESS,
)


"""
    Load Json of payment link
"""
with open("payment_app/tests/constant/payment_link_data.json", 'r') as file:
    payment_payload = json.load(file)

clientInstance = Client(
    name="test",
    callback_url='http://127.0.0.1',
    api_key= get_api_key_hash(x_api_key),
    active=1
)

session.add(clientInstance)
session.commit()
session.refresh(clientInstance)

clientGatewayInstance = ClientGateway(
            driver_id = 1,
            default = True,
            active = True,
            client_id = clientInstance.id
        )

session.add(clientGatewayInstance)
session.commit()
session.refresh(clientGatewayInstance)

transaction = Transaction(
    total_amount=10,
    amount=10,
    source_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["source_id"],
    payment_type= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["payment_type"],
    driver= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["driver"],
    gateway_order_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_order_id"],
    status= "pending",
    api_request= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_request"],
    api_response= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_response"],
    store_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["store_id"],
    client_id= clientInstance.id,
    store_type=None,
    additional_info= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["additional_info"],
    api_version= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_version"],
    client_version= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["client_version"],
    api_status= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_status"],
    callback_response= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["callback_response"],
    gateway_payment_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_payment_id"],
)

session.add(transaction)
session.commit()
session.refresh(transaction)

requestInstance = {
    "request_headers": {
        "x-razorpay-signature": "tabsvsspacess"
    },
    "request_body":{
        "contains": ['payment'],
        "payload":{
            "payment": {
                "entity": {
                    "order_id": transaction.gateway_order_id,
                }
            },
            "qr_code": {
                "entity": {
                    "notes":{
                        "store_id": '13',
                        "store_type": 'pos_store_id',
                        "source_id": "233",
                    }
                }
            }

        },
        "event": "payment.captured"
    },
    "raw_request": "valid"
}

allowedIPInstance  = AllowedIP(
    client_id=clientInstance.id, 
    ip_range='127.0.0.1',
    active=1
)

session.add(allowedIPInstance)
session.commit()
session.refresh(allowedIPInstance)

makePaymentInRazorpay = MakePaymentInRazorpay(
    driver_id= 1,
    total_amount = 10,
    amount_to_pay = 10,
    payment_type = "type",
    source_id = "source_id",
    store_id = "store_id",
    additional_info= {}
)

refund_transaction = RefundTransaction(
    transaction_id=transaction.id,
    refund_id=transaction.id,
    api_request={"data": {"receipt": "56fa4b62-4045-4aa7-998c-8b2b27f6c951"}, "amount": 10, "payment_id": "pay_JDIgZ4mIvaIKTw"},
    api_response={"id": "rfnd_JGOJVluOYJMgno", "notes": [], "amount": 10, "entity": "refund", "status": "processed", "receipt": "3622d849-7063-4f6f-920d-a1bcae0350cd", "batch_id": None, "currency": "INR", "created_at": 1649318113, "payment_id": "pay_JGOJ4oPfbkKSoi", "refund_type": "", "processed_at": None, "acquirer_data": {"arn": None}, "speed_processed": "normal", "speed_requested": "normal"},
    api_status=200,
    callback_response= {"id": "rfnd_KNiEDViGF5gtB3", "notes": {"transaction_id": "01GE4A4E7GNE05TSTV7359X5MK", "order_payment_id": 10501370, "refund_for_order_id": "1b848a4f-c22a-496d-b1f8-c7a4ab179bf7", "refund_transaction_id": "01GE4JR5BFRHD06G9AGWRTC22E"}, "amount": 10, "entity": "refund", "status": "processed", "receipt": "1b848a4f-c22a-496d-b1f8-c7a4ab179bf7", "batch_id": None, "currency": "INR", "created_at": 1664453712, "payment_id": "pay_KNffH8ubvcYxRg", "acquirer_data": {"arn": None}, "speed_processed": "normal", "speed_requested": "normal"},
    status="pending",
    amount=transaction.amount,
    additional_info={}
)

session.add(refund_transaction)
session.commit()
session.refresh(refund_transaction)

refund_payment_in = RefundPaymentIn(
    amount_to_refund=transaction.amount,
    payment_transaction_id= transaction.id,
    notes= {},
    receipt= "receipt"
)

create_payment_link_in = CreatePaymentLinkIn(
    driver_id = 1,
    amount = 10,
    description = 'description',
    customer_email = 'customer@abc.com',
    customer_phone= '12345676890',
    customer_name = 'customer',
    source_id = 'source_id',
    store_id = 'store_id'
)

class TestRazorpayDriver(unittest.TestCase):

    @classmethod
    @patch("fastapi.BackgroundTasks")
    def setUpClass(self, mock_bg_tasks): 
        self.razorpayDriver: BaseDriver = RazorpayDriver(
                session,
                mock_bg_tasks,
                "rzp_test_HIt23Jasd9C5TQ",
                "C3lS280oXKqPCz5aFRJlEtjr",
                "onekay",
            )

    @patch("razorpay.resources.order.Order", create=payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_response"])  
    def testMakePaymentForValidTransaction(self, orderMocker):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        assert transactionResp.total_amount == 10
        assert transactionResp.api_status == 200
        assert transactionResp.status == "pending"
    
    @patch("razorpay.resources.order.Order.create", side_effect=[BadRequestError, GatewayError, ServerError, SignatureVerificationError])  
    def testMakePaymentForValidTransactionWithException(self, orderMocker):
        #BadRequestError
        try:
            transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        except ForbiddenException:
            assert True
        #GatewayError
        try:
            transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        except ForbiddenException:
            assert True
        #ServerError
        try:
            transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        except ForbiddenException:
            assert True
        #SignatureVerificationError
        try:
            transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        except ForbiddenException:
            assert True

    @patch("razorpay.utility.utility.Utility.verify_webhook_signature", return_Value=True)
    def testProcessCallbackForValidTransaction(self, signMock):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        requestInstance["request_body"]["payload"]["payment"]["entity"]["order_id"] = transactionResp.gateway_order_id
        self.razorpayDriver.process_callback(request=requestInstance, callback_type="payment.captured")
        statement = (
            select(TransactionCallbacks)
            .where(TransactionCallbacks.transaction_id == transaction.id)
        )
        results = session.exec(statement)
        transactionCallback = results.first()
        assert transactionCallback != None

    @patch("razorpay.utility.utility.Utility.verify_webhook_signature", side_effect=[SignatureVerificationError])
    def testProcessCallbackForValidTransactionWithException(self, signMock):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        requestInstance["request_body"]["payload"]["payment"]["entity"]["order_id"] = transactionResp.gateway_order_id
        resp = self.razorpayDriver.process_callback(request=requestInstance, callback_type="payment.captured")
        assert isinstance(resp,JSONResponse)

    def testCreateAndResendAndCancelPaymentLink(self):
        transactionResp = self.razorpayDriver.create_payment_link(create_payment_link_in = create_payment_link_in, client=clientInstance, client_version=1.1)
        assert transactionResp['total_amount'] == 10
        assert transactionResp['api_status'] == 200
        assert transactionResp['status'] == "pending"

        statement = (
            select(PaymentLink)
            .where(PaymentLink.transaction_id == transactionResp["id"])
        )
        results = session.exec(statement)
        paymentLink = results.first()

        statement = (
            select(Transaction)
            .where(Transaction.id == transactionResp["id"])
        )
        results = session.exec(statement)
        transactionNew = results.first()

        linkStatus = self.razorpayDriver.get_payment_link_status(plink_id = paymentLink.plink_id, transaction=transactionNew)
        assert linkStatus["status"] == "created"

        response = self.razorpayDriver.resend_payment_link(plink_id = paymentLink.plink_id, medium=NotifyMedium.sms, transaction_id=transactionResp["id"])
        assert response["success"] == True

        try:
            response = self.razorpayDriver.resend_payment_link(plink_id = paymentLink.plink_id, medium=NotifyMedium.sms, transaction_id="invalid_id")
        except NotFoundException:
            assert True

        statement = (
            select(Transaction)
            .where(Transaction.id == transactionResp["id"])
        )
        results = session.exec(statement)
        transactionNew = results.first()
        
        response = self.razorpayDriver.cancel_payment_link(plink_id = paymentLink.plink_id, transaction=transactionNew)
        assert response["status"] == 'cancelled'

    @patch("razorpay.resources.payment_link.PaymentLink.create", side_effect=[NotFoundException, SignatureVerificationError])
    def testCreatePaymentLinkWithException(self, mockLink):
        try:
            transactionResp = self.razorpayDriver.create_payment_link(create_payment_link_in = create_payment_link_in, client=clientInstance, client_version=1.1)
        except NotFoundException:
            assert True
        try:
            transactionResp = self.razorpayDriver.create_payment_link(create_payment_link_in = create_payment_link_in, client=clientInstance, client_version=1.1)
        except Exception:
            assert True

    @patch("razorpay.resources.payment_link.PaymentLink.notifyBy", side_effect=[NotFoundException, SignatureVerificationError])
    def testResendPaymentLinkWithException(self, mockLink):
        transactionResp = self.razorpayDriver.create_payment_link(create_payment_link_in = create_payment_link_in, client=clientInstance, client_version=1.1)
        statement = (
            select(PaymentLink)
            .where(PaymentLink.transaction_id == transactionResp["id"])
        )
        results = session.exec(statement)
        paymentLink = results.first()
        try:
            response = self.razorpayDriver.resend_payment_link(plink_id = paymentLink.plink_id, medium=NotifyMedium.sms, transaction_id=transactionResp["id"])
        except NotFoundException:
            assert True
        try:
            response = self.razorpayDriver.resend_payment_link(plink_id = paymentLink.plink_id, medium=NotifyMedium.sms, transaction_id=transactionResp["id"])
        except Exception:
            assert True
    
    @patch("razorpay.resources.payment_link.PaymentLink.cancel", side_effect=[NotFoundException, SignatureVerificationError])
    def testCancelPaymentLinkWithException(self, mockLink):
        transactionResp = self.razorpayDriver.create_payment_link(create_payment_link_in = create_payment_link_in, client=clientInstance, client_version=1.1)
        statement = (
            select(PaymentLink)
            .where(PaymentLink.transaction_id == transactionResp["id"])
        )
        results = session.exec(statement)
        paymentLink = results.first()

        statement = (
            select(Transaction)
            .where(Transaction.id == transactionResp["id"])
        )
        results = session.exec(statement)
        transactionNew = results.first()
        try:
            response = self.razorpayDriver.cancel_payment_link(plink_id = paymentLink.plink_id, transaction=transactionNew)
        except NotFoundException:
            assert True
        try:
            response = self.razorpayDriver.cancel_payment_link(plink_id = paymentLink.plink_id, transaction=transactionNew)
        except Exception:
            assert True
    
    @patch("razorpay.resources.payment.Payment.refund", return_value={'id': refund_transaction.id, 'amount': 10})  
    def testRefundPaymentForValidTransaction(self, refundMocker):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        transactionResp.gateway_payment_id = payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_payment_id"]
        refundTransactionResp = self.razorpayDriver.refund_payment(transaction = transactionResp,refund_transaction=refund_transaction, refund_payment_in=refund_payment_in, client=clientInstance)
        assert refundTransactionResp.status == 'pending'
        assert refundTransactionResp.api_response["amount"] == 10

    @patch("razorpay.resources.payment.Payment.refund", side_effect=[BadRequestError, GatewayError, ServerError, SignatureVerificationError])  
    def testRefundPaymentForValidTransactionWithException(self, refundMocker):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        #BadRequestError
        try:
            transactionResp = self.razorpayDriver.refund_payment(transaction = transactionResp,refund_transaction=refund_transaction, refund_payment_in=refund_payment_in, client=clientInstance)
        except ForbiddenException:
            assert True
        #GatewayError
        try:
            transactionResp = self.razorpayDriver.refund_payment(transaction = transactionResp,refund_transaction=refund_transaction, refund_payment_in=refund_payment_in, client=clientInstance)
        except ForbiddenException:
            assert True
        #ServerError
        try:
            transactionResp = self.razorpayDriver.refund_payment(transaction = transactionResp,refund_transaction=refund_transaction, refund_payment_in=refund_payment_in, client=clientInstance)
        except ForbiddenException:
            assert True
        # SignatureVerificationError
        try:
            transactionResp = self.razorpayDriver.refund_payment(transaction = transactionResp,refund_transaction=refund_transaction, refund_payment_in=refund_payment_in, client=clientInstance)
        except ForbiddenException:
            assert True

    @patch("razorpay.resources.payment.Payment.refund", side_effect=BadRequestError)  
    def testRetryRefundPaymentForValidTransactionWithException(self, refundMocker):
        self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        refundTransactionResp = self.razorpayDriver.retry_refund(refund_transaction=refund_transaction)
        assert refundTransactionResp == None

    @patch("razorpay.resources.order.Order.payments")
    def testPaymentStatusForValidTransaction(self, paymentMocker):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        paymentMocker.return_value = {'entity': 'transactions', 'collection': 10, 'count': 1, 'items': [{"status": "captured", "order_id": transactionResp.gateway_order_id,'captured': True, "id": transactionResp.id}]}
        transactionResp = self.razorpayDriver.get_payment_status(transaction=transactionResp, send_callback = False)
        assert transactionResp.total_amount == 10
        assert transactionResp.api_status == 200
        assert transactionResp.status == "success"
        
    @patch("razorpay.resources.order.Order.payments", side_effect=BadRequestError)
    def testPaymentStatusForValidTransactionWithException(self, paymentMocker):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        try:
            transactionResp = self.razorpayDriver.get_payment_status(transaction=transactionResp, send_callback = False) 
        except Exception:
            assert True
    
    @patch("razorpay.resources.base.Resource.fetch")
    def testRefundStatusForValidTransaction(self, paymentMocker):
        statement = (
                select(RefundTransaction)
            )
        results = session.exec(statement)
        refund_transaction = results.first()
        paymentMocker.return_value = {"id":refund_transaction.refund_id, "status": 'processed', 'amount': 10, "notes": {"transaction_id": transaction.id}}
        refundTransactionResp = self.razorpayDriver.get_refund_status(refund=refund_transaction, send_callback = False) 
        refundTransactionResp.amount = 10
        refundTransactionResp.status = "processed"
    
    @patch("razorpay.resources.base.Resource.fetch", side_effect = BadRequestError)
    def testRefundStatusForValidTransactionWithException(self, paymentMocker):
        statement = (
                select(RefundTransaction)
            )
        results = session.exec(statement)
        refund_transaction = results.first()
        paymentMocker.return_value = {"id":refund_transaction.refund_id, "status": 'processed', 'amount': 10, "notes": {"transaction_id": transaction.id}}
        try:
            refundTransactionResp = self.razorpayDriver.get_refund_status(refund=refund_transaction, send_callback = False) 
        except Exception:
            assert True
    
    @patch("razorpay.resources.qrcode.Qrcode.create")
    def testCreateQRCode(self, qr_mocker):
        qr_code = QRCode(
            usage=QRUsage.single_use,
            type=QRType.upi_qr,
            payment_amount='20',
            is_fixed_amount=True,
            driver=1,
        )
        session.add(qr_code)
        session.commit()
        session.refresh(qr_code)
        qr_code_in = QRCodeIn(
            usage=QRUsage.single_use,
            type=QRType.upi_qr,
            payment_amount='20',
            is_fixed_amount=True,
            driver=1,
            store_id='13',
            source_id='pos',
            store_type=StoreType.POS_STORE_ID,
            additional_info={
                'store_id': '13',
                'source_id': 'pos',
                'store_type': StoreType.POS_STORE_ID,
            }
        )
        qr_mocker.return_value = {
            'id': 'qr_qwe23fwdfwr4',
            'notes': {},
            'image_url': 'image.url',
            'close_by': 1605871409,
            'status': 'created'
        }
        qr_detail = self.razorpayDriver.create_qr_code(qr_code=qr_code, create_qr_code_in=qr_code_in, client=clientInstance, client_version='1.2')

        assert qr_detail['payment_amount'] == 20
        assert qr_detail['status'] == 'created'
        assert qr_detail['type'] == QRType.upi_qr
    
    @patch("razorpay.resources.qrcode.Qrcode.create", side_effect = SignatureVerificationError)
    def testCreateQRCodeWithException(self, qr_mocker):
        qr_code = QRCode(
            usage=QRUsage.single_use,
            type=QRType.upi_qr,
            payment_amount='20',
            is_fixed_amount=True,
            driver=1,
        )
        session.add(qr_code)
        session.commit()
        session.refresh(qr_code)
        qr_code_in = QRCodeIn(
            usage=QRUsage.single_use,
            type=QRType.upi_qr,
            payment_amount='20',
            is_fixed_amount=True,
            driver=1,
            store_id='13',
            source_id='pos',
            store_type=StoreType.POS_STORE_ID
        )
        qr_mocker.return_value = {
            'id': 'qr_qwe23fwdfwr4',
            'notes': {},
            'image_url': 'image.url',
            'close_by': 1605871409,
            'status': 'created'
        }
        try:
            qr_detail = self.razorpayDriver.create_qr_code(qr_code=qr_code, create_qr_code_in=qr_code_in, client=clientInstance, client_version='1.2')
        except Exception:
            assert True
    
    @patch("razorpay.resources.qrcode.Qrcode.close")
    def testCloseQRCode(self, qr_mocker):
        qr_code = QRCode(
            usage=QRUsage.single_use,
            type=QRType.upi_qr,
            payment_amount='20',
            is_fixed_amount=True,
            driver=1,
            status='created'
        )
        session.add(qr_code)
        session.commit()
        session.refresh(qr_code)
        qr_mocker.return_value = {
            'close_by': 1605871409,
            'closed_at': 1605871409,
            'status': 'closed',
            'close_reason': 'payment completed'
        }
        qr_details = self.razorpayDriver.close_qr_code(qr_code.qr_id)
        assert qr_details['status'] == 'closed'
        try:
            qr_details = self.razorpayDriver.close_qr_code('invalid_id')
        except NotFoundException:
            assert True

    @patch("razorpay.resources.qrcode.Qrcode.close", side_effect=SignatureVerificationError)
    def testCloseQRCodeWithException(self, qr_mocker):
        qr_code = QRCode(
            usage=QRUsage.single_use,
            type=QRType.upi_qr,
            payment_amount='20',
            is_fixed_amount=True,
            driver=1,
            status='created'
        )
        session.add(qr_code)
        session.commit()
        session.refresh(qr_code)
        try:
            qr_details = self.razorpayDriver.close_qr_code(qr_code.qr_id)
        except Exception:
            assert True

    @patch("razorpay.utility.utility.Utility.verify_webhook_signature", return_Value=True)
    def testProcessCallbackForValidQR(self, signMock):
        requestInstance["request_body"]["payload"]["payment"]["entity"]["order_id"] = None
        requestInstance["request_body"]["payload"]["payment"]["entity"]["amount"] = 20
        requestInstance["request_body"]["payload"]["payment"]["entity"]["id"] = 'qr_143'
        requestInstance["request_body"]["event"] = 'qr_code.created'
        requestInstance["request_body"]["payload"]["qr_code"] = {
            "entity": {
                    "notes":{
                        "store_id": '13',
                        "store_type": 'pos_store_id',
                        "source_id": "233",
                    },
                    "id": 'qr_143',
                    "usage": 'single_use',
                    "type": 'upi_qr',
                    "fixed_amount": 20,
                    "amount": 20,
                    "image_url": 'image.url',
                    "close_by": 1605871409,
                    "closed_at": 1605871409,
                    "close_reason": 'payment completed',
                    "status": 'active'
                },
            }
        self.razorpayDriver.process_callback(request=requestInstance, callback_type='qr_code.created')

        statement = (
            select(TransactionCallbacks)
            .where(TransactionCallbacks.type == 'qr_code')
        )
        results = session.exec(statement).first()
        assert results != None

        requestInstance["request_body"]["event"] = 'qr_code.credited'

        self.razorpayDriver.process_callback(request=requestInstance, callback_type='qr_code.credited')

        statement = (
            select(Transaction)
            .where(Transaction.gateway_order_id == 'qr_143')
        )
        results = session.exec(statement).first()
        assert results != None

        requestInstance["request_body"]["event"] = 'qr_code.closed'
        requestInstance["request_body"]["payload"]["qr_code"]["entity"]["status"] = 'closed'

        self.razorpayDriver.process_callback(request=requestInstance, callback_type='qr_code.closed')

        statement = (
            select(QRCode)
            .where(QRCode.qr_id == 'qr_143')
        )
        qr_code = session.exec(statement).first()
        assert qr_code.status == 'closed'

    @patch("razorpay.utility.utility.Utility.verify_webhook_signature", return_Value=True)
    def testProcessCallbackForValidTransactionWithoutCallback(self, signMock):
        transactionResp = self.razorpayDriver.make_payment(transaction = transaction, make_payment_in=makePaymentInRazorpay, client=clientInstance, client_version='1.1')
        requestInstance["request_body"]["payload"]["payment"]["entity"]["order_id"] = transactionResp.gateway_order_id
        requestInstance["request_body"]["payload"]["payment"]["entity"]["id"] = transactionResp.id
        requestInstance["request_body"]["payload"]["payment"]["entity"]["captured"] = True
        requestInstance["request_body"]["event"] = 'payment.captured'
        self.razorpayDriver.process_callback(request=requestInstance, callback_type=None)
        
        statement = (
            select(Transaction)
            .where(Transaction.id == transactionResp.id)
        )
        results = session.exec(statement)
        transactionValid = results.first()
        assert transactionValid.status == STATUS_SUCCESS

        requestInstance["request_body"]["event"] = 'refund.created'
        requestInstance["request_body"]["payload"]["refund"] = {
            "entity":{
                "notes": {},
                "id": "rf_2ed4",
                "status": "created",
                "amount": 1000.00
            }
        }
        self.razorpayDriver.process_callback(request=requestInstance, callback_type=None)

        statement = (
            select(RefundTransaction)
            .where(RefundTransaction.transaction_id == transactionResp.id)
        )
        results = session.exec(statement)
        refundTransactionValid = results.first()
        assert refundTransactionValid != None

    
    @classmethod
    def tearDownClass(self):
        session.query(RefundTransaction).delete()
        session.query(TransactionCallbacks).delete()
        session.query(PaymentLink).delete()
        session.query(Transaction).delete()
        session.query(ClientGateway).delete()
        session.query(AllowedIP).delete()
        session.query(Client).delete()
        session.query(QRCode).delete()
        session.commit()
        session.close()
