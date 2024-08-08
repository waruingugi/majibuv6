from datetime import datetime
from decimal import Decimal

from commons.tests.base_tests import BaseQuizTestCase
from quiz.models import Answer, Choice, Question, UserAnswer


class QuestionModelTest(BaseQuizTestCase):
    def test_question_creation(self):
        """Test if a question is created correctly."""
        self.assertEqual(self.question.category, self.category)
        self.assertEqual(self.question.question_text, self.question_text)

    def test_string_representation(self):
        """Test the string representation of the question."""
        self.assertEqual(str(self.question), self.question_text)


class ChoiceModelTest(BaseQuizTestCase):
    def test_choice_creation(self):
        """Test if a choice is created correctly."""
        self.assertEqual(self.choice.question, self.question)
        self.assertEqual(self.choice.choice_text, self.choice_text)

    def test_string_representation(self):
        """Test the string representation of the choice."""
        self.assertEqual(str(self.choice), self.choice_text)

    def test_choice_belongs_to_question(self):
        """Test that the choice belongs to the correct question."""
        self.assertEqual(self.choice.question.question_text, self.question_text)


class AnswerModelTest(BaseQuizTestCase):
    def test_answer_creation(self):
        """Test if an answer is created correctly."""
        self.assertEqual(self.answer.question, self.question)
        self.assertEqual(self.answer.choice, self.choice)

    def test_answer_belongs_to_correct_question(self):
        """Test that the answer belongs to the correct question."""
        self.assertEqual(self.answer.question.question_text, self.question_text)

    def test_answer_belongs_to_correct_choice(self):
        """Test that the answer belongs to the correct choice."""
        self.assertEqual(self.answer.choice.choice_text, self.choice_text)

    def test_question_and_choice_relationship(self):
        """Test the relationship between question and choice in an answer."""
        self.assertEqual(self.answer.choice.question, self.question)

    def test_unique_question_answer(self):
        """Test that the same question cannot have more than one answer."""
        with self.assertRaises(Exception):
            Answer.objects.create(question=self.question, choice=self.choice)


class UserAnswerModelTest(BaseQuizTestCase):
    def test_user_answer_creation(self):
        """Test if a UserAnswer is created correctly."""
        self.assertEqual(self.user_answer.user, self.user)
        self.assertEqual(self.user_answer.question, self.question)
        self.assertEqual(self.user_answer.choice, self.choice)
        self.assertEqual(self.user_answer.session, self.session)

    def test_user_answer_relationships(self):
        """Test the relationships between UserAnswer and other models."""
        self.assertEqual(self.user_answer.question.question_text, self.question_text)
        self.assertEqual(self.user_answer.choice.choice_text, self.choice_text)
        self.assertEqual(self.user_answer.session.category, self.category)

    def test_user_can_answer_different_questions_in_same_session(self):
        """Test that a user can answer different questions in the same session."""
        new_question = Question.objects.create(
            category="Math", question_text="What is 2 + 2?"
        )
        new_choice = Choice.objects.create(question=new_question, choice_text="4")
        user_answer = UserAnswer.objects.create(
            user=self.user,
            question=new_question,
            choice=new_choice,
            session=self.session,
        )
        self.assertEqual(user_answer.user, self.user)
        self.assertEqual(user_answer.question, new_question)
        self.assertEqual(user_answer.choice, new_choice)
        self.assertEqual(user_answer.session, self.session)


class ResultsModelTest(BaseQuizTestCase):
    def test_result_creation(self):
        """Test if a Results instance is created correctly."""
        self.assertEqual(self.result.user, self.user)
        self.assertEqual(self.result.session, self.session)
        self.assertEqual(self.result.total_answered, 0)
        self.assertEqual(self.result.total_correct, 0)
        self.assertEqual(self.result.total, Decimal(0.0))
        self.assertEqual(self.result.score, Decimal(0.0))
        self.assertTrue(self.result.is_active)

    def test_result_expires_at(self):
        """Test if the expires_at field is set correctly."""
        self.assertTrue(self.result.expires_at < datetime.now())

    def test_result_belongs_to_correct_user_and_session(self):
        """Test the relationships between Results and other models."""
        self.assertEqual(self.result.user.username, self.user.username)
        self.assertEqual(self.result.session.category, self.category)

    def test_result_is_active(self):
        """Test the is_active field."""
        self.assertTrue(self.result.is_active)
