"""
URL configuration for yarawesome project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from rule_editor import views as yara_rule_editor_views
from rule_browser import api as rule_browser_api
from rule_browser import views as rule_browser_views
from rule_editor import api as rule_editor_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("django.contrib.auth.urls")),

    path("api/rules/", rule_browser_api.RuleSearchResource.as_view(), name="rule-search"),
    path("api/rules/<str:rule_id>", rule_browser_api.RuleOpenResource.as_view(), name="rule-open"),
    path("api/rules/<str:rule_id>/debug", rule_editor_api.RuleDebugOpenResource.as_view(), name="rule-open-debug"),

    path("editor/", yara_rule_editor_views.editor, name="editor"),
    path("editor/<str:rule_id>", yara_rule_editor_views.editor, name="editor-open"),
    path("rules/search/", rule_browser_views.search, name="search"),
    path("", core_views.index, name="home")
]
