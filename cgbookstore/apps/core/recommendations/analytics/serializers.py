from rest_framework import serializers
from .models import RecommendationInteraction

class InteractionSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    interaction_type = serializers.ChoiceField(
        choices=RecommendationInteraction.INTERACTION_TYPES
    )
    source = serializers.ChoiceField(
        choices=RecommendationInteraction.SOURCE_TYPES
    )
    score = serializers.FloatField(required=False, allow_null=True)
    position = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, default=dict)

class InteractionStatsSerializer(serializers.Serializer):
    total_interactions = serializers.IntegerField()
    interactions_by_type = serializers.DictField(
        child=serializers.IntegerField()
    )
    interactions_by_source = serializers.DictField(
        child=serializers.IntegerField()
    )