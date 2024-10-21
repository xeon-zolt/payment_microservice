"""
cron job for getting status of pending payments once every 24 hours
"""

from fastapi import BackgroundTasks
from loguru import logger
from sqlmodel import Session, select

from payment_app.configs.db import engine
from payment_app.models.transaction import STATUS_SUCCESS, Transaction
from payment_app.services.payment_service import PaymentService


def pick_pending_transactions(session, background_tasks: BackgroundTasks):
    """Pick pending transactions."""
    statement = (
        select(Transaction)
        .where(Transaction.status != STATUS_SUCCESS)
    ).limit(200)
    transactions = session.exec(statement)
    for transaction in transactions:
        logger.info(f"Checking transaction {transaction.id}")
        driver_id = transaction.driver
        payment_service = PaymentService(session, background_tasks, driver_id)
        payment_service.get_payment_status(transaction, send_callback=True)


def pending_payment_check():
    """Get pending transactions."""
    _bg = BackgroundTasks()
    with Session(engine) as session:
        pick_pending_transactions(session, _bg)


if __name__ == "__main__":
    pending_payment_check()
