from django.db import models
from django.contrib.auth.models import User


class ImportJob(models.Model):
    id = models.AutoField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportJob {self.id} by {self.user.name}"
