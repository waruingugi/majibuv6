import re
import unittest

from django.core.cache import cache

from commons.utils import md5_hash
from users.otp import create_otp, validate_otp


class TestOTP(unittest.TestCase):
    phone_number = "+254703456891"

    def test_create_otp(self):
        """Test successful creation of OTP"""
        create_otp(self.phone_number)
        cached_data = cache.get(md5_hash(self.phone_number))

        self.assertIsNotNone(cached_data)

    def test_validate_otp(self):
        """Test valid OTP is accepted"""
        response = create_otp(self.phone_number)

        pattern = r"\b\d{4}\b"
        match = re.search(pattern, response)
        totp_code = match.group() if match else ""

        valid = validate_otp(totp_code, self.phone_number)

        self.assertTrue(valid)

    def test_invalid_otp_fails(self):
        """Test invalid OTP is rejected"""
        create_otp(self.phone_number)
        valid = validate_otp("1234", self.phone_number)

        self.assertFalse(valid)
