"""Tuya API client for Eufy Clean device management."""

from __future__ import annotations

import hmac
import json
import logging
import math
import random
import string
import time
import uuid
from hashlib import sha256
from typing import Any
from urllib.parse import urljoin

import aiohttp

from .const import (
    TUYA_API_BASE,
    TUYA_CLIENT_ID,
    TUYA_HMAC_KEY,
    TUYA_SIGNATURE_PARAMS,
)
from .tuya_crypto import get_tuya_password_cipher, shuffled_md5, unpadded_rsa

_LOGGER = logging.getLogger(__name__)


class TuyaAPIClient:
    """Client for Tuya API used by Eufy for device management."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize Tuya API client."""
        self.session = session
        self.base_url = TUYA_API_BASE
        self.session_id: str | None = None
        self.device_id = self._generate_device_id()
        self.username: str | None = None
        self.country_code: str | None = None

    @staticmethod
    def _generate_device_id() -> str:
        """
        Generate a device ID for Tuya API.

        Format: 12 chars (predictable) + 32 chars (random) = 44 chars total
        Using Google Pixel hash for first part to blend in with legitimate devices.
        """
        # From Google Pixel in Android Virtual Device
        device_id_prefix = "8534c8ec0ed0"
        random_suffix = "".join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(44 - len(device_id_prefix))
        )
        return device_id_prefix + random_suffix

    @staticmethod
    def _encode_post_data(data: dict[str, Any] | None) -> str:
        """Encode post data as JSON string."""
        if not data:
            return ""
        return json.dumps(data, separators=(",", ":"))

    @staticmethod
    def _get_signature(query_params: dict[str, str], encoded_post_data: str) -> str:
        """
        Generate Tuya API request signature.

        Uses HMAC-SHA256 with a key derived from app secrets.
        Only specific query parameters are included in the signature.
        """
        params = query_params.copy()

        # Add postData to signature if present
        if encoded_post_data:
            params["postData"] = encoded_post_data

        # Filter and sort parameters
        sorted_pairs = sorted(params.items())
        filtered_pairs = [
            (k, v) for k, v in sorted_pairs if k and k in TUYA_SIGNATURE_PARAMS
        ]

        # Map parameters - postData gets MD5 hashed, others as-is
        mapped_pairs = [
            f"{k}={shuffled_md5(v) if k == 'postData' else v}"
            for k, v in filtered_pairs
        ]

        # Join with || delimiter
        message = "||".join(mapped_pairs)

        # Compute HMAC-SHA256
        signature = hmac.HMAC(
            key=TUYA_HMAC_KEY, msg=message.encode("utf-8"), digestmod=sha256
        ).hexdigest()

        return signature

    def _build_default_query_params(self) -> dict[str, str]:
        """Build default query parameters for Tuya API requests."""
        return {
            "appVersion": "2.4.0",
            "deviceId": self.device_id,
            "platform": "sdk_gphone64_arm64",
            "clientId": TUYA_CLIENT_ID,
            "lang": "en",
            "osSystem": "12",
            "os": "Android",
            "timeZoneId": "Europe/Berlin",
            "ttid": "android",
            "et": "0.0.1",
            "sdkVersion": "3.0.8cAnker",
        }

    async def _request(
        self,
        action: str,
        version: str = "1.0",
        data: dict[str, Any] | None = None,
        query_params: dict[str, str] | None = None,
        requires_session: bool = True,
    ) -> Any:
        """Make a request to Tuya API."""
        # Acquire session if needed
        if requires_session and not self.session_id:
            await self.acquire_session()

        # Build query parameters
        current_time = time.time()
        request_id = uuid.uuid4()

        extra_params = {
            "time": str(int(current_time)),
            "requestId": str(request_id),
            "a": action,
            "v": version,
            **(query_params or {}),
        }

        all_query_params = {**self._build_default_query_params(), **extra_params}

        # Add session ID if available
        if self.session_id:
            all_query_params["sid"] = self.session_id

        # Encode post data
        encoded_post_data = self._encode_post_data(data)

        # Generate signature
        signature = self._get_signature(all_query_params, encoded_post_data)

        # Build URL
        url = urljoin(self.base_url, "/api.json")

        # Build request parameters
        params = {**all_query_params, "sign": signature}

        # Prepare form data (Tuya sends JSON as form-encoded value)
        form_data = {"postData": encoded_post_data} if encoded_post_data else None

        _LOGGER.debug("Tuya API request: action=%s, url=%s", action, url)

        try:
            headers = {"User-Agent": "TY-UA=APP/Android/2.4.0/SDK/null"}

            async with self.session.post(
                url, params=params, data=form_data, headers=headers, timeout=10
            ) as response:
                response.raise_for_status()
                result = await response.json()

                # Check for Tuya API errors
                if not result.get("success", True):
                    error_code = result.get("errorCode", "UNKNOWN")
                    error_msg = result.get("errorMsg", "Unknown error")
                    raise ValueError(f"Tuya API error [{error_code}]: {error_msg}")

                if "result" not in result:
                    raise ValueError(f"No 'result' key in Tuya API response: {result}")

                return result["result"]

        except aiohttp.ClientError as err:
            _LOGGER.error("Tuya API request failed: %s", err)
            raise

    async def request_token(self, username: str, country_code: str) -> dict[str, Any]:
        """Request a token from Tuya API."""
        return await self._request(
            action="tuya.m.user.uid.token.create",
            data={"uid": username, "countryCode": country_code},
            requires_session=False,
        )

    def _determine_password(self, username: str) -> str:
        """
        Determine password for Tuya authentication.

        The password is:
        1. Username padded to multiple of 16
        2. AES-encrypted
        3. Hex-encoded and uppercased
        4. MD5-hashed
        """
        from hashlib import md5

        # Pad username to multiple of 16
        padded_size = 16 * math.ceil(len(username) / 16)
        password_uid = username.zfill(padded_size)

        # Encrypt with AES
        cipher = get_tuya_password_cipher()
        encryptor = cipher.encryptor()
        encrypted_uid = encryptor.update(password_uid.encode("utf-8"))
        encrypted_uid += encryptor.finalize()

        # Hex encode, uppercase, and MD5 hash
        hex_password = encrypted_uid.hex().upper()
        hashed_password = md5(hex_password.encode("utf-8")).hexdigest()

        return hashed_password

    async def acquire_session(self) -> None:
        """Acquire a session from Tuya API."""
        if not self.username or not self.country_code:
            raise ValueError(
                "Username and country_code must be set before acquiring session"
            )

        _LOGGER.debug("Acquiring Tuya session for user: %s", self.username)

        # Request token
        token_response = await self.request_token(self.username, self.country_code)
        token = token_response.get("token")
        public_key = token_response.get("publicKey")
        exponent = token_response.get("exponent")

        if not token or not public_key or not exponent:
            raise ValueError(
                f"Missing token data from Tuya API. Got: {token_response.keys()}"
            )

        # Determine password (MD5-hashed AES-encrypted username)
        password = self._determine_password(self.username)

        # Encrypt password with RSA using public key from token response
        encrypted_password = await asyncio.get_event_loop().run_in_executor(
            None,
            unpadded_rsa,
            int(exponent),
            int(public_key),
            password.encode("utf-8"),
        )

        _LOGGER.debug(
            "Using RSA-encrypted password (length: %d bytes)",
            len(encrypted_password),
        )

        # Login with encrypted password
        login_response = await self._request(
            action="tuya.m.user.uid.password.login.reg",
            data={
                "uid": self.username,
                "createGroup": True,
                "ifencrypt": 1,
                "passwd": encrypted_password.hex(),
                "countryCode": self.country_code,
                "options": '{"group": 1}',
                "token": token,
            },
            requires_session=False,
        )

        self.session_id = login_response.get("sid")

        if not self.session_id:
            raise ValueError("Failed to get session ID from Tuya API")

        _LOGGER.info("Successfully acquired Tuya session")

    async def list_homes(self) -> list[dict[str, Any]]:
        """List all homes (groups) in Tuya."""
        result = await self._request(action="tuya.m.location.list", version="2.1")
        return result or []

    async def list_devices(self, home_id: str) -> list[dict[str, Any]]:
        """List all devices in a Tuya home."""
        # Get own devices
        own_devices = await self._request(
            action="tuya.m.my.group.device.list",
            version="1.0",
            query_params={"gid": home_id},
        )

        # Get shared devices
        shared_devices = await self._request(
            action="tuya.m.my.shared.device.list",
            version="1.0",
        )

        all_devices = (own_devices or []) + (shared_devices or [])
        _LOGGER.debug("Found %d devices in home %s", len(all_devices), home_id)

        return all_devices

    async def get_all_devices(self) -> list[dict[str, Any]]:
        """Get all devices from all homes."""
        homes = await self.list_homes()
        _LOGGER.debug("Found %d homes", len(homes))

        all_devices = []
        for home in homes:
            home_id = home.get("groupId")
            if home_id:
                devices = await self.list_devices(home_id)
                all_devices.extend(devices)

        return all_devices
