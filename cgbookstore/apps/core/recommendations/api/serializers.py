from rest_framework import serializers
from cgbookstore.apps.core.models import Book


class BookRecommendationSerializer(serializers.ModelSerializer):
    """Serializer para livros locais"""
    capa_url = serializers.SerializerMethodField()
    preco_formatado = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'titulo', 'autor', 'editora', 'isbn',
            'categoria', 'genero', 'descricao', 'capa_url',
            'preco', 'preco_promocional', 'preco_formatado',  # <--- Adicionado aqui
            'e_destaque', 'quantidade_vendida', 'quantidade_acessos'
        ]

    def get_capa_url(self, obj):
        return obj.get_capa_url()

    def get_preco_formatado(self, obj):
        return obj.get_formatted_price()

class ExternalBookSerializer(serializers.Serializer):
    """Serializer para livros externos da API"""
    id = serializers.CharField()
    volumeInfo = serializers.DictField()

class PersonalizedShelfSerializer(serializers.Serializer):
    """Serializer para prateleira personalizada"""
    destaques = serializers.ListField(child=serializers.DictField(), required=False)
    seu_idioma = serializers.ListField(child=serializers.DictField(), required=False)
    por_genero = serializers.DictField(required=False)
    por_autor = serializers.DictField(required=False)
    descobertas = serializers.ListField(child=serializers.DictField(), required=False)
    has_external = serializers.BooleanField()
    total = serializers.IntegerField()
    language_preference = serializers.FloatField(required=False)