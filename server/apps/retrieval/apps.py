from django.apps import AppConfig


class RetrievalConfig(AppConfig):
    name = 'apps.retrieval'

    def ready(self):
        import apps.retrieval.signals

        # Django does not auto-discover signal files; this import is strictly necessary to execute the file and register the @receiver hooks into memory.
        # It must live inside ready()—not at the top level—to prevent premature model loading which triggers AppRegistryNotReady runtime errors.