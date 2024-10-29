import json
import ulid

import unittest
from unittest.mock import patch

from payment_app.models import ClientGateway, Client, Transaction, AllowedIP
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.utils import get_api_key_hash
from payment_app.tests.conftest import session, client, x_api_key, mockClient

"""
    Load Json of payment link
"""
with open("payment_app/tests/constant/payment_link_data.json", 'r') as file:
    payment_payload = json.load(file)

@patch("fastapi.Request.client", new = mockClient)
class TestPaymentApisV1(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        session.begin()
        clientInstance = Client(name="test",
                                callback_url='http://127.0.0.1',
                                api_key= get_api_key_hash(x_api_key),
                                active=1)
        session.add(clientInstance)
        session.commit()
        session.refresh(clientInstance)

        allowedIPInstance = AllowedIP(client_id=clientInstance.id, 
                                    ip_range='127.0.0.1',
                                    active=1)
        session.add(allowedIPInstance)
        session.commit()
        session.refresh(allowedIPInstance)

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
            total_amount= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["total_amount"],
            amount= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["amount"],
            source_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["source_id"],
            payment_type= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["payment_type"],
            driver= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["driver"],
            gateway_order_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_order_id"],
            status= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["status"],
            api_request= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_request"],
            api_response= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_response"],
            store_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["store_id"],
            client_id= None,
            additional_info= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["additional_info"],
            api_version= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_version"],
            client_version= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["client_version"],
            api_status= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_status"],
            callback_response= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["callback_response"],
            gateway_payment_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_payment_id"],
        )

        transactionAmountCheck = Transaction(
            total_amount= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["total_amount"],
            amount= 9.00,
            source_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["source_id"],
            payment_type= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["payment_type"],
            driver= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["driver"],
            gateway_order_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_order_id"],
            status= "success",
            api_request= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_request"],
            api_response= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_response"],
            store_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["store_id"],
            client_id= None,
            additional_info= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["additional_info"],
            api_version= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_version"],
            client_version= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["client_version"],
            api_status= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_status"],
            callback_response= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["callback_response"],
            gateway_payment_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_payment_id"],
        )
        transactionSuccess = Transaction(
            total_amount= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["total_amount"],
            amount= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["amount"],
            source_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["source_id"],
            payment_type= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["payment_type"],
            driver= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["driver"],
            gateway_order_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["gateway_order_id"],
            status= "success",
            api_request= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_request"],
            api_response= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["api_response"],
            store_id= payment_payload["MAKE_PAYMENT_RESPONSE"]["transaction"]["store_id"],
            client_id= None,
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
        session.add(transactionAmountCheck)
        session.commit()
        session.refresh(transactionAmountCheck)
        session.add(transactionSuccess)
        session.commit()
        session.refresh(transactionSuccess)

        refund_transaction = RefundTransaction(
            transaction_id=transaction.id,
            refund_id=transaction.id,
            api_request={"data": {"receipt": "56fa4b62-4045-4aa7-998c-8b2b27f6c951"}, "amount": 100, "payment_id": "pay_JDIgZ4mIvaIKTw"},
            api_response={"id": "rfnd_JGOJVluOYJMgno", "notes": [], "amount": 200, "entity": "refund", "status": "processed", "receipt": "3622d849-7063-4f6f-920d-a1bcae0350cd", "batch_id": None, "currency": "INR", "created_at": 1649318113, "payment_id": "pay_JGOJ4oPfbkKSoi", "refund_type": "", "processed_at": None, "acquirer_data": {"arn": None}, "speed_processed": "normal", "speed_requested": "normal"},
            api_status=200,
            callback_response= {"id": "rfnd_KNiEDViGF5gtB3", "notes": {"transaction_id": "01GE4A4E7GNE05TSTV7359X5MK", "order_payment_id": 10501370, "refund_for_order_id": "1b848a4f-c22a-496d-b1f8-c7a4ab179bf7", "refund_transaction_id": "01GE4JR5BFRHD06G9AGWRTC22E"}, "amount": 82400, "entity": "refund", "status": "processed", "receipt": "1b848a4f-c22a-496d-b1f8-c7a4ab179bf7", "batch_id": None, "currency": "INR", "created_at": 1664453712, "payment_id": "pay_KNffH8ubvcYxRg", "acquirer_data": {"arn": None}, "speed_processed": "normal", "speed_requested": "normal"},
            status="pending",
            amount=transaction.amount,
            additional_info={}
        )
        session.add(refund_transaction)
        session.commit()
        session.refresh(refund_transaction)

        self.trasactionId = transaction.id
        self.transactionStatus = transaction.status
        self.trasactionIdAmount = transactionAmountCheck.id
        self.trasactionSuccess = transactionSuccess.id
        

    """
        Make Payment Testcases
    """

    def test_make_payment_where_total_amount_less_then_amount_to_pay(self):
        payload: dict[str, any] = payment_payload["MAKE_PAYMENT"]
        payload["amount_to_pay"] = 11.00

        response = client.post("/v1/make_payment", json=payload, headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 422
        assert response.json()["message"] == "total amount cannot be greater than amount to pay"

    def test_make_payment_with_invalid_driver_id(self):
        payload: dict[str, any] = payment_payload["MAKE_PAYMENT"]
        payload["driver_id"] = 5
        response = client.post("/v1/make_payment", json=payload, headers={"x-api-key": x_api_key})
        assert response.json()["detail"][0]["msg"] == "No match for discriminator 'driver_id' and value 5 (allowed values: 1, 2, '1', '2', '3', 3)"
        assert response.status_code == 422

    def test_make_payment_where_driver_id_not_mapped_with_client(self):
        payload: dict[str, any] = {
            "driver_id": 2,
            "total_amount": 10.00,
            "amount_to_pay": 10.00,
            "payment_type": "",
            "source_id": "",
            "store_id": 63,
            "additional_info": {}
        }

        response = client.post("/v1/make_payment", json=payload, headers={"x-api-key": x_api_key})
        print("sdfsdfsd", response.json())
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == "gateway id provided by client not found"

    @patch("payment_app.services.payment_service.PaymentService.make_payment")
    def test_make_payment_with_valid_request(self, mocker):
        payload: dict[str, any] = {
            "driver_id": 1,
            "total_amount": 10.00,
            "amount_to_pay": 10.00,
            "payment_type": "app_mall",
            "source_id": ulid.ulid(),
            "store_id": 63,
            "additional_info": {}
        }
        mocker.return_value = payment_payload["MAKE_PAYMENT_RESPONSE"]
        response = client.post("/v1/make_payment", json=payload, headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert response.json()["response"]["entity"] == "transaction"
        assert response.json()["response"]["transaction"]["id"] is not None
        assert response.json()["response"]["transaction"]["gateway_order_id"] is not None

    @patch("payment_app.services.payment_service.PaymentService.create_payment_link")
    def test_create_payment_link(self, mocker):
        payload: dict[str, any] = payment_payload["CREATE_PAYMENT_LINK_PAYLOAD"]
        mocker.return_value = payment_payload["CREATE_PAYMENT_LINK"]
        response = client.post("/v1/create_payment_link", json=payload, headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert response.json()["response"]["id"] is not None
        assert response.json()["response"]["short_url"] is not None

    """
        Refund Payment Testcases
    """

    def test_refund_payment_with_invalid_transaction_id(self):
        payload: dict[str, any] = payment_payload["REFUND_PAYMENT"]
        payload["payment_transaction_id"] = 0
        response = client.post("/v1/refund_payment", json=payload, headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == "Transaction not found"

    def test_refund_payment_where_transaction_status_not_success(self):
        payload: dict[str, any] = payment_payload["REFUND_PAYMENT"]
        payload["payment_transaction_id"] = self.trasactionId
        response = client.post("/v1/refund_payment", json=payload, headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 422
        assert response.json()["message"] == f"Refund can not be processed for {self.transactionStatus} transaction."

    def test_refund_payment_where_amount_to_refund_greater_then_amount(self):
        payload: dict[str, any] = payment_payload["REFUND_PAYMENT"]
        payload["payment_transaction_id"] = self.trasactionIdAmount
        response = client.post("/v1/refund_payment", json=payload, headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 403
        assert response.json()["message"] == "The total refund amount is greater than the refund payment amount"

    @patch("payment_app.services.payment_service.PaymentService.refund_payment")
    def test_refund_payment_with_valid_transaction(self, mocker):
        payload: dict[str, any] = payment_payload["REFUND_PAYMENT"]
        payload["payment_transaction_id"] = self.trasactionSuccess
        mocker.return_value = payment_payload["REFUND_PAYMENT_RESPONSE"]
        response = client.post("/v1/refund_payment", json=payload, headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert response.json()["response"]["id"] is not None
        assert response.json()["response"]["refund_id"] is not None
        assert response.json()["response"]["status"] == "success"
        assert response.json()["response"]["api_status"] == 200

    """ 
        Get Payment Status Testcases
    """

    def test_transaction_payment_status_with_invalid_transaction_id(self):
        response = client.get("/v1/get_payment_status?transaction_id=0&recheck=false&entity=transaction", headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == "Transaction not found"

    def test_transaction_payment_status_where_recheck_false(self):
        response = client.get(f"/v1/get_payment_status?transaction_id={self.trasactionId}&recheck=false&entity=transaction", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert response.json()["entity"][0] == "transaction"
        assert response.json()["event"] == "transaction"
        assert response.json()["transaction"]["id"] is not None
        assert response.json()["transaction"]["source_id"] is not None

    def test_refund_transaction_status_with_invalid_refund_id(self):
        response = client.get(f"/v1/get_payment_status?transaction_id=0&recheck=false&entity=refund", headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == "Refund not found for transaction 0"

    def test_refund_transaction_status_where_recheck_false(self):
        response = client.get(f"/v1/get_payment_status?transaction_id={self.trasactionId}&recheck=false&entity=refund", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert response.json()["entity"][0] == "refund"
        assert response.json()["event"] == "refund"
        assert response.json()["refund"]["id"] is not None
        assert response.json()["refund"]["refund_id"] is not None

    @classmethod
    def tearDownClass(self):
        session.query(RefundTransaction).delete()
        session.query(Transaction).delete()
        session.query(ClientGateway).delete()
        session.query(AllowedIP).delete()
        session.query(Client).delete()
        session.commit()
        session.close()
