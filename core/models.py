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


class YaraRuleCollection(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=32)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    import_job = models.ForeignKey(ImportYaraRuleJob, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class YaraRule(models.Model):
    """
    A model to represent a YARA rule.
    """

    id = models.AutoField(primary_key=True)
    yara_id = models.CharField(max_length=32)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    import_job = models.ForeignKey(ImportYaraRuleJob, on_delete=models.CASCADE)
    collection = models.ForeignKey(
        YaraRuleCollection, on_delete=models.CASCADE, null=True
    )

    class Meta:
        unique_together = ("yara_id", "import_job")

    def __str__(self):
        return self.id
