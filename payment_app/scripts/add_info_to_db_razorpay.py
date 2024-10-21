"""Module to populate refund transaction details."""
from sqlmodel import Session, select
from payment_app.models.refund_transactions import RefundTransaction
from payment_app.configs.db import engine


def populate_add_info():
    """Method to populate notes in refund transactions."""
    with Session(engine) as session:
        statement = select(RefundTransaction).where(RefundTransaction.additional_info is None)
        ref_transaction = session.exec(statement)
        print(ref_transaction)
        for ref in ref_transaction:
            req = ref.request
            print(req)
            if req and "data" in req:
                req_data = req["data"]
                print(req_data)
                if "notes" in req_data:
                    notes = req_data["notes"]
                    if notes:
                        print(notes)
                        ref.additional_info = notes
                        session.add(ref)
        session.commit()


populate_add_info()
