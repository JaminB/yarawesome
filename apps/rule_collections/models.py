from django.db import models
from django.contrib.auth.models import User
from apps.rule_import.models import ImportYaraRuleJob


class YaraRuleCollection(models.Model):
    """
    A model to represent a collection of YARA rules.
    """

    id = models.AutoField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=False)
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


class YaraRuleCollectionDownload(models.Model):
    """
    A model to represent a collection of YARA rules.
    """

    id = models.TextField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    collection = models.ForeignKey(YaraRuleCollection, on_delete=models.CASCADE)
