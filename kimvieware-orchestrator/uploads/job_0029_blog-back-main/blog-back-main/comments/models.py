from django.db import models
from articles.models import Article

class Commentaire(models.Model):
    nom = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='commentaires'
    )

    def __str__(self):
        return f"{self.nom} - {self.article.titre}"
