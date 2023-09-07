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
    """
    A model to represent a collection of YARA rules.
    """

    id = models.AutoField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=32)
    icon = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    import_job = models.ForeignKey(ImportYaraRuleJob, on_delete=models.CASCADE)

    def get_rule_count(self):
        """
        Returns the count of YaraRule objects associated with this collection.
        """
        return self.yararule_set.count()

    def __str__(self):
        return self.name


class YaraRule(models.Model):
    """
    A model to represent a YARA rule.
    """

    id = models.AutoField(primary_key=True)
    rule_id = models.CharField(max_length=32)
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    import_job = models.ForeignKey(ImportYaraRuleJob, on_delete=models.CASCADE)
    collection = models.ForeignKey(
        YaraRuleCollection, on_delete=models.CASCADE, null=True
    )

    class Meta:
        # A user can only have one rule with a given rule_id
        unique_together = ("rule_id", "user")

    def __str__(self):
        return self.id
