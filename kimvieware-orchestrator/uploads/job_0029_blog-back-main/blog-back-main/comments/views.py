from rest_framework.viewsets import ModelViewSet
from .models import Commentaire
from .serializers import CommentaireSerializer
from rest_framework.permissions import AllowAny

class CommentaireViewSet(ModelViewSet):
    serializer_class = CommentaireSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Commentaire.objects.all().order_by('-created_at')
        article_id = self.request.query_params.get('article')  # lire le paramètre ?article=ID
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        return queryset
