from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def editor(request):
    return render(request, "yara_rule_editor/editor.html")
