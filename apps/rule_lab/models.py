import re
import hashlib
from django.db import models
from django.contrib.auth.models import User
from apps.rules.models import YaraRule


def user_binaries_directory_path(instance, filename):
    """
    Return the path to a user's test binary.
    """
    partial_hash = hashlib.md5(instance.file.read(4096)).hexdigest()
    return f"test_binaries/{instance.user.id}/{partial_hash}"


class TestBinary(models.Model):
    """
    A model to represent a test binary.
    """

    id = models.AutoField(primary_key=True)
    binary_id = models.CharField(
        max_length=32, unique=True, blank=True, null=True, editable=False
    )
    name = models.CharField(max_length=255)
    created_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_binaries_directory_path)

    def __str__(self):
        return f"TestBinary {self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Calculate MD5 hash of the file's contents
        if not self.binary_id:
            md5_hash = hashlib.md5()
            for chunk in self.file.chunks():
                md5_hash.update(chunk)
            self.binary_id = md5_hash.hexdigest()

        super(TestBinary, self).save(*args, **kwargs)


class YaraRuleMatch(models.Model):
    """
    A model to represent a YARA rule match.
    """

    id = models.AutoField(primary_key=True)
    created_time = models.DateTimeField(auto_now_add=True)
    rule = models.ForeignKey(YaraRule, on_delete=models.CASCADE)
    test_binary = models.ForeignKey(TestBinary, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"YaraRuleMatch {self.id} for {self.rule.rule_id}"
