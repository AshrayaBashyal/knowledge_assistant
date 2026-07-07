from django.conf import settings
from django.urls import reverse
from documents.models import Document
from pathlib import Path
from rest_framework import serializers


class DocumentSerializer(serializers.ModelSerializer):
    """Read representation - used for list, retrieve, and as the response
    shape after a successful upload."""
 
    download_url = serializers.SerializerMethodField()
 
    class Meta:
        model = Document
        fields = ["id", "original_filename", "file_type", "uploaded_at", "download_url"]
        read_only_fields = ["id", "original_filename", "file_type", "uploaded_at", "download_url"]
 
    def get_download_url(self, obj: Document) -> str:
        request = self.context.get("request")
        path = reverse("documents:document-download", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(path) if request else path
        

class DocumentUploadSerializer(serializers.ModelSerializer):
    """
    Write-only shape for POST /documents/ - accepts just the raw file.
    original_filename and file_type are derived from it, not client input,
    so a client can't claim a .exe is a .txt by lying about the field.
    """
 
    class Meta:
        model = Document
        fields = ["id", "file"]
        read_only_fields = ["id"]
 
    def validate_file(self, value):
        extension = Path(value.name).suffix.lower()
        if extension not in Document.EXTENSION_MAP:
            allowed = ", ".join(Document.EXTENSION_MAP)
            raise serializers.ValidationError(
                f"Unsupported file type '{extension}'. Allowed: {allowed}"
            )
 
        max_bytes = settings.DOCUMENT_MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError(
                f"File too large. Max size is {settings.DOCUMENT_MAX_UPLOAD_SIZE_MB}MB."
            )
 
        return value
 
    def create(self, validated_data):
        file = validated_data["file"]
        validated_data["original_filename"] = file.name
        validated_data["file_type"] = Document.EXTENSION_MAP[Path(file.name).suffix.lower()]
        return super().create(validated_data)
 
    def to_representation(self, instance):
        # Return the richer read shape (with download_url) after create, instead of echoing back the raw uploaded file.
        return DocumentSerializer(instance, context=self.context).data




# Later Use this with magic byte checking to prevent false extension attacks/ 

# class DocumentUploadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Document
#         fields = ["id", "file"]
#         read_only_fields = ["id"]

#     def validate_file(self, value):
#         extension = Path(value.name).suffix.lower()
        
#         # 1. Structural Extension Check
#         if extension not in Document.EXTENSION_MAP:
#             allowed = ", ".join(Document.EXTENSION_MAP.keys())
#             raise serializers.ValidationError(f"Unsupported extension. Allowed: {allowed}")

#         # 2. Deep Magic Byte Parsing (Security Fix)
#         # Read the first 2048 bytes to identify the true file type
#         file_head = value.read(2048)
#         actual_mime = magic.from_buffer(file_head, mime=True)
#         value.seek(0) # IMPORTANT: Reset stream pointer back to beginning!

#         expected_mime = Document.EXTENSION_MAP[extension]["mime"]
        
#         # Note: Some markdown files return text/plain, which is fine
#         if actual_mime != expected_mime and not (extension == ".md" and actual_mime == "text/plain"):
#             raise serializers.ValidationError("File contents do not match the file extension.")

#         # 3. Size Check
#         max_bytes = settings.DOCUMENT_MAX_UPLOAD_SIZE_MB * 1024 * 1024
#         if value.size > max_bytes:
#             raise serializers.ValidationError(f"File too large. Max is {settings.DOCUMENT_MAX_UPLOAD_SIZE_MB}MB.")

#         return value

#     def create(self, validated_data):
#         file = validated_data["file"]
#         ext = Path(file.name).suffix.lower()
#         validated_data["original_filename"] = file.name
#         # Updated to read from the new dictionary structure
#         validated_data["file_type"] = Document.EXTENSION_MAP[ext]["type"]
#         return super().create(validated_data)