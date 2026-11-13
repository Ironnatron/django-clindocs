from django.apps import AppConfig


class ClinDocsConfig(AppConfig):
    name = 'polls'
    verbose_name = 'ClinDocs'

    def ready(self):
        from . import signals
