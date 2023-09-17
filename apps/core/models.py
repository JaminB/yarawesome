import re
from django.contrib.auth.models import User
from django.db import models


def user_binaries_directory_path(instance, filename):
    # Upload files to a subdirectory of 'test_binaries' with the user's ID
    alphanumeric_filename = re.sub(r"[^a-zA-Z0-9.]", "_", filename).lower()
    return f"test_binaries/{instance.user.id}/{alphanumeric_filename}"


class ImportYaraRuleJob(models.Model):
    """
    A model to represent an import job for YARA rules.
    """

    id = models.AutoField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"ImportYaraRuleJob {self.id} by {self.user.name}"


class TestBinary(models.Model):
    """
    A model to represent a test binary.
    """

    id = models.AutoField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_binaries_directory_path)

    def __str__(self):
        return f"TestBinary {self.id} by {self.user.name}"


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
