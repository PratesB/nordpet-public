from django.apps import AppConfig


class AiConfig(AppConfig):
    name = 'ai'

    def ready(self):
        import ai.signals
