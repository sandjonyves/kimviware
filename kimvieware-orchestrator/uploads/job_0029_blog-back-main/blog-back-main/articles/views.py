from rest_framework.viewsets import ModelViewSet
from .models import Article, Categorie
from .serializers import ArticleSerializer, CategorieSerializer
from .permissions import IsAdminOrReadOnly

class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        # On associe automatiquement l'article à l'admin connecté
        serializer.save(admin=self.request.user)

class CategorieViewSet(ModelViewSet):
    queryset = Categorie.objects.all().order_by('nom')
    serializer_class = CategorieSerializer
    permission_classes = [IsAdminOrReadOnly]