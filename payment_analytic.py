import razorpay
import toml
import os
import time

from sqlmodel import Session, select

from payment_app.models import Transaction
from payment_app.configs.db import engine

from payment_app.models.payment_analytic import PaymentAnalytic
session = Session(engine)

current_req_slot = {
    "skip": 0,
    "limit": 50,
    # get total row count
    "total_rows": 0
}

def get_payment_analytic_count():
    analytic_count = session.query(PaymentAnalytic.transaction_id).distinct().count()
    current_req_slot["skip"] = analytic_count
    current_req_slot["total_rows"] = session.query(Transaction).count()

def get_transactions(skip, limit):
    statement = select(Transaction).where(Transaction.status != 'pending').offset(skip).limit(limit)
    transactions = session.exec(statement)
    return transactions

def get_env_by_driver_id(driver_id: int): 
    payment_config = toml.load(os.environ.get("PAYMENT_CONFIG_PATH", "config.toml"))
    for gateway in payment_config["gateway"]:
        if driver_id == gateway["id"]:
            _config = gateway
            break
    client = razorpay.Client(auth=(_config["key_id"], _config["key_secret"]))
    return client

def payment_analytic():
    transactions = get_transactions(current_req_slot["skip"], current_req_slot["limit"])
    for transaction in transactions:
        get_details(transaction, get_env_by_driver_id(transaction.driver))
        time.sleep(2)

def get_details(tran, client):
    current_req_slot["skip"] += 1
    print('crt slot', current_req_slot)
    if tran.gateway_order_id:
        if str(tran.gateway_order_id).startswith('qr_'):
            gateway_res = client.qrcode.fetch_all_payments(tran.gateway_order_id, {})
        else:
            gateway_res = client.order.payments(tran.gateway_order_id)
        
        for item in gateway_res["items"]:              
            statement = select(PaymentAnalytic).where(PaymentAnalytic.payment_id == item["id"])
            result = session.exec(statement).first()
            if not result:
                payload = {
                    "card_id": "",
                    "name": "",
                    "network": "",
                    "type": "",
                    "issuer": ""
                }
                if item["method"] == 'card':
                    payload["card_id"] = item["card"]["id"]
                    payload["name"] = item["card"]["name"]
                    payload["network"] = item["card"]["network"]
                    payload["type"] = item["card"]["type"]
                    payload["issuer"] = item["card"]["issuer"]

                payment_history = PaymentAnalytic(
                    transaction_id=tran.id,
                    order_id=item["order_id"],
                    payment_id=item["id"],
                    razorpay_status=item["status"],
                    status=tran.status,
                    step=item["error_step"],
                    payment_method=item["method"],
                    reason=item["error_description"],
                    card_id=payload["card_id"],
                    card_name=payload["name"],
                    card_type=payload["type"],
                    card_network=payload["network"],
                    issuer=payload["issuer"],
                )
                session.add(payment_history)
                session.commit()
            else:
                print('payment_id already exists', item["id"])
    else:
        print('gateway_order_id = null', tran)
    

def populate_payment_analytics():
    while current_req_slot["skip"] < current_req_slot["total_rows"]:
        payment_analytic()

get_payment_analytic_count()
populate_payment_analytics()
