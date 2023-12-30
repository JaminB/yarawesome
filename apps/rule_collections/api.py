import json
from hashlib import sha256
from datetime import datetime
from django.http import HttpResponse
from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.rule_collections.models import YaraRuleCollection, YaraRuleCollectionDownload
from apps.rule_import.models import ImportYaraRuleJob
from .tasks import clone_collection, download_collection, publish_collection
from .serializers import (
    YaraRuleCollectionDeleteRequest,
    YaraRuleCollectionPublishRequest,
    YaraRuleCollectionUpdateRequest,
    YaraRuleCollectionCloneRequest,
)


class YaraRuleCollectionCloneResource(APIView):
    """
    A view to clone a YARA rule collection into a personal collection.
    """

    def put(self, request, *args, **kwargs):
        YaraRuleCollectionCloneRequest(data=kwargs).is_valid(raise_exception=True)
        copy_from_collection_id = kwargs["collection_id"]
        copy_from_collection = YaraRuleCollection.objects.get(
            id=copy_from_collection_id
        )
        new_import_job = ImportYaraRuleJob(user=request.user)
        new_import_job.save()

        new_collection = YaraRuleCollection.objects.create(
            user=request.user,
            name=copy_from_collection.name,
            description=copy_from_collection.description,
            import_job=new_import_job,
        )
        new_collection.save()

        # Fork to celery worker
        clone_collection.delay(
            model_to_dict(copy_from_collection),
            model_to_dict(new_collection),
            {"id": request.user.id},
        )
        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "collection": {
                    "id": new_collection.id,
                    "name": new_collection.name,
                    "description": new_collection.description,
                    "icon": new_collection.icon,
                },
                "import_job": new_import_job.id,
                "message": "Starting process of cloning collection. This may take some time to complete.",
            },
        )


class YaraRuleCollectionDownloadTaskResource(APIView):
    """
    A view to create download task from YARA rule collection.
    """

    def get(self, request, *args, **kwargs):
        collection_id = kwargs["collection_id"]
        download_id = kwargs["download_id"]
        download = request.query_params.get("download")

        if not download:
            try:
                YaraRuleCollectionDownload.objects.get(
                    id=download_id, collection_id=collection_id
                )
                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "download_url": f"/api/collections/{collection_id}/download/{download_id}/?download=true"
                    },
                )
            except YaraRuleCollectionDownload.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            collection_download = YaraRuleCollectionDownload.objects.get(
                id=download_id, collection_id=collection_id
            )

            if collection_download:
                collection_name = YaraRuleCollection.objects.get(id=collection_id).name
                response = HttpResponse(
                    collection_download.content,
                    content_type="application/x-yara",
                )
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{collection_name}.yara"'
                return response
        return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        """
        Create a YARA rule collection download job.
        """
        download_id = sha256(str(datetime.now()).encode()).hexdigest()
        collection_id = kwargs["collection_id"]
        download_collection.delay(
            collection_id=collection_id,
            download_id=download_id,
        )
        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "download_id": download_id,
                "collection_id": collection_id,
                "message": "Starting process of creating downloadable collection. "
                "This may take some time to complete.",
            },
        )


class YaraRuleCollectionResource(APIView):
    """
    A view to view a YARA rule collection.
    """

    def put(self, request, *args, **kwargs):
        """
        Update a YARA rule collection.
        """

        request_body = request.body.decode("utf-8")
        data = None
        if request_body:
            try:
                data = json.loads(request_body)
                data.update(kwargs)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON data"}, status=400)
        if not data:
            return Response({"error": "No payload provided"}, status=400)
        serializer = YaraRuleCollectionUpdateRequest(data=data)
        serializer.is_valid(raise_exception=True)
        collection_id = serializer.validated_data["collection_id"]
        yara_rule_collection = YaraRuleCollection.objects.filter(
            id=collection_id, user=request.user
        ).first()
        if not yara_rule_collection:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"error": "Collection not found."},
            )
        yara_rule_collection.name = serializer.validated_data["name"]
        yara_rule_collection.description = serializer.validated_data["description"]
        yara_rule_collection.icon = serializer.validated_data["icon"]
        yara_rule_collection.save()
        return Response(
            status=status.HTTP_200_OK,
            data={
                "collection": {
                    "id": yara_rule_collection.id,
                    "name": yara_rule_collection.name,
                    "description": yara_rule_collection.description,
                    "icon": yara_rule_collection.icon,
                }
            },
        )

    def delete(self, request, *args, **kwargs):
        serializer = YaraRuleCollectionDeleteRequest(data=kwargs)
        serializer.is_valid(raise_exception=True)
        collection_id = serializer.validated_data["collection_id"]
        yara_rule_collection = YaraRuleCollection.objects.filter(
            id=collection_id, user=request.user
        ).first()
        if not yara_rule_collection:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"error": "Collection not found."},
            )
        yara_rule_collection.delete()
        return Response(status=status.HTTP_200_OK, data={"deleted": True})


class PublishYaraRuleCollectionResource(APIView):
    """
    A view to publish a YARA rule collection, and all of its rules to the public.
    """

    def put(self, request, *args, **kwargs):
        """
        Publish a YARA rule collection.
        """
        set_to_public = True
        serializer = YaraRuleCollectionPublishRequest(data=kwargs)
        serializer.is_valid(raise_exception=True)
        collection_id = serializer.validated_data["collection_id"]

        yara_rule_collection = YaraRuleCollection.objects.filter(
            id=collection_id, user=request.user
        ).first()

        request_body = request.body.decode("utf-8")
        if request_body:
            try:
                data = json.loads(request_body)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON data"}, status=400)
            if not data.get("public"):
                set_to_public = False
        publish_collection.delay(
            collection=model_to_dict(yara_rule_collection),
            user={"id": request.user.id},
            set_to_public=set_to_public,
        )
        yara_rule_collection.public = set_to_public
        yara_rule_collection.save()

        return Response(
            data={
                "published": yara_rule_collection.public,
                "message": "Starting process of publishing collection. This may take some time to complete.",
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request, *args, **kwargs):
        """
        Check if a YARA rule collection is published.
        """
        serializer = YaraRuleCollectionPublishRequest(data=kwargs)
        serializer.is_valid(raise_exception=True)
        collection_id = serializer.validated_data["collection_id"]
        yara_rule_collection = YaraRuleCollection.objects.filter(
            id=collection_id, user=request.user
        ).first()
        if not yara_rule_collection:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            data={"published": yara_rule_collection.public},
            status=status.HTTP_200_OK,
        )
