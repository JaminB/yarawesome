from typing import Optional

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def import_rule(request):
    return render(request, "rule_import/import.html")


