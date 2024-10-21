"""Module for handling callbacks"""
import json as json_lib
import requests
from loguru import logger
from sqlmodel import col, select
from payment_app.models import Client
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.models.transaction import Transaction
from payment_app.models.transaction_communication import TransactionCommunications
from uplink import Consumer, headers, get, retry, returns, post, Body, response_handler, json
from uplink.retry.when import raises, status
from uplink.retry.stop import after_attempt, after_delay
from uplink.retry.backoff import jittered

max_attempts: int = 5

def raise_for_status(response):
    return response

class ClientCallbackHandler(Consumer):
    @headers({
        "Content-Type": "application/json",
    })
    @response_handler(raise_for_status)
    @retry(
        when=raises(Exception) | status(*[i  for i in range(400, 600)]),
        stop=after_attempt(max_attempts) | after_delay(10),
        backoff=jittered(multiplier=0.5)
        )
    @json
    @post("")
    def send_acknowledgement(self, data: Body):
        "Send Acknowledgement"
    

# TODO add client to reduce db query maybe
def client_callback_transaction_handler(session, data):
    """Callback function handler"""
    logger.info("started background task")
    client: Client = data["transaction"].client
    transaction: Transaction = data["transaction"]
    data["transaction"] = json_lib.loads(transaction.json())
    data["entity"] = ["transaction"]
    if data["event"] == "refund":
        logger.info("refund event")
        statement = select(RefundTransaction).where(
            col(RefundTransaction.refund_id) is not None).where(
            RefundTransaction.transaction_id == transaction.id,
        )
        results = session.exec(statement)
        refund_transaction: RefundTransaction = results.all()
        refund_transactions = [
            json_lib.loads(refund.json()) for refund in refund_transaction
        ]
        data["refunds"] = refund_transactions
        data["entity"].append("refunds")
    logger.info(f"client is {client.id}")
    logger.info(f"callback data is {data}")

    if data["event"] == 'refund':
        statement = select(TransactionCommunications).where(
            TransactionCommunications.transaction_id == transaction.id
        ).where(TransactionCommunications.event == 'refund')
    else:
        statement = select(TransactionCommunications).where(
            TransactionCommunications.transaction_id == transaction.id
        ).where(TransactionCommunications.event == 'transaction')
    results = session.exec(statement)
    transaction_communication = results.first()
    if not transaction_communication:
        transaction_communication = TransactionCommunications(
            transaction_id=transaction.id,
            communication_count=0,
            event=data["event"],
            status='pending',
        )
        session.add(transaction_communication)
        session.commit()
        session.refresh(transaction_communication)
        
    client_ref = ClientCallbackHandler(base_url=client.callback_url)
    result = client_ref.send_acknowledgement(data=data)

    if not result.status_code in (200, 201):
        logger.info("transaction communication failed")
        transaction_communication.communication_count = max_attempts
        transaction_communication.error = result.text
        transaction_communication.status = "failed"
        session.add(transaction_communication)
        session.commit()
        logger.info("transaction communication updated")
    else:
        logger.info("callback sent successfully")
        transaction_communication.status = "success"
        session.add(transaction_communication)
        session.commit()
        logger.info("transaction communication updated")
    logger.info("finished background task")
