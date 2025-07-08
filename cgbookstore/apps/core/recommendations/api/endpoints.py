from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from ...models import Book
from ..engine import RecommendationEngine
from ..utils.cache_manager import RecommendationCache
from .serializers import BookRecommendationSerializer, PersonalizedShelfSerializer, ExternalBookSerializer

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """Endpoint para obter recomendações gerais"""
    limit_str = request.query_params.get('limit', '10') # Obter como string
    try:
        limit = int(limit_str)
    except ValueError:
        limit = 10

    user = request.user

    # Tenta obter do cache
    # O RecommendationCache.get_recommendations já retorna dados serializados adequadamente pelo _serialize_recommendations
    cached_data = RecommendationCache.get_recommendations(user)
    if cached_data:
        # cached_data é uma lista de dicts já serializados pelo _serialize_recommendations do RecommendationCache
        # Estes dicts têm 'type' e 'data'. A resposta da API deve ser uma lista de dados de livros.
        # Precisamos processar cached_data para o formato de resposta esperado ou ajustar o que é salvo/retornado pelo cache.
        # Por enquanto, vamos assumir que o formato do cache é o que queremos na resposta.
        # Se o cache_data já for uma lista de recomendações serializadas prontas para o cliente:
        return Response(cached_data.get('recommendations', [])[:limit])


    # Se não estiver em cache, gera novas recomendações
    engine = RecommendationEngine()
    # recommendations_from_engine é uma List[Union[Book, Dict]]
    recommendations_from_engine = engine.get_recommendations(user, limit=limit)

    # Prepara os dados para a resposta da API serializando cada tipo de item
    response_data = []
    for item in recommendations_from_engine:
        if isinstance(item, Book):
            response_data.append(BookRecommendationSerializer(item).data)
        elif isinstance(item, dict) and 'volumeInfo' in item: # Suposição para identificar livro externo
            # Se o dict 'item' já estiver no formato que a API espera para livros externos,
            # você pode adicioná-lo diretamente ou usar o ExternalBookSerializer.
            # Usar ExternalBookSerializer para consistência e validação da estrutura.
            response_data.append(ExternalBookSerializer(item).data)
        # Adicione 'else' para lidar com outros tipos de dicts se necessário, ou logar.

    # Salva a lista mista original (Book objects e dicts) no cache.
    # O RecommendationCache._serialize_recommendations fará a serialização interna para o cache.
    # O metadata aqui pode ser útil para a lógica de _is_cache_valid
    RecommendationCache.set_recommendations(user, recommendations_from_engine, metadata={'source': 'live_generation'})

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personalized_shelf(request):
    """Endpoint para obter prateleira personalizada"""
    shelf_size_str = request.query_params.get('shelf_size', '5') # Obter como string
    try:
        shelf_size = int(shelf_size_str)
    except ValueError:
        shelf_size = 5 # Default shelf_size

    user = request.user

    # Tenta obter do cache. get_shelf retorna dados já serializados pelo PersonalizedShelfSerializer
    cached_shelf_data = RecommendationCache.get_shelf(user)
    if cached_shelf_data:
        # PersonalizedShelfSerializer serializa a prateleira inteira como um grande dicionário.
        # A lógica de ajustar o tamanho das listas internas precisaria ser feita
        # antes de serializar e salvar, ou aqui ao recuperar.
        # Por ora, vamos assumir que o cache já está no formato correto e com o tamanho correto,
        # ou que o cliente lida com o excesso se o shelf_size do cache for maior.
        # Se uma re-serialização ou ajuste for necessário, seria mais complexo.
        # O serializer do PersonalizedShelfSerializer não tem um `many=True` no uso,
        # então ele espera um único objeto dict para serializar/desserializar.
        return Response(cached_shelf_data)

    # Se não estiver em cache, gera nova prateleira
    engine = RecommendationEngine()
    # shelf_data do engine já é um dicionário estruturado com listas de Book e/ou dicts externos
    shelf_data_from_engine = engine.get_personalized_shelf(user, shelf_size=shelf_size)

    # Serializa os dados da prateleira completa
    # PersonalizedShelfSerializer espera um dicionário e serializa suas chaves/valores.
    # As listas internas (destaques, seu_idioma, descobertas) podem conter objetos Book ou dicts.
    # Precisamos garantir que PersonalizedShelfSerializer lide com isso,
    # ou pré-serializar os itens dentro dessas listas.

    # Abordagem: Pré-serializar os itens dentro das listas de shelf_data_from_engine
    processed_shelf_data = {}
    for section_key, section_items in shelf_data_from_engine.items():
        if section_key in ['destaques', 'seu_idioma', 'descobertas'] and isinstance(section_items, list):
            serialized_items = []
            for item in section_items:
                if isinstance(item, Book):
                    serialized_items.append(BookRecommendationSerializer(item).data)
                elif isinstance(item, dict) and 'volumeInfo' in item:
                    serialized_items.append(ExternalBookSerializer(item).data)
                elif isinstance(item, dict): # Outros dicts (ex: por_genero, por_autor que já são dicts de listas)
                    # Se as sub-listas de por_genero/por_autor também precisam de serialização item a item:
                    if section_key in ['por_genero', 'por_autor'] and isinstance(item, dict): # item aqui é o valor da categoria/autor
                        # Este 'item' é na verdade o valor associado a uma chave em por_genero/por_autor, que é uma lista
                        # Esta lógica precisa ser mais específica para a estrutura de por_genero/por_autor
                        # Por ora, vamos assumir que PersonalizedShelfSerializer lida com a estrutura interna
                        # ou que os itens já estão serializados se necessário.
                        # A lógica original abaixo apenas serializa o shelf_data_from_engine como um todo.
                        pass # A lógica de serialização abaixo cuidará disso se o serializer for robusto

            if serialized_items: # Se houve serialização para estas chaves
                 processed_shelf_data[section_key] = serialized_items
            else: # Mantém como está se não for uma lista de itens serializáveis ou se a chave não for uma das listadas
                 processed_shelf_data[section_key] = section_items

        elif section_key in ['por_genero', 'por_autor'] and isinstance(section_items, dict):
            processed_sub_dict = {}
            for sub_key, sub_list_items in section_items.items():
                serialized_sub_items = []
                if isinstance(sub_list_items, list):
                    for item in sub_list_items:
                        if isinstance(item, Book):
                            serialized_sub_items.append(BookRecommendationSerializer(item).data)
                        elif isinstance(item, dict) and 'volumeInfo' in item:
                             serialized_sub_items.append(ExternalBookSerializer(item).data)
                        else:
                            serialized_sub_items.append(item) # Mantém outros dicts/primitivos como estão
                processed_sub_dict[sub_key] = serialized_sub_items
            processed_shelf_data[section_key] = processed_sub_dict
        else:
            processed_shelf_data[section_key] = section_items # Mantém outras chaves como 'has_external', 'total', etc.

    serializer = PersonalizedShelfSerializer(processed_shelf_data)
    serialized_shelf_for_api = serializer.data

    # Salva a estrutura serializada (ou a estrutura pré-serializada processed_shelf_data) no cache.
    # O PersonalizedShelfSerializer não tem um método _serialize_recommendations interno como o RecommendationCache.
    # Portanto, o que é salvo deve ser o que o serializer produz.
    RecommendationCache.set_shelf(user, serialized_shelf_for_api)

    return Response(serialized_shelf_for_api)