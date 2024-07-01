from rest_framework.permissions import BasePermission

from accounts.constants import MPESA_WHITE_LISTED_IPS


class IsMpesaWhiteListedIP(BasePermission):
    """
    Custom permission to only allow access to specific M-Pesa IP addresses.
    """

    allowed_ips = MPESA_WHITE_LISTED_IPS

    def has_permission(self, request, view):
        ip_addr = request.META.get("REMOTE_ADDR")
        return ip_addr in self.allowed_ips
