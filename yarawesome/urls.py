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

from apps.core import views as core_views
from apps.rules import api as rule_browser_api
from apps.rules import views as rule_browser_views
from apps.rule_collections import api as rule_collections_api
from apps.rule_collections import views as rule_collections_views
from apps.rule_editor import api as rule_editor_api
from apps.rule_editor import views as rule_editor_views
from apps.rule_lab import api as rule_lab_api
from apps.rule_lab import views as rule_lab_views
from apps.rule_import import api as rule_import_api
from apps.rule_import import views as rule_import_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("django.contrib.auth.urls")),
    path(
        "api/collections/<str:collection_id>/",
        rule_collections_api.RuleCollectionResource.as_view(),
        name="api-collection",
    ),
    path(
        "api/collections/<str:collection_id>/download/",
        rule_collections_api.RuleCollectionDownloadTaskResource.as_view(),
        name="api-download-collection-task",
    ),
    path(
        "api/collections/<str:collection_id>/download/<str:download_id>/",
        rule_collections_api.RuleCollectionDownloadTaskResource.as_view(),
        name="api-download-collection",
    ),
    path(
        "api/collections/<str:collection_id>/clone/",
        rule_collections_api.RuleCollectionCloneResource.as_view(),
        name="api-clone-collection",
    ),
    path(
        "api/collections/<str:collection_id>/publish/",
        rule_collections_api.PersonalRuleCollectionPublishResource.as_view(),
        name="api-publish-collection",
    ),
    path(
        "api/lab/upload/",
        rule_lab_api.CreateUploadBinaryResource.as_view(),
        name="api-create-upload-binary",
    ),
    path(
        "api/lab/binaries/<str:binary_id>/scan/",
        rule_lab_api.ScanUploadBinaryResource.as_view(),
        name="api-scan-upload-binary",
    ),
    path(
        "api/rules/import/",
        rule_import_api.CreateImportJobResource.as_view(),
        name="api-create-import-job",
    ),
    path(
        "api/rules/import/<str:import_id>",
        rule_import_api.ImportJobResource.as_view(),
        name="api-view-import-job",
    ),
    path(
        "api/rules/",
        rule_browser_api.RuleSearchResource.as_view(public=True),
        name="api-shared-rules-search",
    ),
    path(
        "api/rules/mine/",
        rule_browser_api.RuleSearchResource.as_view(public=False),
        name="api-my-rules-search",
    ),
    path(
        "api/rules/<str:rule_id>/",
        rule_browser_api.RuleResource.as_view(),
        name="api-rule-view",
    ),
    path(
        "api/rules/<str:rule_id>/clone/",
        rule_browser_api.RuleCloneResource.as_view(),
        name="api-rule-clone",
    ),
    path(
        "api/rules/<str:rule_id>/editor/",
        rule_editor_api.RuleEditorResource.as_view(),
        name="api-rule-editor",
    ),
    path("editor/", rule_editor_views.editor, name="editor"),
    path("import/", rule_import_views.import_rule, name="import"),
    path("lab/upload/", rule_lab_views.upload_test_binary, name="lab"),
    path("rules/<str:rule_id>/editor/", rule_editor_views.editor, name="editor-open"),
    path("rules/", rule_browser_views.shared_rules, name="shared-rules-search"),
    path(
        "rules/mine/",
        rule_browser_views.my_rules,
        name="my-rules-search",
    ),
    path("rules/<str:rule_id>/", rule_browser_views.rule, name="rule"),
    path(
        "collections/",
        rule_collections_views.shared_collections,
        name="shared-collections",
    ),
    path(
        "collections/mine/",
        rule_collections_views.my_collections,
        name="my-collections",
    ),
    path(
        "collections/<collection_id>/",
        rule_collections_views.collection,
        name="collection",
    ),
    path("imports/mine/", rule_import_views.my_imports, name="my-imports"),
    path("", core_views.index, name="home"),
]
