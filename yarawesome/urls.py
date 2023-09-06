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
from django.urls import include, path

from core import views as core_views
from rule_browser import api as rule_browser_api
from rule_browser import views as rule_browser_views
from rule_editor import api as rule_editor_api
from rule_editor import views as rule_editor_views
from rule_import import api as rule_import_api
from rule_import import views as rule_import_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("django.contrib.auth.urls")),
    path(
        "api/rules/import/",
        rule_import_api.CreateImportJobResource.as_view(),
        name="create-import-job",
    ),
    path(
        "api/rules/import/<str:import_id>",
        rule_import_api.ImportJobResource.as_view(),
        name="view-import-job",
    ),
    path(
        "api/rules/", rule_browser_api.RuleSearchResource.as_view(), name="rule-search"
    ),
    path(
        "api/rules/<str:rule_id>",
        rule_browser_api.RuleOpenResource.as_view(),
        name="rule-view",
    ),
    path(
        "api/rules/<str:rule_id>/editor",
        rule_editor_api.RuleEditorResource.as_view(),
        name="rule-editor",
    ),
    path("editor/", rule_editor_views.editor, name="editor"),
    path("import/", rule_import_views.import_rule, name="import"),
    path("rules/<str:rule_id>/editor", rule_editor_views.editor, name="editor-open"),
    path("rules/search/", rule_browser_views.search, name="search"),
    path("rules/<str:rule_id>", rule_browser_views.rule, name="rule"),
    path("my_imports/", rule_import_views.my_imports, name="my-imports"),
    path("", core_views.index, name="home"),
]
