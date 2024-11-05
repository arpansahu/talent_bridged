from django.utils import timezone

from django.db import models

# Create your models here.
from talent_bridged.models import AbstractBaseModel


class EmailsOtpRecord(AbstractBaseModel):
    class Meta:
        unique_together = ('email', 'date')

    email = models.EmailField()
    date = models.DateField(default=timezone.now)
    count = models.IntegerField(default=1)

class ContactSubmission(AbstractBaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    contact = models.CharField(max_length=15, blank=True, null=True)  # Adjust max_length as needed
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

        