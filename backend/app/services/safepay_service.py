"""
SafePay Service
===============
Direct REST integration with SafePay API (bypasses broken safepay-python
asyncio issue on Python 3.10+).

SafePay payment flow:
  1. POST /order/v1/init  →  get beacon token
  2. Build checkout URL with beacon token  →  redirect user
  3. User pays  →  SafePay redirects back with ?tracker=<token>&sig=<hmac>
  4. Verify HMAC: hmac_sha256(secret, tracker) == sig  →  activate subscription
  5. Webhook (optional backup): POST /payments/webhook with x-sfpy-signature header
"""
import hmac
import uuid
import logging
import urllib.parse
from hashlib import sha256, sha512
from typing import Optional, Dict, Any

import requests as http

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── SafePay API base URLs ─────────────────────────────────────────────────────
_API_URLS = {
    "production":  "https://api.getsafepay.com",
    "sandbox":     "https://sandbox.api.getsafepay.com",
    "development": "https://dev.api.getsafepay.com",
}
_CHECKOUT_URLS = {
    "production":  "https://getsafepay.com/checkout/pay",
    "sandbox":     "https://sandbox.api.getsafepay.com/checkout/pay",
    "development": "https://dev.api.getsafepay.com/checkout/pay",
}

PKR_RATE = 278  # 1 USD ≈ 278 PKR — update as needed


def _api_url() -> str:
    return _API_URLS.get(settings.SAFEPAY_ENVIRONMENT, _API_URLS["sandbox"])


def _checkout_base() -> str:
    return _CHECKOUT_URLS.get(settings.SAFEPAY_ENVIRONMENT, _CHECKOUT_URLS["sandbox"])


def usd_to_pkr_paisas(usd: float) -> int:
    """Convert USD to PKR in smallest unit (paisas = PKR * 100)."""
    return int(round(usd * PKR_RATE * 100))


class SafePayService:
    """Direct SafePay REST API integration."""

    @staticmethod
    def create_payment_token(amount_paisas: int, currency: str = "PKR") -> Optional[str]:
        """
        Step 1 — Reserve a payment token (beacon).

        POST /order/v1/init
        Returns the beacon token string, or None on error.
        """
        url = f"{_api_url()}/order/v1/init"
        payload = {
            "amount":      amount_paisas,
            "client":      settings.SAFEPAY_API_KEY,
            "currency":    currency,
            "environment": settings.SAFEPAY_ENVIRONMENT,
        }
        try:
            resp = http.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            # SafePay returns {"data": {"token": "..."}} or {"token": "..."}
            token = (
                data.get("data", {}).get("token")
                or data.get("token")
            )
            if not token:
                logger.error(f"SafePay: no token in response: {data}")
                return None
            return token
        except Exception as e:
            logger.error(f"SafePay: create_payment_token failed: {e}", exc_info=True)
            return None

    @staticmethod
    def build_checkout_url(
        token: str,
        order_id: str,
        redirect_url: str,
        cancel_url: str,
        source: str = "custom",
        webhooks: bool = True,
    ) -> str:
        """
        Step 2 — Build hosted checkout URL.
        Redirect user to this URL to complete payment.
        """
        params = urllib.parse.urlencode({
            "beacon":       token,
            "cancel_url":   cancel_url,
            "env":          settings.SAFEPAY_ENVIRONMENT,
            "order_id":     order_id,
            "redirect_url": redirect_url,
            "source":       source,
            "webhooks":     "true" if webhooks else "false",
        })
        return f"{_checkout_base()}?{params}"

    @staticmethod
    def create_checkout_session(
        usd_price: float,
        plan_id: str,
        user_id: str,
        order_id: str,
        success_url: str,
        cancel_url: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Full checkout session creation:
          1. Get beacon token from SafePay
          2. Build checkout URL

        Returns dict with checkout_url and tracker, or None on error.
        """
        amount_paisas = usd_to_pkr_paisas(usd_price)

        token = SafePayService.create_payment_token(amount_paisas)
        if not token:
            return None

        checkout_url = SafePayService.build_checkout_url(
            token=token,
            order_id=order_id,
            redirect_url=success_url,
            cancel_url=cancel_url,
        )

        logger.info(
            f"SafePay checkout: order={order_id}, user={user_id}, "
            f"plan={plan_id}, token={token}, amount={amount_paisas} paisas"
        )
        return {
            "checkout_url": checkout_url,
            "tracker":      token,
            "session_id":   token,
        }

    @staticmethod
    def verify_payment(sig: str, tracker: str) -> bool:
        """
        Step 4 — Verify HMAC signature after SafePay redirect.

        SafePay appends ?tracker=<token>&sig=<hmac_sha256(secret, tracker)>

        Returns True if payment is genuine.
        """
        try:
            secret = settings.SAFEPAY_API_KEY.encode("utf-8")
            mac = hmac.new(secret, msg=tracker.encode("utf-8"), digestmod=sha256)
            computed = mac.hexdigest()
            valid = hmac.compare_digest(computed, sig)
            logger.info(f"SafePay verify: tracker={tracker}, valid={valid}")
            return valid
        except Exception as e:
            logger.error(f"SafePay verify_payment error: {e}", exc_info=True)
            return False

    @staticmethod
    def verify_webhook(headers: Dict[str, str], data: Any) -> bool:
        """
        Verify SafePay webhook signature (x-sfpy-signature header).

        HMAC-SHA512(webhookSecret, JSON(data))
        """
        try:
            import json as _json
            sig = headers.get("x-sfpy-signature") or headers.get("X-Sfpy-Signature", "")
            if not sig:
                return False
            secret = settings.SAFEPAY_WEBHOOK_SECRET.encode("utf-8")
            payload = _json.dumps(data, separators=(",", ":")).encode("utf-8")
            mac = hmac.new(secret, msg=payload, digestmod=sha512)
            computed = mac.hexdigest()
            return hmac.compare_digest(computed, sig)
        except Exception as e:
            logger.error(f"SafePay verify_webhook error: {e}", exc_info=True)
            return False

    @staticmethod
    def build_order_id(user_id: str, plan_id: str) -> str:
        """Build unique order ID encoding user + plan for lookup on redirect."""
        rand = uuid.uuid4().hex[:8]
        return f"{user_id}__{plan_id}__{rand}"

    @staticmethod
    def parse_order_id(order_id: str):
        """Parse order_id back to (user_id, plan_id). Returns (None, None) if invalid."""
        parts = order_id.split("__")
        if len(parts) >= 2:
            return parts[0], parts[1]
        return None, None


safepay_service = SafePayService()
