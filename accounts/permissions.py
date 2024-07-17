from rest_framework.permissions import BasePermission

from accounts.constants import MPESA_WHITE_LISTED_IPS
from commons.raw_logger import logger


class IsMpesaWhiteListedIP(BasePermission):
    """
    Custom permission to only allow access to specific M-Pesa IP addresses.
    """

    allowed_ips = MPESA_WHITE_LISTED_IPS

    def has_permission(self, request, view):
        # We're running of Fly.io so to get the ip, first check using it's default fly-client-ip
        # then fall back to remote-addr
        ip_addr = request.META.get("HTTP_FLY_CLIENT_IP") or request.META.get(
            "REMOTE_ADDR"
        )
        logger.info(
            f"Asserting IP: {ip_addr} is in M-Pesa white-listed IP addresses..."
        )
        return ip_addr in self.allowed_ips
