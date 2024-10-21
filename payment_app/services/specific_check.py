"""
cron job for getting status of pending payments once every 24 hours
"""

from fastapi import BackgroundTasks
from sqlmodel import Session, select
from payment_app.configs.db import engine
from payment_app.models.transaction import Transaction
from payment_app.services.payment_service import PaymentService


def pick_pending_transactions(session, background_tasks: BackgroundTasks):
    """Pick pending transactions."""
    statement = (
        select(Transaction)
        .where(Transaction.id == '01GJ7B7P8J2W84S9QWH3YPTWDD')
    )
    transactions = session.exec(statement)
    for transaction in transactions:
        driver_id = transaction.driver
        payment_service = PaymentService(session, background_tasks, driver_id)
        payment_service.get_payment_status(transaction)


def pending_payment_check():
    """Get pending transactions."""
    _bg = BackgroundTasks()
    with Session(engine) as session:
        pick_pending_transactions(session, _bg)


if __name__ == "__main__":
    pending_payment_check()
