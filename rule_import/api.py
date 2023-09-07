import requests
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ImportYaraRuleJob, YaraRule, YaraRuleCollection
from yarawesome import config

from .serializers import CreateImportJobSerializer, ImportJobSerializer


def make_import_count_request(import_id: int) -> int:
    """
    Make a count request to the database.

    Args:
        import_id (int): The import ID to search for.

    Returns:
        int: The number of YARA rules imported.
    """
    return YaraRule.objects.filter(import_job__id=import_id).count()


class CreateImportJobResource(CreateAPIView):
    """
    A view to create an ImportYaraRuleJob instance.
    """

    serializer_class = CreateImportJobSerializer
    parser_classes = [MultiPartParser]

    def create(self, request, *args, **kwargs):
        # Create the ImportYaraRuleJob instance
        import_job = ImportYaraRuleJob(user=request.user)
        import_job.save()

        # Create the serializer instance
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(import_id=import_job.id)

        # Return a JSON response
        response_data = {
            "message": f"Import job {import_job.id} created successfully.",
            "import_id": import_job.id,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class ImportJobResource(APIView):
    def get(self, request, import_id):
        try:
            # Retrieve the ImportYaraRuleJob by id
            import_job = ImportYaraRuleJob.objects.get(id=import_id)

            # Serialize the result
            serializer = ImportJobSerializer(import_job)

            results = {
                "job_info": serializer.data,
                "imported_rule_count": make_import_count_request(import_id),
                "collections_created": YaraRuleCollection.objects.filter(
                    import_job__id=import_id
                ).count(),
            }
            return Response(results, status=status.HTTP_200_OK)
        except ImportYaraRuleJob.DoesNotExist:
            return Response(
                {"error": f"Import job {import_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
