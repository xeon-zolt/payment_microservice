"""Module for payment services"""
from loguru import logger
from sqlmodel import Session, select
from payment_app.configs.db import engine
from payment_app.handlers.client_callback_handler import (
    client_callback_transaction_handler,
)
from payment_app.models.transaction import STATUS_SUCCESS, Transaction

def pick_success_transactions(session):
    """Pick successful transactions."""
    statement = select(Transaction).where(Transaction.status == STATUS_SUCCESS)
    transactions = session.exec(statement)
    for transaction in transactions:
        logger.info(f"resending success transaction {transaction.id}")
        client_callback_transaction_handler(
            session,
            {
                "entity": "transaction",
                "transaction": transaction,
                "driver": "razorpay",
            },
        )


def success_payment_check():
    """Get successful transactions."""
    with Session(engine) as session:
        pick_success_transactions(session)


if __name__ == "__main__":
    success_payment_check()
