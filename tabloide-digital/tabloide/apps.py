from django.apps import AppConfig

class TabloideConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tabloide'
    
    def ready(self):
        # Import signals module
        from . import signals
        # Import other necessary modules
        import tabloide.modelss.profile