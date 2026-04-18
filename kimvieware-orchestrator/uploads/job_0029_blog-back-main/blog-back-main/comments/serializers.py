from rest_framework import serializers
from .models import Commentaire

class CommentaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentaire
        fields = ['id', 'nom', 'message', 'article', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_message(self, value):
        if any(x in value.lower() for x in ['http', 'https', 'www.', '.com', '.fr', '.org', 'bit.ly']):
            raise serializers.ValidationError("Les liens et URLs sont interdits.")
        return value