import os
import django
from django.core.mail import send_mail
from django.conf import settings
import socket
import environ


def setup_django_environment():
    """Configura o ambiente Django com as variáveis corretas"""
    # Carrega as variáveis de ambiente primeiro
    env = environ.Env()
    env_file = '.env.prod'
    env_path = os.path.join(os.getcwd(), env_file)

    if os.path.exists(env_path):
        environ.Env.read_env(env_path)
        print(f"✅ Arquivo {env_file} carregado com sucesso!")
    else:
        print(f"❌ Arquivo {env_file} não encontrado!")
        return False

    # Define o ambiente como produção
    os.environ['DJANGO_ENV'] = 'production'

    # Configura o módulo de settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')

    # Inicializa o Django
    try:
        django.setup()
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar Django: {e}")
        return False


def test_smtp_connection():
    """Testa a conexão com o servidor SMTP"""
    try:
        print("\n=== Testando Conexão SMTP ===")
        sock = socket.create_connection((settings.EMAIL_HOST, settings.EMAIL_PORT), timeout=5)
        sock.close()
        print("✅ Conexão com servidor SMTP bem sucedida!")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão SMTP: {e}")
        return False


def send_test_email():
    """Envia um e-mail de teste usando as configurações de produção"""
    print("\n=== Configurações de E-mail ===")
    print(f"Ambiente: {'Produção' if os.getenv('DJANGO_ENV') == 'production' else 'Desenvolvimento'}")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Porta: {settings.EMAIL_PORT}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print(f"Usuário: {settings.EMAIL_HOST_USER}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")

    # Verifica se as configurações essenciais estão presentes
    if not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ EMAIL_HOST_PASSWORD não configurado!")
        return

    # Testar conexão SMTP
    if not test_smtp_connection():
        return

    try:
        recipient = input("\nDigite o e-mail para teste: ").strip()
        if not recipient:
            print("❌ E-mail de destino não fornecido!")
            return

        # Enviar e-mail de teste
        send_mail(
            subject='Teste de E-mail - CGBookstore',
            message='Este é um e-mail de teste para verificar a configuração do SendGrid.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print("\n✅ E-mail de teste enviado com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro ao enviar e-mail: {str(e)}")
        print("\nDetalhes da configuração:")
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")


if __name__ == '__main__':
    if setup_django_environment():
        send_test_email()