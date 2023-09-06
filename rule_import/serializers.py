import os
import shutil
import patoolib
from rest_framework import serializers
from yarawesome.settings import MEDIA_ROOT

from core.models import ImportYaraRuleJob


def extract_specific_files(
    file_path, extract_dir=None, allowed_extensions=None, extracted_file_prefix=None
):
    """
    Extracts specific files with allowed extensions from an archive file to a specified directory.

    Args:
        file_path (str): Path to the archive file.
        extract_dir (str, optional): Directory where the contents should be extracted.
                                     If not specified, the contents will be extracted to the current directory.
        allowed_extensions (list, optional): List of allowed file extensions (e.g., ['.yar', '.yara']).

    Returns:
        str: The path to the directory where the contents are extracted.
    """
    try:
        if extract_dir is None:
            extract_dir = "./"

        os.makedirs(extract_dir, exist_ok=True)

        temp_dir = patoolib.extract_archive(file_path, outdir=None)

        for root, _, files in os.walk(temp_dir):
            for file_name in files:
                file_ext = os.path.splitext(file_name)[1]
                if allowed_extensions is None or file_ext in allowed_extensions:
                    source_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(source_path, temp_dir)
                    destination_path = os.path.join(extract_dir, relative_path)
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    if allowed_extensions and extracted_file_prefix:
                        destination_path = destination_path.replace(
                            file_name, f"{extracted_file_prefix}_{file_name}"
                        )
                    shutil.copy2(source_path, destination_path)

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
        return extract_dir

    except Exception as e:
        return str(e)


class CreateImportJobSerializer(serializers.Serializer):

    file = serializers.FileField()

    def create(self, validated_data):
        import_id = validated_data.pop("import_id")
        uploaded_file = validated_data["file"]

        file_path = f"{MEDIA_ROOT}/uploads/{uploaded_file.name}"
        with open(file_path, "wb") as destination_file:
            for chunk in uploaded_file.chunks():
                destination_file.write(chunk)
        extract_specific_files(
            file_path,
            allowed_extensions=[".yara", ".yar"],
            extract_dir=f"{MEDIA_ROOT}/rule-uploads/",
            extracted_file_prefix=import_id,
        )
        return validated_data

    def update(self, instance, validated_data):
        # Custom logic to update an existing object with the validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportYaraRuleJob
        fields = "__all__"
