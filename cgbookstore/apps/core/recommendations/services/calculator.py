from typing import Dict, List
from django.db.models import QuerySet


class RecommendationCalculator:
    """Serviço responsável por calcular scores das recomendações"""

    # Pesos para cada tipo de recomendação
    WEIGHTS = {
        'history': 0.5,
        'category': 0.3,
        'similarity': 0.2
    }

    def calculate_scores(self, recommendations: Dict[str, QuerySet]) -> Dict[int, float]:
        """
        Calcula scores finais para cada livro recomendado
        Args:
            recommendations: Dicionário com recomendações de cada provider
        Returns:
            Dicionário com scores finais por ID do livro
        """
        final_scores = {}

        for source, books in recommendations.items():
            weight = self.WEIGHTS.get(source, 0.1)

            for rank, book in enumerate(books):
                # Score base diminui com o ranking
                base_score = 1.0 / (rank + 1)
                # Aplica peso do provider
                weighted_score = base_score * weight

                book_id = book.id
                if book_id in final_scores:
                    final_scores[book_id] += weighted_score
                else:
                    final_scores[book_id] = weighted_score

        return final_scores

    def normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        """
        Normaliza scores para range 0-1
        Args:
            scores: Dicionário com scores por ID
        Returns:
            Dicionário com scores normalizados
        """
        if not scores:
            return {}

        max_score = max(scores.values())
        min_score = min(scores.values())
        score_range = max_score - min_score

        if score_range == 0:
            return {k: 1.0 for k in scores}

        return {
            k: (v - min_score) / score_range
            for k, v in scores.items()
        }