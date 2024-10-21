from loguru import logger
from sqlmodel import Session, select
from payment_app.configs.db import engine
from payment_app.handlers.client_callback_handler import (
    client_callback_transaction_handler,
)
from payment_app.models.transaction import STATUS_SUCCESS, Transaction
from datetime import datetime, timedelta    

def pick_success_transactions(session):
    last_month = (datetime.now() - timedelta(days=40))
    statement = select(Transaction).where(Transaction.id == '01GS9HDEQSG4CJMFQ0MA3KPVKD')
    #.where(Transaction.created_at <= last_month)
    transactions = session.exec(statement)
    for transaction in transactions:
        logger.info(f"resending success transaction {transaction.id}")
        client_callback_transaction_handler(
            session,
            {
                "event": "transaction",
                "transaction": transaction,
                "driver": "razorpay",
            },
        )


def success_payment_check():
    with Session(engine) as session:
        pick_success_transactions(session)


if __name__ == "__main__":
    success_payment_check()
