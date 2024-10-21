from uplink import Consumer, headers, get, retry, returns
import toml
import os
from sqlmodel import Session, select
from payment_app.configs.db import engine
from payment_app.models import Dispute, DisputeEvidence, DisputDocuments
import datetime

class RazorpayDispute(Consumer):
    @returns.json(key="items")
    @retry(
        # Retry on 503 response status code or any exception.
        when=retry.when.status(503) | retry.when.raises(Exception),
        # Stop after 5 attempts or when backoff exceeds 10 seconds.
        stop = retry.stop.after_attempt(5) | retry.stop.after_delay(10),
        # Use exponential backoff with added randomness.
        backoff = retry.backoff.jittered(multiplier=0.5)
    )
    @headers({
        "Content-Type": "application/json",
    })
    @get('?count=1&skip={skip}') #add skip and count
    def populate_disputes(self, skip: int):
        """ fetch all the disputes from razorpay """

class RazorpayDocument(Consumer):
    @headers({
        "Content-Type": "application/json",
    })
    @returns.json()
    @get()
    def get_document(self):
        """ fetch document info """

    @get("/content")
    def download_document(self):
        """ download document """


def populate():
    print(1.1)
    payment_config = toml.load(os.environ.get("PAYMENT_CONFIG_PATH", "config.toml"))
    for gateway in payment_config["gateway"]:
        print('1.1.1')
        if gateway['driver'] == 'razorpay':
            key_id = gateway["key_id"]
            key_secret = gateway["key_secret"]
            driver_id = gateway["id"]
            disputes = RazorpayDispute(base_url="https://api.razorpay.com/v1/disputes",
                                       auth=(f"{key_id}", f"{key_secret}"))
            skip=0
            while True:
                skip+=1
                dispute = disputes.populate_disputes(skip)
                print('1.1.2')
                if dispute:
                    print('1.1.3')
                    dispute = dispute[0]
                    with Session(engine) as session:
                        evidence = None
                        print(1.2)
                        if 'evidence' in dispute.keys() and dispute['evidence']:
                            breakpoint()
                            evidence = DisputeEvidence(amount=dispute['evidence']["amount"],
                                                       summary=dispute['evidence']["summary"],
                                                       shipping_proof=dispute['evidence']["shipping_proof"],
                                                       billing_proof=dispute['evidence']["billing_proof"],
                                                       cancellation_proof=dispute['evidence']["cancellation_proof"],
                                                       customer_communication=dispute['evidence']["customer_communication"],
                                                       proof_of_service=dispute['evidence']["proof_of_service"],
                                                       explanation_letter=dispute['evidence']["explanation_letter"],
                                                       refund_confirmation=dispute['evidence']["refund_confirmation"],
                                                       access_activity_log=dispute['evidence']["access_activity_log"],
                                                       refund_cancellation_policy=dispute['evidence']["refund_cancellation_policy"],
                                                       term_and_conditions=dispute['evidence']["terms_and_conditions"],
                                                       others=dispute['evidence']["others"],
                                                       submitted_at=datetime.datetime.utcfromtimestamp(dispute['evidence']["submitted_at"]))
                            session.add(evidence)
                            session.commit()
                            session.refresh(evidence)
                            shipping_proof_docs = dispute['evidence'].get('shipping_proof') or []
                            billing_proof_docs = dispute['evidence'].get('billing_proof') or []
                            cancellation_proof_docs = dispute['evidence'].get('cancellation_proof') or []
                            customer_communication_docs = dispute['evidence'].get('customer_communication') or []
                            proof_of_service_docs = dispute['evidence'].get('proof_of_service') or []
                            explanation_letter_docs = dispute['evidence'].get('explanation_letter') or []
                            refund_confirmation_docs = dispute['evidence'].get('refund_confirmation') or []
                            access_activity_log_docs = dispute['evidence'].get('access_activity_log') or []
                            refund_cancellation_policy_docs = dispute['evidence'].get('refund_cancellation_policy') or []
                            term_and_conditions_docs = dispute['evidence'].get('term_and_conditions') or []
                            other_docs = dispute['evidence'].get('others') or []
                            other_docs_flat = []
                            other_docs = [flat_doc for flat_doc in [doc['document_ids'] for doc in other_docs]]
                            [other_docs_flat.extend(l) for l in other_docs]
                            all_docs = []
                            [all_docs.extend(l) for l in (shipping_proof_docs,
                                                          billing_proof_docs,
                                                          cancellation_proof_docs,
                                                          customer_communication_docs,
                                                          proof_of_service_docs,
                                                          explanation_letter_docs,
                                                          refund_confirmation_docs,
                                                          access_activity_log_docs,
                                                          refund_cancellation_policy_docs,
                                                          term_and_conditions_docs,
                                                          other_docs_flat
                                                          )]
                            # if customer_communication_docs:
                            for doc in all_docs:
                                document = RazorpayDocument(base_url=f"https://api.razorpay.com/v1/documents/{doc}",
                                                            auth=(f"{key_id}", f"{key_secret}"))
                                document_obj = document.get_document()
                                dispute_document = DisputDocuments(dispute_evidence_id=evidence.id,
                                                                    rzp_created_at=document_obj['created_at'],
                                                                    display_name=document_obj['display_name'],
                                                                    entity=document_obj['entity'],
                                                                    document_id=document_obj['id'],
                                                                    mime_type=document_obj['mime_type'],
                                                                    size=document_obj['size'],
                                                                    url=document_obj['url'])
                                session.add(dispute_document)
                                session.commit()

                        dispute_db = Dispute(
                            dispute_id=dispute["id"],
                            entity=dispute["entity"],
                            gateway_dispute_id=dispute["gateway_dispute_id"],
                            payment_id=dispute["payment_id"],
                            amount=dispute["amount"],
                            currency=dispute["currency"],
                            comments=dispute["comments"],
                            amount_deducted=dispute["amount_deducted"],
                            reason_code=dispute["reason_code"],
                            respond_by=dispute['respond_by'],
                            status=dispute['status'],
                            phase=dispute['phase'],
                            driver_created_at=datetime.datetime.utcfromtimestamp(dispute['created_at']),
                            driver_id=driver_id,
                            dispute_evidence_id=evidence.id if evidence else None,
                        )
                        session.add(dispute_db)
                        session.commit()
                        session.refresh(dispute_db)
                else:
                    exit()
populate()
