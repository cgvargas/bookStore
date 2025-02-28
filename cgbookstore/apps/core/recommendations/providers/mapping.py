from typing import Set


class CategoryMapping:
    """Classe para mapeamento e normalização de categorias e gêneros"""

    # Mapeamento de categorias principais e suas relações
    CATEGORY_RELATIONS = {
        'fiction': {
            'similar': [
                'fiction', 'ficção', '[\'fiction\']', 'young adult fiction',
                'fantasy', 'fantasia'
            ],
            'related': [
                'aventura', 'ação', 'action', 'adventure',
                'fantasia de ação e aventura', 'livros de fantasia'
            ]
        },
        'manga': {
            'similar': [
                'manga', 'mangá', 'manhwa', 'graphic novels',
                'mangá hqs, mangás e graphic novels', 'comics & graphic novels',
                '[\'comics & graphic novels\']', 'novel coreana'
            ],
            'related': [
                'anime', 'light novel', 'novel', 'quadrinhos',
                'mangá de mistério', 'suspense e crime'
            ]
        },
        'programming': {
            'similar': [
                'computers', '[\'computers\']', 'programação',
                'computação, informática e mídias digitais',
                'programação de computadores'
            ],
            'related': [
                'tecnologia', 'software', 'development', 'educativo'
            ]
        },
        'religion': {
            'similar': [
                'religion', '[\'religion\']', 'bibles', '[\'bibles\']',
                'devocionais cristãs', 'ritual religião e espiritualidade'
            ],
            'related': [
                'adoração', 'louvor', 'liturgia', 'cristão',
                'fantasia religião e espiritualidade'
            ]
        },
        'fantasy': {
            'similar': [
                'fantasia', 'fantasy', 'fantasia épica',
                'fantasia de ação e aventura', 'alta fantasia'
            ],
            'related': [
                'aventura', 'ação', 'espada e feitiçaria',
                'livros de fantasia de ação e aventura'
            ]
        }
    }

    def clean_category(self, category: str) -> str:
        """Limpa uma string de categoria"""
        if not category:
            return ''

        # Remove colchetes, aspas e espaços extras
        category = category.lower().strip()
        category = category.replace('[', '').replace(']', '')
        category = category.replace('\'', '').replace('"', '')
        category = category.strip()

        # Remove categorias vazias
        if category in ('[]', ''):
            return ''

        return category

    def normalize_category(self, category: str) -> str:
        """Normaliza uma categoria para um formato padrão"""
        category = self.clean_category(category)
        if not category:
            return ''

        # Tenta cada categoria base
        for base_category, relations in self.CATEGORY_RELATIONS.items():
            if (category == base_category or
                    category in relations['similar'] or
                    any(similar in category for similar in relations['similar'])):
                return base_category

        return category

    def get_related_categories(self, category: str) -> Set[str]:
        """Retorna categorias relacionadas"""
        category = self.normalize_category(category)
        related = set()

        # Busca relacionamentos diretos
        if category in self.CATEGORY_RELATIONS:
            related.update(self.CATEGORY_RELATIONS[category]['similar'])
            related.update(self.CATEGORY_RELATIONS[category]['related'])

        # Busca relacionamentos indiretos
        for base_category, relations in self.CATEGORY_RELATIONS.items():
            if (category in relations['similar'] or
                    category in relations['related']):
                related.add(base_category)
                related.update(relations['similar'])

        return {cat for cat in related if cat}