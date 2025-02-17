import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def test_sendgrid():
    # Configurações
    smtp_server = "smtp.sendgrid.net"
    port = 587
    sender_email = "cg.bookstore.online@outlook.com"
    api_key = "SG.GrZm2LEaSUmLbEwdnQ6eBg._UAWXniDaQWYinXCMS6ILdRlD9oiZgXeI8dUm9NmgXU"

    print("\n=== Teste de Conexão SendGrid ===")
    print(f"De: {sender_email}")
    print(f"Servidor: {smtp_server}")
    print(f"Porta: {port}")

    # Email de destino
    recipient_email = input("Digite o email para teste: ")

    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['Subject'] = 'Teste de Email - CGBookstore'
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Conteúdo do email
        text = """
        Este é um email de teste do CGBookstore.

        Se você está recebendo este email, a configuração do SendGrid está funcionando.

        Atenciosamente,
        Equipe CGBookstore
        """

        msg.attach(MIMEText(text, 'plain'))

        # Conectar ao servidor
        print("\nConectando ao servidor SMTP...")
        server = smtplib.SMTP(smtp_server, port)
        server.set_debuglevel(1)  # Ativa logs detalhados
        server.starttls()

        print("Autenticando...")
        server.login("apikey", api_key)

        print("Enviando email...")
        server.send_message(msg)
        print("\n✅ Email enviado com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        print("\nStacktrace completo:")
        print(traceback.format_exc())

    finally:
        try:
            print("\nFechando conexão...")
            server.quit()
        except:
            pass


if __name__ == "__main__":
    test_sendgrid()