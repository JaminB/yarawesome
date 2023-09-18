from django.contrib.auth.models import User
from django.db import models


class ImportYaraRuleJob(models.Model):
    """
    A model to represent an import job for YARA rules.
    """

    id = models.AutoField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportYaraRuleJob {self.id} by {self.user.name}"
