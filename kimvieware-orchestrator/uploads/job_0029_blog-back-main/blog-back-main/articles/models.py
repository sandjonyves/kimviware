from django.db import models
from django.contrib.auth.models import User


class Categorie(models.Model):
    nom = models.CharField(
        max_length=100,
        unique=True,
        help_text="Code court (ex: BELGIQUE, CONGO...)",
    )
    label = models.CharField(
        max_length=200,
        help_text="Nom affiché (ex: Économie et Société – Belgique)",
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} – {self.label}"


class Article(models.Model):
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    image_url = models.CharField(max_length=500, blank=True, null=True)

    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.CASCADE, 
        related_name="articles"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles"
    )

    def __str__(self):
        return self.titre