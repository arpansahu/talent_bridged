from django.db import models

# Create your models here.
from talent_bridged.models import AbstractBaseModel


class Skills(AbstractBaseModel):
    name = models.CharField(max_length=100, null=False)

class Sauce(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Sandwich(models.Model):
    name = models.CharField(max_length=100)
    sauces = models.ManyToManyField(Sauce)

    def __str__(self):
        return self.name