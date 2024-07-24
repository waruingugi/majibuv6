from django.contrib.auth import get_user_model
from django.db import models

from commons.models import Base

User = get_user_model()


class Questions(Base):
    """Questions Model"""

    category = models.CharField(max_length=255, null=False)
    question_text = models.TextField(null=False)

    def __str__(self):
        return self.question_text


class Choices(Base):
    """Choices Model"""

    question = models.ForeignKey(Questions, on_delete=models.CASCADE)
    choice_text = models.TextField(null=False)

    def __str__(self):
        return self.choice_text


class Answers(Base):
    """Answers Model"""

    question = models.OneToOneField(Questions, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choices, on_delete=models.CASCADE)


# class UserAnswers(Base):
#     """UserAnswers Model: Save user answers"""

#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     question = models.ForeignKey(Questions, on_delete=models.CASCADE)
#     choice = models.ForeignKey(Choices, on_delete=models.CASCADE)
#     session = models.ForeignKey("Sessions", on_delete=models.CASCADE)
