#!/usr/bin/env python3
"""Kubioscloud example for Authorization"""
import logging
import os
import uuid
from typing import Dict
from urllib.parse import parse_qs, urlparse

import requests

USERNAME = "abo.ehea.m.z@hotmail.com"
PASSWORD = "Zeko00963"
CLIENT_ID = "74571pdhuc7vvak4tl45uts8u8"

LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"

USER_AGENT = "TestApp 1.0"  # FIXME: Use unique name for your application


class AuthenticationError(BaseException):
    """Authentication Error"""


def user_login(
    username: str, password: str, client_id: str, redirect_uri: str = REDIRECT_URI
) -> Dict[str, str]:
    """Get authentication tokens using username & password.

    :param: username: KubiosCloud username
    :param: password: Password

    :return: dict with authentication and refresh tokens
    """
    log = logging.getLogger(__name__)
    csrf = str(uuid.uuid4())

    # Authentication
    session = requests.session()
    log.info("Authenticating to %r with client_id: %r", LOGIN_URL, client_id)
    login_data = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "username": username,
        "password": password,
        "response_type": "token",
        "scope": "openid",
        "_csrf": csrf,
    }
    login_response = session.post(
        LOGIN_URL,
        data=login_data,
        allow_redirects=False,
        headers={"Cookie": f"XSRF-TOKEN={csrf}", "User-Agent": USER_AGENT},
    )
    # Verify results
    login_response.raise_for_status()
    location_url = login_response.headers["Location"]
    if location_url == LOGIN_URL:
        raise AuthenticationError(
            f"Status: {login_response.status_code}, Authentication failed."
        )
    parsed = urlparse(location_url)
    parameters = parse_qs(parsed.fragment)
    tokens = {
        "id_token": parameters["id_token"][0],
        "access_token": parameters["access_token"][0],
    }

    return tokens


def main():
    log = logging.getLogger(__name__)

    tokens = user_login(USERNAME, PASSWORD, CLIENT_ID)

    log.info("Query for user details to test obtained credentials")
    session = requests.session()
    response = session.get(
        "https://analysis.kubioscloud.com/v1/user/self",
        headers={"Authorization": tokens["id_token"], "User-Agent": USER_AGENT},
    )
    print(response.json())


if __name__ == "__main__":
    main()