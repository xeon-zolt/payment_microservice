from sqlmodel import Session, select
from payment_app.models import TransactionCallbacks
from payment_app.configs.db import engine
from payment_app.models import Transaction

def populate_payment_id():
    count = 0 
    with Session(engine) as session:
        statement = select(TransactionCallbacks).where(TransactionCallbacks.event == 'payment.failed').where(TransactionCallbacks.type=='payment').order_by(TransactionCallbacks.updated_at.desc())
        transaction = session.exec(statement)
        updated_trans = []
        for tran in transaction:
            transaction_id = tran.transaction_id
            print(transaction_id)
            if tran.transaction_id in updated_trans:
                continue
            else:
                updated_trans.append(transaction_id)
                transaction_callback = tran.callback
                print(transaction_callback)
                print(transaction_callback['payload']['payment']['entity'])
                stat = select(Transaction).where(Transaction.id == transaction_id)
                trans = session.exec(stat).first()
                print(trans.id)
                trans.callback_response = transaction_callback['payload']['payment']['entity']
                print(trans)
                session.add(trans)
                session.commit()
            #try:
            #    if rep:
                count = count + 1
            #        tran.callback_response = rep
            #        session.add(tran)
            #except:
            #    print(rep)
        print(count)
        #session.commit()


populate_payment_id()
