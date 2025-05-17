# Importar para disponibilizar para o restante do aplicativo
from cgbookstore.apps.chatbot_literario.services.chatbot_service import chatbot
from cgbookstore.apps.chatbot_literario.services.training_service import TrainingService

# Certificar-se de que temos uma instância confiável
try:
    from cgbookstore.apps.chatbot_literario.services.training_service import training_service
except (ImportError, AttributeError):
    # Se falhar por algum motivo, criar uma nova instância
    training_service = TrainingService()