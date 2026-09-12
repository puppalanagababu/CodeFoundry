import logging
from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger("users.auth")


class LoginRateThrottle(SimpleRateThrottle):
    """
    Rate-limits login attempts per IP and username to protect against brute-force attacks.
    Configured via settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['login'] (e.g. '5/15m').
    """
    scope = "login"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        username = ""
        if hasattr(request, "data") and isinstance(request.data, dict):
            username = request.data.get("username", "")

        if username:
            clean_user = str(username).replace("\r", "").replace("\n", "").replace("\t", "").strip().lower()[:150]
            ident = f"{ident}_{clean_user}"

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }

    def parse_rate(self, rate):
        """
        Parses rate strings like '5/15m', '5/minute', '10/h', '100/d'.
        """
        if rate is None:
            return (None, None)
        try:
            num, period = rate.split("/")
            num_requests = int(num)
            if period.endswith("m") and len(period) > 1:
                duration = int(period[:-1]) * 60
            elif period.endswith("s") and len(period) > 1:
                duration = int(period[:-1])
            elif period.endswith("h") and len(period) > 1:
                duration = int(period[:-1]) * 3600
            elif period.endswith("d") and len(period) > 1:
                duration = int(period[:-1]) * 86400
            else:
                duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period[0]]
            return (num_requests, duration)
        except Exception:
            return (5, 900)

    def allow_request(self, request, view):
        try:
            allowed = super().allow_request(request, view)
            if not allowed:
                ident = self.get_cache_key(request, view)
                logger.warning("Login rate limit exceeded for ident: %s", ident)
            return allowed
        except Exception as exc:
            logger.warning("Cache backend error during login throttling: %s", exc)
            return True


class PasswordResetRateThrottle(SimpleRateThrottle):
    """
    Rate-limits password-reset requests per IP (and normalized email if provided)
    to prevent spamming and abuse.
    Configured via settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['password_reset'] (e.g. '5/15m').
    """
    scope = "password_reset"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        email = ""
        if hasattr(request, "data") and isinstance(request.data, dict):
            email = request.data.get("email", "")

        if email:
            clean_email = str(email).replace("\r", "").replace("\n", "").replace("\t", "").strip().lower()[:150]
            ident = f"{ident}_{clean_email}"

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        try:
            num, period = rate.split("/")
            num_requests = int(num)
            if period.endswith("m") and len(period) > 1:
                duration = int(period[:-1]) * 60
            elif period.endswith("s") and len(period) > 1:
                duration = int(period[:-1])
            elif period.endswith("h") and len(period) > 1:
                duration = int(period[:-1]) * 3600
            elif period.endswith("d") and len(period) > 1:
                duration = int(period[:-1]) * 86400
            else:
                duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period[0]]
            return (num_requests, duration)
        except Exception:
            return (5, 900)

    def allow_request(self, request, view):
        try:
            allowed = super().allow_request(request, view)
            if not allowed:
                ident = self.get_cache_key(request, view)
                logger.warning("Password reset rate limit exceeded for ident: %s", ident)
            return allowed
        except Exception as exc:
            logger.warning("Cache backend error during password reset throttling: %s", exc)
            return True
