import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cgbookstore.config.settings')
django.setup()


def check_sendgrid_config():
    print("\n=== Verificando Configurações SendGrid ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

    try:
        print("\nTentando enviar email de teste...")
        result = send_mail(
            subject='Teste de Configuração SendGrid',
            message='Este é um email de teste para verificar as configurações do SendGrid.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[input("Digite o email para teste: ")],
            fail_silently=False,
        )

        if result:
            print("\n✅ Email enviado com sucesso!")
        else:
            print("\n❌ Falha no envio do email")

    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        print("\nStacktrace completo:")
        print(traceback.format_exc())


if __name__ == "__main__":
    check_sendgrid_config()