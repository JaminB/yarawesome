from django.db import models
from django.contrib.auth.models import User


class YaraRule(models.Model):

    id = models.CharField(primary_key=True, max_length=32)
    rule = models.TextField()

    def __str__(self):
        return self.id