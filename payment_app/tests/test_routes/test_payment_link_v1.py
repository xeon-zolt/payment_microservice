import json
import ulid

import unittest
from unittest.mock import patch, Mock

from payment_app.models import ClientGateway, Client, Transaction,AllowedIP
from payment_app.utils import get_api_key_hash
from payment_app.tests.conftest import session, client, x_api_key, x_api_key_without_gateway, mockClient

"""
Load Json of payment link
"""
with open("payment_app/tests/constant/payment_link_data.json", 'r') as file:
    payment_link_constant = json.load(file)

@patch("fastapi.Request.client", new = mockClient)
class TestPaymentLinkV1(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        clientInstance = Client(name="test",
                                callback_url='http://127.0.0.1',
                                api_key= get_api_key_hash(x_api_key),
                                active=1)
        session.add(clientInstance)
        session.commit()
        session.refresh(clientInstance)

        clientInstanceWithoutGateway = Client(name="test",
                                callback_url='http://127.0.0.1',
                                api_key= get_api_key_hash(x_api_key_without_gateway),
                                active=1)
        session.add(clientInstanceWithoutGateway)
        session.commit()
        session.refresh(clientInstanceWithoutGateway)

        allowedIPInstance = AllowedIP(client_id=clientInstance.id, 
                                    ip_range='127.0.0.1',
                                    active=1)
        session.add(allowedIPInstance)
        session.commit()
        session.refresh(allowedIPInstance)

        allowedIPInstanceWithoutGateway = AllowedIP(client_id=clientInstanceWithoutGateway.id, 
                                    ip_range='127.0.0.1',
                                    active=1)
        session.add(allowedIPInstanceWithoutGateway)
        session.commit()
        session.refresh(allowedIPInstanceWithoutGateway)

        clientGatewayInstance = ClientGateway(
            driver_id = 3,
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
                source_id=ulid.ulid(),
                payment_type='link',
                driver=1,
                gateway_order_id=ulid.ulid() ,
                status = "pending",
                api_request={},
                api_response={"id": "inv_KMqV9U0Fb0mxIt", "date": 1664264508, "type": "link", "notes": [], "terms": None, "amount": 1000, "entity": "invoice", "status": "issued", "comment": None, "paid_at": None, "receipt": None, "user_id": "", "currency": "INR", "order_id": "order_KMqVB7yC4yyHEi", "expire_by": None, "issued_at": 1664264508, "short_url": "https://rzp.io/i/bC7Ps9L", "view_less": True, "amount_due": 1000, "created_at": 1664264508, "expired_at": None, "line_items": [], "payment_id": None, "sms_status": "sent", "tax_amount": 0, "amount_paid": 0, "billing_end": None, "customer_id": "cust_KMqVAdmHSdmWU3", "description": "string", "cancelled_at": None, "email_status": "sent", "gross_amount": 1000, "billing_start": None, "invoice_number": None, "taxable_amount": 0, "currency_symbol": "₹", "partial_payment": False, "reminder_enable": False, "customer_details": {"id": "cust_KMqVAdmHSdmWU3", "name": "ashu", "email": "ashu@gmail.com", "gstin": None, "contact": "+918417809551", "customer_name": "ashu", "customer_email": "ashu@gmail.com", "billing_address": None, "customer_contact": "+918417809551", "shipping_address": None}, "group_taxes_discounts": False, "first_payment_min_amount": 0},
                store_id=ulid.ulid(),
                client_id=clientInstance.id,
                additional_info={},
                api_version=1,
                client_version="client_version",
                callback_response={},
            )

        transactionSuccess = Transaction(
                total_amount=10,
                amount=10,
                source_id=ulid.ulid(),
                payment_type='link',
                driver=1,
                gateway_order_id=ulid.ulid() ,
                status = "success",
                api_request={},
                api_response={"id": "inv_KMqV9U0Fb0mxIt", "date": 1664264508, "type": "link", "notes": [], "terms": None, "amount": 1000, "entity": "invoice", "status": "issued", "comment": None, "paid_at": None, "receipt": None, "user_id": "", "currency": "INR", "order_id": "order_KMqVB7yC4yyHEi", "expire_by": None, "issued_at": 1664264508, "short_url": "https://rzp.io/i/bC7Ps9L", "view_less": True, "amount_due": 1000, "created_at": 1664264508, "expired_at": None, "line_items": [], "payment_id": None, "sms_status": "sent", "tax_amount": 0, "amount_paid": 0, "billing_end": None, "customer_id": "cust_KMqVAdmHSdmWU3", "description": "string", "cancelled_at": None, "email_status": "sent", "gross_amount": 1000, "billing_start": None, "invoice_number": None, "taxable_amount": 0, "currency_symbol": "₹", "partial_payment": False, "reminder_enable": False, "customer_details": {"id": "cust_KMqVAdmHSdmWU3", "name": "ashu", "email": "ashu@gmail.com", "gstin": None, "contact": "+918417809551", "customer_name": "ashu", "customer_email": "ashu@gmail.com", "billing_address": None, "customer_contact": "+918417809551", "shipping_address": None}, "group_taxes_discounts": False, "first_payment_min_amount": 0},
                store_id=ulid.ulid(),
                client_id=clientInstance.id,
                additional_info={},
                api_version=1,
                client_version="client_version",
                callback_response={},
            )

        session.add(transaction)
        session.commit()
        session.refresh(transaction)

        session.add(transactionSuccess)
        session.commit()
        session.refresh(transactionSuccess)

        self.transactionId = transaction.id
        self.transactionSuccessId = transactionSuccess.id


    """
        Testcase for create payment link
    """

    def test_create_payment_link_with_invalid_client_id(self):
        test_create_payment_link_payload = payment_link_constant["CREATE_PAYMENT_LINK_PAYLOAD"]
        test_create_payment_link_payload["source_id"] = ulid.ulid()

        response = client.post("/v1/create_payment_link", json=test_create_payment_link_payload, headers={"x-api-key": x_api_key_without_gateway})
        assert response.json()["error_code"] ==  404
        assert response.json()["message"] == "gateway id provided by client not found"

    @patch("payment_app.services.payment_service.PaymentService.create_payment_link")
    def test_create_payment_link(self, mocker):
        test_create_payment_link_payload = payment_link_constant["CREATE_PAYMENT_LINK_PAYLOAD"]
        test_create_payment_link_payload["source_id"] = ulid.ulid()
        """
            Make payment_service class method "create_payment_link"
            mocker.patch(<module.className.methodName>, return_value=<mock_reponse>)
        """
        mocker.return_value = payment_link_constant["CREATE_PAYMENT_LINK"]
        response = client.post("/v1/create_payment_link", json=test_create_payment_link_payload, headers={"x-api-key": x_api_key})
        assert response.json()["response"]["status"] == "created"
        assert response.json()["response"]["id"] is not None
        assert response.json()["response"]["amount"] > 0

    """
        Testcase for cancel payment link
    """

    def test_cancel_payment_link_with_invalid_transaction_id(self):
        response = client.put("/v1/cancel_payment_link/0", json={}, headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == "transaction id not found"

    def test_cancel_payment_link_for_not_pending_transaction_status(self):
        response = client.put(f"/v1/cancel_payment_link/{self.transactionSuccessId}", json={}, headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 422
        assert response.json()["message"] == "transaction not issued"

    @patch("payment_app.services.payment_service.PaymentService.cancel_payment_link")
    def test_cancel_payment_link_with_valid_transaction_id(self, mocker):
        mocker.return_value = payment_link_constant["CANCEL_PAYMENT_LINK"]
        response = client.put(f"/v1/cancel_payment_link/{self.transactionId}", json={}, headers={"x-api-key": x_api_key})
        assert response.json()["response"]["status"] == "cancelled"
        assert response.json()["response"]["id"] is not None
        assert response.json()["response"]["amount"] > 0

    """
        Testcase for resend payment link
    """

    def test_resend_payment_link_with_invalid_transaction(self):
        response = client.post("/v1/resend_payment_link", json={
            "transaction_id": 0,
            "medium": "sms"
        }, headers={"x-api-key": x_api_key})
        assert response.json()["detail"]["error"] == "transaction id not found"

    @patch("payment_app.services.payment_service.PaymentService.resend_payment_link")
    def test_resend_payment_link_with_valid_transaction(self, mocker):
        mocker.return_value = payment_link_constant["RESEND_PAYMENT_LINK"]
        response = client.post(f"/v1/resend_payment_link", json={
            "transaction_id": self.transactionId,
            "medium": "sms"
        }, headers={"x-api-key": x_api_key})
        assert response.json()["response"]["success"] == True

    @classmethod
    def tearDownClass(self):
        session.query(Transaction).delete()
        session.query(ClientGateway).delete()
        session.query(AllowedIP).delete()
        session.query(Client).delete()
        session.commit()
        session.close()