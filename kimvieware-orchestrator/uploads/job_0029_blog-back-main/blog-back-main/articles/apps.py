from django.apps import AppConfig

class ArticlesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'articles'

    def ready(self):
        # Importer le modèle **à l'intérieur** de ready()
        from django.contrib.auth.models import User

        # Créer le superuser uniquement si la DB est prête
        try:
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser(
                    username="admin",
                    email="admin@gmail.com",
                    password="admin123"
                )
                print("Superuser par défaut créé : admin/admin123")
        except Exception as e:
            # Par exemple, si migrate n'a pas encore été fait, on ignore
            pass
