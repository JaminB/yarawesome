from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def editor(request, **kwargs):
    yara_rule = None
    context = {"yara_rule": yara_rule}
    return render(request, "rule_editor/editor.html", context=context)
