from rest_framework import serializers
from cgbookstore.apps.core.models import Book


class BookRecommendationSerializer(serializers.ModelSerializer):
    capa_url = serializers.SerializerMethodField()
    preco_formatado = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'titulo', 'autor', 'editora', 'categoria',
            'capa_url', 'preco_formatado', 'e_lancamento',
            'preco_promocional'
        ]

    def get_capa_url(self, obj):
        return obj.get_capa_url()

    def get_preco_formatado(self, obj):
        return obj.get_formatted_price()


class PersonalizedShelfSerializer(serializers.Serializer):
    based_on_history = BookRecommendationSerializer(many=True)
    based_on_categories = BookRecommendationSerializer(many=True)
    you_might_like = BookRecommendationSerializer(many=True)