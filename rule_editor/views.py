from typing import Optional
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def editor(request, rule_id: Optional[str] = None):
    yara_rule = None
    context = {"yara_rule": yara_rule}
    return render(request, "rule_editor/editor.html", context=context)


