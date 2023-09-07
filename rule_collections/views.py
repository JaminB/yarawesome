from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from core.models import YaraRuleCollection


@login_required
def my_collections(request):

    collections = YaraRuleCollection.objects.filter(user=request.user)
    return render(
        request, "rule_collections/my_collections.html", {"collections": collections}
    )
