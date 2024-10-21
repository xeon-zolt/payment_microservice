"""
cron job for getting status of pending redunds once every 24 hours
"""
from fastapi import BackgroundTasks
from loguru import logger
from sqlmodel import Session, select
from payment_app.configs.db import engine
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.services.payment_service import PaymentService


def pick_pending_refund_transactions(session, background_tasks: BackgroundTasks):
    """Pick pending refund transactions."""
    statement = (
        select(RefundTransaction)
        .where(RefundTransaction.status == "pending")
    )
    refunds = session.exec(statement)
    for refund in refunds:
        logger.info(f"Checking refund {refund.id}")
        driver_id = refund.transaction.driver
        payment_service = PaymentService(session, background_tasks, driver_id)
        payment_service.retry_refund(refund)


def pending_refund_check():
    """Get pending refund transactions."""
    _bg = BackgroundTasks()
    with Session(engine) as session:
        pick_pending_refund_transactions(session, _bg)


if __name__ == "__main__":
    pending_refund_check()
