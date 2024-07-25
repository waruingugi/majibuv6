from datetime import datetime

from django.contrib.auth import get_user_model

from commons.constants import SessionCategories
from commons.tests.base_tests import BaseUserAPITestCase
from quiz.models import Result
from user_sessions.models import Session
from user_sessions.utils import query_available_active_sessions

User = get_user_model()


class QueryAvailableActiveSessionsTests(BaseUserAPITestCase):
    def setUp(self):
        # Create test users
        self.user = self.create_user()
        self.foreign_user = User.objects.create_user(
            phone_number="+254713476781", password="password456", username="testuser2"
        )
        self.bible_category = SessionCategories.BIBLE.value
        self.football_category = SessionCategories.FOOTBALL.value

        # Create test sessions
        self.session1 = Session.objects.create(
            category=self.bible_category, _questions="Q1,Q2"
        )
        self.session2 = Session.objects.create(
            category=self.bible_category, _questions="Q3,Q4"
        )
        self.session3 = Session.objects.create(
            category=self.football_category, _questions="Q5,Q6"
        )
        self.session4 = Session.objects.create(
            category=self.bible_category, _questions="Q7,Q8"
        )

        # Create test results
        Result.objects.create(
            user=self.user,
            session=self.session1,
            is_active=True,
            expires_at=datetime.now(),
        )
        Result.objects.create(
            user=self.user,
            session=self.session3,
            is_active=True,
            expires_at=datetime.now(),
        )
        Result.objects.create(
            user=self.foreign_user,
            session=self.session2,
            is_active=True,
            expires_at=datetime.now(),
        )

    def test_user_has_available_active_sessions(self):
        """Assert only 1 active session in BIBLE category available for user"""
        available_sessions = query_available_active_sessions(
            user=self.user, category=self.bible_category
        )
        expected_sessions = [
            self.session2.id
        ]  # Sessions not played by user in BIBLE category
        self.assertListEqual(available_sessions, expected_sessions)

    def test_foreign_user_has_available_active_sessions(self):
        """Assert only 1 active session in BIBLE category available for foreing user"""
        available_sessions = query_available_active_sessions(
            user=self.foreign_user, category=self.bible_category
        )
        expected_sessions = [
            self.session1.id
        ]  # Sessions not played by foreign user in BIBLE category
        self.assertListEqual(available_sessions, expected_sessions)

    def test_user_has_no_available_active_sessions(self):
        """Assert user has no active session to play"""
        Result.objects.filter(user=self.foreign_user).update(is_active=False)
        available_sessions = query_available_active_sessions(
            user=self.user, category=self.bible_category
        )
        self.assertListEqual(available_sessions, [])

    def test_foreign_user_has_no_available_active_sessions(self):
        """Assert user has no active session to play in a different category"""
        Result.objects.filter(user=self.user).update(
            session=self.session1
        )  # Update all other sessions to BIBLE category
        available_sessions = query_available_active_sessions(
            user=self.foreign_user, category=self.football_category
        )
        self.assertListEqual(available_sessions, [])
