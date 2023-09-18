from django.db import models
from django.contrib.auth.models import User
from apps.rule_import.models import ImportYaraRuleJob
from apps.rule_collections.models import YaraRuleCollection


class YaraRule(models.Model):
    """
    A model to represent a YARA rule.
    """

    id = models.AutoField(primary_key=True)
    rule_id = models.CharField(max_length=32)
    public = models.BooleanField(default=False)
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    import_job = models.ForeignKey(ImportYaraRuleJob, on_delete=models.CASCADE)
    collection = models.ForeignKey(
        YaraRuleCollection, on_delete=models.CASCADE, null=True
    )

    class Meta:
        # A user can only have one rule with a given rule_id
        unique_together = ("rule_id", "collection")

    def __str__(self):
        return self.id
