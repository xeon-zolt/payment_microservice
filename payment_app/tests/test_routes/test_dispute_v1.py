import json
import ulid

import unittest
from unittest.mock import patch
from payment_app.lib.errors.error_handler import NotFoundException

from payment_app.models import ClientGateway, Client, Transaction, AllowedIP
from payment_app.models.dispute import DisputDocuments, Dispute, DisputeEvidence
from payment_app.utils import get_api_key_hash
from payment_app.tests.conftest import session, client, x_api_key, mockClient

with open("payment_app/tests/constant/dispute_mock.json", 'r') as file:
    dispute_data = json.load(file)
    
@patch("fastapi.Request.client", new = mockClient)
class TestDisputeApisV1(unittest.TestCase):
    __dispute: Dispute
    
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
        
        dispute_evidence = DisputeEvidence (
            amount=dispute_data["DISPUTE_EVIDENCE"]["amount"],
            summary=dispute_data["DISPUTE_EVIDENCE"]["summary"],
            shipping_proof=dispute_data["DISPUTE_EVIDENCE"]["shipping_proof"],
            billing_proof=dispute_data["DISPUTE_EVIDENCE"]["billing_proof"],
            cancellation_proof=dispute_data["DISPUTE_EVIDENCE"]["cancellation_proof"],
            customer_communication=dispute_data["DISPUTE_EVIDENCE"]["customer_communication"],
            proof_of_service=dispute_data["DISPUTE_EVIDENCE"]["proof_of_service"],
            explanation_letter=dispute_data["DISPUTE_EVIDENCE"]["explanation_letter"],
            refund_confirmation=dispute_data["DISPUTE_EVIDENCE"]["refund_confirmation"],
            access_activity_log=dispute_data["DISPUTE_EVIDENCE"]["access_activity_log"],
            refund_cancellation_policy=dispute_data["DISPUTE_EVIDENCE"]["refund_cancellation_policy"],
            term_and_conditions=dispute_data["DISPUTE_EVIDENCE"]["term_and_conditions"],
            others=dispute_data["DISPUTE_EVIDENCE"]["others"],
            submitted_at=dispute_data["DISPUTE_EVIDENCE"]["submitted_at"]
        )
        session.add(dispute_evidence)
        session.commit()
        session.refresh(dispute_evidence)
        
        dispute = Dispute(
            dispute_id=dispute_data["DISPUTES"]["dispute_id"],
            entity=dispute_data["DISPUTES"]["entity"],
            payment_id=dispute_data["DISPUTES"]["payment_id"],
            amount=dispute_data["DISPUTES"]["amount"],
            currency=dispute_data["DISPUTES"]["currency"],
            comments=dispute_data["DISPUTES"]["comments"],
            gateway_dispute_id=dispute_data["DISPUTES"]["gateway_dispute_id"],
            amount_deducted=dispute_data["DISPUTES"]["amount_deducted"],
            reason_code=dispute_data["DISPUTES"]["reason_code"],
            respond_by=dispute_data["DISPUTES"]["respond_by"],  
            status='open',
            phase=dispute_data["DISPUTES"]["phase"],
            driver_created_at=dispute_data["DISPUTES"]["driver_created_at"],
            driver_id=dispute_data["DISPUTES"]["driver_id"],
            dispute_evidence_id=dispute_evidence.id,
        )
        
        session.add(dispute)
        session.commit()
        session.refresh(dispute)
        self.__dispute = dispute
        
    def test_get_disputes(self):
        response = client.get("/v1/disputes?page=1&limit=10", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert type(response.json()["results"]) == list
        assert response.json()["total"] > 0
    
    def test_get_dispute_by_invalid_id(self):
        response = client.get("/v1/disputes/0", headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == 'Dispute not found!'
    
    def test_accept_dispute_by_invalid_id(self):
        response = client.post("/v1/disputes/accept/0", headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == 'Dispute not found'
    
    @patch("payment_app.services.payment_service.PaymentService.accept_dispute")   
    def test_accept_dispute_by_valid_id(self, mocker):
        mocker.return_value = dispute_data["ACCEPT_DISPUTE"]
        response = client.post(f"/v1/disputes/accept/{self.__dispute.id}", headers={"x-api-key": x_api_key})
        assert response.json()["response"]["status"] == 'lost'
        assert response.status_code == 200
    
    def test_contest_dispute_by_invalid_id(self):
        response = client.post("/v1/disputes/contest/0", headers={"x-api-key": x_api_key})
        assert response.json()["error_code"] == 404
        assert response.json()["message"] == 'Dispute not found'
        
    @patch("payment_app.services.payment_service.PaymentService.contest_dispute")   
    def test_contest_dispute_by_valid_id(self, mocker):
        mocker.return_value = dispute_data["CONTEST_DISPUTE"]
        response = client.post(f"/v1/disputes/contest/{self.__dispute.id}", headers={"x-api-key": x_api_key})
        assert response.json()["response"]["status"] == 'open'
        assert response.status_code == 200

    @patch("payment_app.services.payment_service.PaymentService.accept_dispute")
    def test_accept_dispute_successfully(self, mocker):
        mocker.return_value = dispute_data["ACCEPT_DISPUTE"]
        response = client.post(f"/v1/disputes/accept/{self.__dispute.id}", headers={"x-api-key": x_api_key})
        assert response.status_code == 200
        assert response.json()["response"]["status"] == 'lost'
        
    @classmethod
    def tearDownClass(self):
        session.query(Dispute).delete()
        session.query(DisputDocuments).delete()
        session.query(DisputeEvidence).delete()
        session.query(ClientGateway).delete()
        session.query(AllowedIP).delete()
        session.query(Client).delete()
        session.commit()
        session.close()
