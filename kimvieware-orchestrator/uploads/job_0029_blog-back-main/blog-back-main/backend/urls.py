from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import des ViewSets
from articles.views import (
    ArticleViewSet,
    CategorieViewSet,          # ← Nouveau : ajoute-le ici
)
from comments.views import CommentaireViewSet

from rest_framework.authtoken.views import obtain_auth_token

# Création du router
router = DefaultRouter()

# Enregistrement des endpoints API
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'commentaires', CommentaireViewSet, basename='commentaire')
router.register(r'categories', CategorieViewSet, basename='categorie')  # ← Ajouté ici

# URLs principales
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),           # Tous les endpoints API sous /api/
    path('api-token-auth/', obtain_auth_token),   # Pour obtenir un token (login)
]