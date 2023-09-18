from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def upload_test_binary(request):
    return render(request, "rule_lab/upload.html")
