# Celery's autodiscover_tasks() looks for a module literally named
# tasks.py inside each INSTALLED_APPS entry - since this whole app is
# *named* "tasks", that module ends up being tasks/tasks.py. The actual
# task definitions live in retrieval_tasks.py and flashcard_tasks.py
# instead of directly in this file, purely for readability as more get
# added; this file just needs to import them so autodiscovery finds them.
from tasks.flashcard_tasks import generate_flashcards_task 
from tasks.retrieval_tasks import index_content_task  