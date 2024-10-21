"""
cron job for hitting callback of client till client recived the information on success or failur
"""

from datetime import datetime, timedelta

from loguru import logger
from sqlmodel import Session, select

from payment_app.configs.db import engine
from payment_app.handlers.client_callback_handler import (
    client_callback_transaction_handler,
)
from payment_app.models.transaction_communication import TransactionCommunications
from payment_app.utils import get_driver_name


def pick_clients(session):
    """Pick successful transaction communications."""
    statement = (
        select(TransactionCommunications)
        .where(TransactionCommunications.communication_count <= 50)
        .where(TransactionCommunications.status != "success")
    ).order_by(TransactionCommunications.created_at.desc()).limit(50)
    results = session.exec(statement)
    return results


def communicate_with_client():
    """Handle client callbacks."""
    with Session(engine) as session:
        logger.info("clients")
        clients = pick_clients(session)
        for client in clients:
            logger.info(client)
            client_callback_transaction_handler(
                session,
                {
                    "event": client.event,
                    "transaction": client.transaction,
                    "driver": get_driver_name(client.transaction.driver),
                },
            )



if __name__ == "__main__":
    communicate_with_client()
