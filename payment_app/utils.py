"""Utility functions."""
from datetime import date, datetime
from decimal import Decimal
import hashlib
import io
import ipaddress
import os
import secrets
from loguru import logger

import boto3
import toml
from botocore.exceptions import ClientError
from fastapi import Request

from payment_app.models.dispute import DisputeEvidence


def create_api_key():  # pragma: no cover
    """Create api key."""
    return secrets.token_urlsafe(40)


def get_api_key_hash(api_key):
    """Generate key hash."""
    return hashlib.sha256(str(api_key).encode("utf-8")).hexdigest()


def check_ip_in_range(_ip, ip_range):
    """Check if ip is in range."""
    address = ipaddress.ip_address(_ip)
    network = ipaddress.ip_network(ip_range)
    return network.supernet_of(
        ipaddress.ip_network(f"{address}/{address.max_prefixlen}")
    )


def get_driver_name(driver_id):
    """Get payment driver name."""
    payment_config = toml.load(os.environ.get("PAYMENT_CONFIG_PATH", "config.toml"))
    for gateway in payment_config["gateway"]:
        if driver_id == gateway["id"]:
            return gateway["driver"]


async def parse_body(request: Request):
    """Parse request body."""
    data: bytes = await request.body()
    return data

def is_ip_allowed(host_ip, results) -> bool:
    """Check alowed ips."""
    for allowed_ip in results:
        if check_ip_in_range(host_ip, allowed_ip.ip_range):
            return True
    return False

def update_dispute_evidence(
    dispute_evidence_type: str, 
    dispute_evidence_detail: dict, 
    dispute_evidence: DisputeEvidence,
    data: dict
):
    match dispute_evidence_type:
        case 'shipping_proof':
            if dispute_evidence.shipping_proof:
                dispute_evidence.shipping_proof.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.shipping_proof = [dispute_evidence_detail["id"]]
            data['shipping_proof'] = [proof["id"] for proof in dispute_evidence.shipping_proof]
            return dispute_evidence
        case 'billing_proof':
            if not dispute_evidence.billing_proof:
                dispute_evidence.billing_proof.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.billing_proof = [dispute_evidence_detail["id"]]
            data['billing_proof'] = [proof["id"] for proof in dispute_evidence.billing_proof]
            return dispute_evidence
        case 'cancellation_proof':
            if dispute_evidence.cancellation_proof:
                dispute_evidence.cancellation_proof.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.cancellation_proof = [dispute_evidence_detail["id"]]
            data['cancellation_proof'] = [proof["id"] for proof in dispute_evidence.cancellation_proof]
            return dispute_evidence
        case 'customer_communication':
            if dispute_evidence.customer_communication:
                dispute_evidence.customer_communication.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.customer_communication = [dispute_evidence_detail["id"]]
            data['customer_communication'] = [proof["id"] for proof in dispute_evidence.customer_communication]
            return dispute_evidence
        case 'proof_of_service':
            if dispute_evidence.proof_of_service:
                dispute_evidence.proof_of_service.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.proof_of_service = [dispute_evidence_detail["id"]]
            data['proof_of_service'] = [proof["id"] for proof in dispute_evidence.proof_of_service]
            return dispute_evidence
        case 'explanation_letter':
            if dispute_evidence.explanation_letter:
                dispute_evidence.explanation_letter.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.explanation_letter = [dispute_evidence_detail["id"]]
            data['explanation_letter'] = [proof["id"] for proof in dispute_evidence.explanation_letter]
            return dispute_evidence
        case 'refund_confirmation':
            if dispute_evidence.refund_confirmation:
                dispute_evidence.refund_confirmation.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.refund_confirmation = [dispute_evidence_detail["id"]]
            data['refund_confirmation'] = [proof["id"] for proof in dispute_evidence.refund_confirmation]
            return dispute_evidence
        case 'access_activity_log':
            if dispute_evidence.access_activity_log:
                dispute_evidence.access_activity_log.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.access_activity_log = [dispute_evidence_detail["id"]]
            data['access_activity_log'] = [proof["id"] for proof in dispute_evidence.access_activity_log]
            return dispute_evidence
        case 'refund_cancellation_policy':
            if dispute_evidence.refund_cancellation_policy:
                dispute_evidence.refund_cancellation_policy.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.refund_cancellation_policy = [dispute_evidence_detail["id"]]
            data['refund_cancellation_policy'] = [proof["id"] for proof in dispute_evidence.refund_cancellation_policy]
            return dispute_evidence
        case 'term_and_conditions':
            if dispute_evidence.term_and_conditions:
                dispute_evidence.term_and_conditions.append(dispute_evidence_detail["id"])
            else:
                dispute_evidence.term_and_conditions = [dispute_evidence_detail["id"]]
            data['term_and_conditions'] = [proof["id"] for proof in dispute_evidence.term_and_conditions]
            return dispute_evidence
        case default:
            if dispute_evidence.others:
                dispute_evidence.others = [{
                        "type": dispute_evidence_type,
                        "evidence_details": [dispute_evidence_detail["id"]]
                    }]
            else:
                dispute_evidence.others = handle_custom_evidence_type(
                    dispute_evidence_type, dispute_evidence_detail, dispute_evidence.others
                )
            data['others'] = [proof for proof in dispute_evidence.billing_proof]
            return dispute_evidence

def handle_custom_evidence_type(dispute_evidence_type, dispute_evidence_detail, custom_dispute_evidence_details):
    for index in range(len(custom_dispute_evidence_details)):
        if custom_dispute_evidence_details[index]["type"] == dispute_evidence_type:
            custom_dispute_evidence_details[index]["document_ids"].append(dispute_evidence_detail["id"])
            return custom_dispute_evidence_details
    custom_dispute_evidence_details.append({"type": dispute_evidence_type, "document_ids": [dispute_evidence_detail["id"]]})
    return custom_dispute_evidence_details

def upload_file_to_s3(file, filename: str):
    try:
        bucket = os.environ["S3_BUCKET"]
        file.seek(0)
        s3 = boto3.resource("s3")
        s3.meta.client.upload_fileobj(file, bucket, f"{filename}")
    except ClientError as e:
        logger.debug(f"error while uploading to s3 ==> {e}")
        return False
    return True

def custom_json_serializer(value):
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, (date, datetime)):
        return value.isoformat()
    
    raise TypeError(f"Value {value!r} not serializable")
