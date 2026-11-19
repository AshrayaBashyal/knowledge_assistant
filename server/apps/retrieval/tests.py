from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document
from apps.notes.models import Note
from apps.retrieval.models import ContentIndex
from apps.retrieval.services.indexing import index_content


class ContentIndexStatusTests(TestCase):
    def test_document_and_note_lists_include_persisted_index_status(self):
        user = User.objects.create_user(
            email="index-status@example.com",
            password="test-password",
        )
        document = Document.objects.create(
            user=user,
            file="document/1/example.txt",
            original_filename="example.txt",
            file_type=Document.FileType.TXT,
        )
        note = Note.objects.bulk_create(
            [Note(user=user, title="Example note", content="Example content")]
        )[0]
        for obj in (document, note):
            ContentIndex.objects.create(
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.pk,
                status=ContentIndex.Status.INDEXED,
                chunk_count=2,
            )

        client = APIClient()
        client.force_authenticate(user=user)

        document_response = client.get("/api/documents/")
        note_response = client.get("/api/notes/")

        self.assertEqual(document_response.status_code, 200)
        self.assertEqual(document_response.data[0]["index_status"], "indexed")
        self.assertEqual(note_response.status_code, 200)
        self.assertEqual(note_response.data[0]["index_status"], "indexed")

    def test_failed_reindex_does_not_delete_previous_vectors(self):
        user = User.objects.create_user(
            email="reindex@example.com",
            password="test-password",
        )
        document = Document.objects.create(
            user=user,
            file="document/1/example.txt",
            original_filename="example.txt",
            file_type=Document.FileType.TXT,
        )
        index = ContentIndex.objects.create(
            content_type=ContentType.objects.get_for_model(document),
            object_id=document.pk,
            status=ContentIndex.Status.INDEXED,
            chunk_count=2,
        )
        vector_store = Mock()
        vector_store.add_documents.side_effect = RuntimeError("Embedding failed")

        with (
            patch(
                "apps.retrieval.services.indexing.load_content_text",
                return_value=["text"],
            ),
            patch(
                "apps.retrieval.services.indexing.split_into_chunks",
                return_value=[object()],
            ),
            patch(
                "apps.retrieval.services.indexing.get_vector_store",
                return_value=vector_store,
            ),
        ):
            result = index_content(document)

        self.assertEqual(result.status, ContentIndex.Status.FAILED)
        self.assertEqual(result.chunk_count, 2)
        vector_store.delete.assert_not_called()
