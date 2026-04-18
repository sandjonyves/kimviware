from rest_framework import serializers
from .models import Article, Categorie


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'label']
        read_only_fields = ['id']


class ArticleSerializer(serializers.ModelSerializer):
    # On surcharge le champ categorie pour afficher plus d'infos en lecture
    categorie = serializers.PrimaryKeyRelatedField(
        queryset=Categorie.objects.all(),
        write_only=True,  # On accepte l'ID en écriture (plus sûr)
    )
    
    # Champ calculé pour la lecture (renvoie l'objet complet ou juste le nom/label)
    categorie_detail = CategorieSerializer(source='categorie', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id',
            'titre',
            'contenu',
            'image_url',
            'categorie',          # ← ID en écriture
            'categorie_detail',   # ← objet complet en lecture (nom + label)
            'created_at',
            'updated_at',
            'admin',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'admin']