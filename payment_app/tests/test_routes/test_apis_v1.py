import unittest
import ulid
from unittest.mock import patch

from payment_app.models import Client,AllowedIP,Transaction
from payment_app.utils import get_api_key_hash
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.tests.conftest import session, client, x_api_key, x_api_key_wrong, mockClient
@patch("fastapi.Request.client", new = mockClient)
class TestApiV1(unittest.TestCase):

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
        allowedIPInstance  = AllowedIP(client_id=clientInstance.id, 
                                    ip_range='127.0.0.1',
                                    active=1)
        session.add(allowedIPInstance)
        session.commit()
        session.refresh(allowedIPInstance)
        transaction = Transaction(
                total_amount=10,
                amount=10,
                source_id=ulid.ulid(),
                payment_type='link',
                driver=1,
                gateway_order_id=ulid.ulid() ,
                status = "pending",
                api_request={},
                api_response={},
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

        refund_transaction = RefundTransaction(
                transaction_id=transaction.id,
                refund_id=ulid.ulid(),
                api_request={},
                api_response={},
                api_status=200,
                callable_response={},
                status="pending",
                amount=10.00,
                additional_info={})
        session.add(refund_transaction)
        session.commit()
        session.refresh(refund_transaction)

        self.transactionId = transaction.id
        self.refundTransactionId = refund_transaction.id

    """
        test case for validate token
    """

    def test_invalid_token(self):
        response = client.get("/admin/v1/get_transactions?page=0&limit=10&ordering=-created_at", headers={"x-api-key": x_api_key_wrong})
        assert response.status_code == 403
        assert response.json()['detail']['error'] == "Wrong Api Token"

    """
        test case for Transaction
    """

    def test_get_transactions_with_empty_list(self):
        response = client.get("/admin/v1/get_transactions?page=0&limit=0&ordering=-created_at", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert isinstance(response.json()["results"], list) 
        assert response.json()["total"] == 1

    def test_get_transactions_with_valid_transactions(self):
        response = client.get("/admin/v1/get_transactions?page=1&limit=10&ordering=-created_at", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert isinstance(response.json()["results"], list) 
        assert response.json()["total"] == 1

    def test_get_transaction_with_invalid_id(self):
        response = client.get("/admin/v1/get_transaction/12312312", headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == "Transaction not found!"

    def test_get_transaction_with_valid_id(self):
        response = client.get(f"/admin/v1/get_transaction/{self.transactionId}", headers={"x-api-key": x_api_key})
        assert response.status_code == 200

    """
        Test case for refund transaction
    """
    def test_get_refund_transactions_with_empty_list(self):
        response = client.get("/admin/v1/get_refund_transactions?page=1&limit=10&ordering=-created_at", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert isinstance(response.json()["results"], list) 
        assert response.json()["total"] == 1

    def test_get_refund_transaction_with_invalid_id(self):
        response = client.get("/admin/v1/get_refund_transactions/0", headers={"x-api-key": x_api_key})
        print("ressfs", response.json())
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == "Refund Transaction not found!"

    def test_get_refund_transaction_with_valid_id(self):
        response = client.get(f"/admin/v1/get_refund_transactions/{self.refundTransactionId}", headers={"x-api-key": x_api_key})
        assert response.status_code == 200

    def test_get_refund_transactions_with_valid_refund_transactions(self):
        response = client.get("/admin/v1/get_refund_transactions?page=1&limit=10&ordering=-created_at", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert isinstance(response.json()["results"], list) 
        assert response.json()["total"] == 1
    
    @classmethod
    def tearDownClass(self):
        session.query(RefundTransaction).delete()
        session.query(Transaction).delete()
        session.query(AllowedIP).delete()
        session.query(Client).delete()
        session.commit()
        session.close()




