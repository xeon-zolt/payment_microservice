"""Module to add verification dependencies"""
from fastapi import Depends, HTTPException, Request, Header
from loguru import logger
from pydantic import Required
from sqlmodel import Session, select

from payment_app.configs.db import get_session
from payment_app.models.access_client_relation import AccessClientMapper
from payment_app.models.access_points import AccessPoint
from payment_app.models.allowed_ip import AllowedIP
from payment_app.models.client import Client
from payment_app.utils import get_api_key_hash, is_ip_allowed


# read https://fastapi.tiangolo.com/tutorial/header-params/ for headers
async def verify_api_key(
    request: Request,
    session: Session = Depends(get_session),
    x_api_key: str | None = Header(Required),
    x_version: str | None = Header(None),
):
    """Check for api key exist or not and then fetch if app is hitting it from a valid IP"""
    request_headers = {"x_version": x_version}
    api_key_hash = get_api_key_hash(x_api_key)
    statement = select(Client).where(Client.api_key == api_key_hash)
    results = session.exec(statement)
    client = results.first()
    logger.info('few_things')
    if not client:
        logger.error(f"API key not found: {x_api_key}")
        raise HTTPException(
            status_code=403,
            detail={
                "headers": request_headers,
                "error": "Wrong Api Token",
            },
        )

    # check for IP
    statement = select(AllowedIP).where(AllowedIP.client_id == client.id)
    results = session.exec(statement)

    if not results:
        raise HTTPException(
            status_code=403,
            detail={
                "headers": request_headers,
                "error": "No Whitelist IP found",
            },
        )

    host_ip = request.client.host
    logger.info(host_ip)
    if not is_ip_allowed(host_ip, results):
        raise HTTPException(
                status_code=403,
                detail={
                    "headers": request_headers,
                    "error": "Api not allowed outside IP range",
                },
            )
    cur_endpoint = (str(request.url)).split('v1/')[-1].split('/')[0].split('?')[0]

    # check for end point
    statement = select(AccessPoint).where(AccessPoint.endpoint == cur_endpoint)
    endpoint_obj = session.exec(statement).first()
    if endpoint_obj:
        statement = select(AccessClientMapper).where(AccessClientMapper.endpoint_id == endpoint_obj.id).where(AccessClientMapper.client_id == client.id).where(AccessClientMapper.active == True)
        relation = session.exec(statement).first()
        if not relation:
            raise HTTPException(
                status_code=403,
                detail={
                    "headers": request_headers,
                    "error": "Client do not have access to the url. Kindly contact admin.",
                },
            )

    return {
        "client": client,
        "request_headers": request_headers,
        "client_version": x_version,
    }
