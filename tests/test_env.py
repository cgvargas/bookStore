import os
import sys
import environ
from django.core.exceptions import ImproperlyConfigured


def test_environment_config():
    # Imprimir todas as variáveis de ambiente para depuração
    print("Variáveis de ambiente:")
    for key, value in os.environ.items():
        print(f"{key}: {value}")

    # Verificar explicitamente a variável DJANGO_ENV
    env_type = os.environ.get('DJANGO_ENV')
    print(f"\nDJANGO_ENV obtido: {env_type}")

    # Se não foi definido, usar valor padrão e informar
    if not env_type:
        print("⚠️ DJANGO_ENV não definido. Usando desenvolvimento como padrão.")
        env_type = 'development'

    # Determinar o arquivo .env correto
    env_file = '.env.dev' if env_type == 'development' else '.env.prod'

    print(f"\nTestando configurações de ambiente - Tipo: {env_type}")
    print(f"Arquivo de configuração: {env_file}")

    # Carregar o arquivo .env
    try:
        environ.Env.read_env(os.path.join(os.getcwd(), env_file))
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo {env_file} não encontrado!")
        sys.exit(1)

    # Inicializar environ
    env = environ.Env()

    # Testar algumas configurações
    print("\nVerificando configurações:")
    print(f"DEBUG: {env.bool('DEBUG')}")
    print(f"Email Backend: {env('EMAIL_BACKEND')}")

    # Tratar ALLOWED_HOSTS de forma mais flexível
    try:
        allowed_hosts = env('ALLOWED_HOSTS')
        print(f"Allowed Hosts (string original): {allowed_hosts}")

        # Converter string para lista, lidando com diferentes formatos
        if ',' in allowed_hosts:
            hosts_list = [host.strip() for host in allowed_hosts.split(',')]
        else:
            hosts_list = [allowed_hosts.strip()]

        print(f"Allowed Hosts (lista processada): {hosts_list}")
    except ImproperlyConfigured as e:
        print(f"Erro ao carregar ALLOWED_HOSTS: {e}")
        hosts_list = ['*'] if env_type == 'development' else []

    # Testar chave secreta
    secret_key = env('SECRET_KEY')
    print(f"\nSecret Key (primeiros 10 caracteres): {secret_key[:10]}...")

    # Verificar ambiente
    if env_type == 'development':
        assert env(
            'EMAIL_BACKEND') == 'django.core.mail.backends.console.EmailBackend', "Erro: Backend de email incorreto para desenvolvimento"
        assert len(hosts_list) > 0, "Deve ter pelo menos um host configurado"
    else:
        assert env(
            'EMAIL_BACKEND') == 'django.core.mail.backends.smtp.EmailBackend', "Erro: Backend de email incorreto para produção"
        assert len(hosts_list) > 0, "Hosts de produção devem ser explicitamente definidos"

    print("\n✅ Configurações de ambiente carregadas com sucesso!")


if __name__ == '__main__':
    test_environment_config()