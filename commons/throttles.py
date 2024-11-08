from rest_framework.throttling import SimpleRateThrottle


class AuthenticationThrottle(SimpleRateThrottle):
    scope = "authentication_throttle"

    def get_cache_key(self, request, view):
        return self.get_ident(request)


class MpesaSTKPushThrottle(SimpleRateThrottle):
    scope = "mpesa_stkpush_throttle"

    def get_cache_key(self, request, view):
        return self.get_ident(request)


class MpesaWithdrawalThrottle(SimpleRateThrottle):
    scope = "mpesa_withdrawal_throttle"

    def get_cache_key(self, request, view):
        return self.get_ident(request)
