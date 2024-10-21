from payment_app.models.access_client_relation import AccessClientMapper
from payment_app.models.access_points import AccessPoint
from sqlmodel import Session, select
from fastapi import Depends
from payment_app.configs.db import engine

data = {
    'relations' : {
        '1': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
            # Payment Link
            'create_payment_link',
            'cancel_payment_link',
            'resend_payment_link',
            'get_payment_link_status',
        ],
        '2': [
            # Admin apis
            'get_transactions',
            'get_transaction',
            'get_refunc_transactions',
            'get_endpoints',
            'get_client_endpoints',
            'get_payment_methods',
            'payment_downtime',
            # Dispute and documents
            'disputes',
            'documents', 
        ],
        '3': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
        '4': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
        '5': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
        '6': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
        '7': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
        '8': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
        '9': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
        '10': [
            # Version 1 Apis
            'get_payment_status_by_source_id',
            'make_payment',
            'refund_payment',
            'get_payment_status',
            'retry_payment',
            'register_callback_url',
            'get_transaction_by_payment_id',
        ],
    },
    'endpoints' : [
        # Version 1 Apis
        'get_payment_status_by_source_id',
        'make_payment',
        'refund_payment',
        'get_payment_status',
        'retry_payment',
        'register_callback_url',
        'get_transaction_by_payment_id',
        # Payment Link
        'create_payment_link',
        'cancel_payment_link',
        'resend_payment_link',
        'get_payment_link_status',
        # Admin apis
        'get_transactions',
        'get_transaction',
        'get_refunc_transactions',
        'get_endpoints',
        'get_client_endpoints',
        'get_payment_methods',
        'payment_downtime',
        # Qr Code
        'create_qr_code',
        'close_qr_code',
        'get_qr_code_status',
        # Dispute and documents
        'disputes',
        'documents', 
    ]
}


def populate_endpoints():
    with Session(engine) as session:
        for endpoint in data['endpoints']:
            statement = select(AccessPoint).where(AccessPoint.endpoint == endpoint)
            endpoint_obj = session.exec(statement).first()
            if not endpoint_obj:
                session.add(AccessPoint(endpoint=endpoint))
                session.commit()

def populate_endpoint_client_relations():
    with Session(engine) as session:
        for client_id, endpoints in data['relations'].items():
            for endpoint in endpoints:
                statement = select(AccessPoint).where(AccessPoint.endpoint == endpoint)
                endpoint_obj = session.exec(statement).first()
                if endpoint_obj:
                    statement = select(AccessClientMapper).where(
                        AccessClientMapper.endpoint_id == endpoint_obj.id
                    ).where(
                        AccessClientMapper.client_id == client_id
                    )
                    client_access_map = session.exec(statement).first()
                    if not client_access_map:
                        relation_object = AccessClientMapper(endpoint_id=endpoint_obj.id, client_id=client_id)
                        session.add(relation_object)
                        session.commit()

populate_endpoints()
populate_endpoint_client_relations()