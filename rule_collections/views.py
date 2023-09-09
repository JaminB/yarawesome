from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q

from core.models import YaraRuleCollection


@login_required
def collection(request, collection_id):
    """
    View a YaraRuleCollection. If the collection is not public, the user must be the owner of the collection.
    Args:
        request: The HTTP request.
        collection_id: The ID of the collection to view.

    Returns:
        A view of the YaraRuleCollection. Will attempt to find the collection in the user's collections first,
        and then the public collections if the user collection is not found.
    """
    _collection = YaraRuleCollection.objects.filter(
        id=collection_id, user=request.user
    ).first()
    if not _collection:
        _collection = YaraRuleCollection.objects.filter(
            id=collection_id, public=True
        ).first()
    if not _collection:
        return redirect("/collections/")
    if _collection.user == request.user:
        _collection.is_owner = True
    else:
        _collection.is_owner = False
    return render(
        request, "rule_collections/collection.html", {"collection": _collection}
    )


@login_required
def my_collections(request):
    """
    Search all YaraRuleCollections owned by the user.
    Args:
        request: The HTTP request.

    Returns:
        A view of all YaraRuleCollections owned by the user.
    """
    start = int(request.GET.get("start", 0))
    max_results = int(request.GET.get("max_results", 10))
    term = request.GET.get("term", "")

    if term:
        collections = YaraRuleCollection.objects.filter(
            Q(name__icontains=term) | Q(description__icontains=term), user=request.user
        )
    else:
        collections = YaraRuleCollection.objects.filter(user=request.user)
    start_page = int(start / max_results) + 1
    paginated_collection = []
    for _collection in Paginator(collections, per_page=max_results).page(start_page):
        if _collection.user == request.user:
            _collection.is_owner = True
        else:
            _collection.is_owner = False
        paginated_collection.append(_collection)
    return render(
        request,
        "rule_collections/my_collections.html",
        {
            "collections": paginated_collection,
            "search_parameters": {
                "term": term,
                "max_results": max_results,
                "start": start,
            },
            "displayed": len(paginated_collection),
            "available": collections.count(),
            "has_previous_page": start > 0,
            "has_next_page": collections.count() > start + max_results,
        },
    )


@login_required
def shared_collections(request):
    """
    Search all YaraRuleCollections that are public.
    Args:
        request: The HTTP request.

    Returns:
        A view of all YaraRuleCollections that are public.

    """
    start = int(request.GET.get("start", 0))
    max_results = int(request.GET.get("max_results", 10))
    term = request.GET.get("term", "")
    if term:
        collections = YaraRuleCollection.objects.filter(
            Q(name__icontains=term) | Q(description__icontains=term),
            public=True,
        )
    else:
        collections = YaraRuleCollection.objects.filter(public=True)

    start_page = int(start / max_results) + 1

    paginated_collection = []
    for _collection in Paginator(collections, per_page=max_results).page(start_page):
        if _collection.user == request.user:
            _collection.is_owner = True
        else:
            _collection.is_owner = False
        paginated_collection.append(_collection)
    return render(
        request,
        "rule_collections/shared_collections.html",
        {
            "collections": paginated_collection,
            "search_parameters": {
                "term": term,
                "max_results": max_results,
                "start": start,
            },
            "displayed": len(paginated_collection),
            "available": collections.count(),
            "has_previous_page": start > 0,
            "has_next_page": collections.count() > start + max_results,
        },
    )
