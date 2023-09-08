from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.utils import database, search_index


@login_required
def rule(request, rule_id: str):
    yara_rule = database.lookup_yara_rule(rule_id, user=request.user)
    if not yara_rule:
        return redirect("/rules/search/")
    yara_rule = database.parse_lookup_rule_response(yara_rule)

    context = {"rule": yara_rule["yara_rule"]}
    return render(request, "rule_browser/rule.html", context=context)


@login_required
def search(request):
    context = {}
    term = request.GET.get("term", "*")
    if not term:
        term = "*"
    start = int(request.GET.get("start", 0))
    max_results = int(request.GET.get("max_results", 10))
    response = search_index.search_yara_rules_index(
        term, start, max_results, user=request.user
    )
    if response.status_code == 200:
        search_results = search_index.contextualize_yara_rules_search_response(
            response, term=term, start=start, max_results=max_results, user=request.user
        )
    else:
        search_results = {
            "search_time": 0,
            "displayed": 0,
            "available": 0,
            "results": [],
            "search_parameters": {"start": start, "max_results": max_results},
        }
    context["search_results"] = search_results
    return render(request, "rule_browser/search.html", context=context)
