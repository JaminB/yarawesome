from typing import Optional

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.models import ImportYaraRuleJob, YaraRule


@login_required
def import_rule(request):
    return render(request, "rule_import/import.html")


def my_imports(request):
    user_imports = []
    for rule_import in ImportYaraRuleJob.objects.filter(user=request.user):
        rule_count = YaraRule.objects.filter(import_job=rule_import).count()
        user_imports.append(
            {
                "id": rule_import.id,
                "imported_at": rule_import.created_time,
                "rule_count": rule_count,
            }
        )
    context = {"my_imports": user_imports}
    return render(request, "rule_import/my_imports.html", context=context)
