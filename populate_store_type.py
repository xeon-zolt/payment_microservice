from typing import List
from sqlmodel import Session, select
from payment_app.models.transaction import Transaction
from payment_app.configs.db import engine

def populate_store_type():
    with Session(engine) as session:
        statement = select(Transaction)
        transaction: List[Transaction] = session.exec(statement)
        for tran in transaction:
            if tran.payment_type == 'link':
                tran.store_type = 'bd_store_id'
            else:
                tran.store_type = 'pos_store_id'
            session.add(tran)
        session.commit()

populate_store_type()
