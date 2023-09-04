from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .api import (make_lookup_rule_request, make_search_request,
                  parse_lookup_rule_response, parse_search_response)


@login_required
def rule(request, rule_id: str):
    yara_rule = parse_lookup_rule_response(make_lookup_rule_request(rule_id))
    context = {
        "rule": yara_rule["yara_rule"]
    }
    return render(request, "rule_browser/rule.html", context=context)


@login_required
def search(request):
    context = {}
    term = request.GET.get("term", "*")
    if not term:
        term = "*"
    start = int(request.GET.get("start", 0))
    max_results = int(request.GET.get("max_results", 10))
    response = make_search_request(term, start, max_results)
    if response.status_code == 200:
        search_results = parse_search_response(response)
    else:
        search_results = {"search_time": 0, "results": []}
    context["search_results"] = search_results
    return render(request, "rule_browser/search.html", context=context)
