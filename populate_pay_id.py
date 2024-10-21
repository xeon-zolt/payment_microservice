from sqlmodel import Session, select
from payment_app.models.transaction import Transaction
from payment_app.configs.db import engine


def populate_payment_id():
    count = 0 
    with Session(engine) as session:
        statement = select(Transaction)
        transaction = session.exec(statement)
        for tran in transaction:
            rep = tran.api_response
            try:
                if rep and 'pay' in rep['id']:
                    count = count + 1
                    print(rep['id'])
                    tran.gateway_payment_id = rep['id']
                    session.add(tran)
            except:
                print(rep)
        print(count)
        session.commit()


populate_payment_id()
