from rest_framework.throttling import SimpleRateThrottle


class RegisterThrottle(SimpleRateThrottle):
    scope = "register_throttle"

    def get_cache_key(self, request, view):
        return self.get_ident(request)
