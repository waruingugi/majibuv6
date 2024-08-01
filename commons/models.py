import uuid

from django.db import models


class Base(models.Model):
    """
    All other models inherit from Base.
    Base contains common fields among the models.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)
