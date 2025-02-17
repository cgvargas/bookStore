# apps/core/views/auth.py
"""
Módulo de autenticação customizado para o projeto.

Fornece views customizadas para login, logout, reset de senha e verificação de email.
Inclui tratamento de logs, mensagens e validações personalizadas.
"""

import logging
import smtplib

from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.conf import settings
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password

from ..forms import CustomPasswordResetForm
from ..models import User

# Configuração de logging para rastreamento de eventos de autenticação
logger = logging.getLogger(__name__)

PASSWORD_REUSE_ERROR = "Esta senha já foi utilizada recentemente. Por segurança, você não pode reutilizar suas últimas 3 senhas."

class CustomLoginView(LoginView):
    """
    View customizada para login com validações adicionais.

    Características:
    - Verifica status da conta (ativa/inativa)
    - Requer verificação de email
    - Gerencia sessão com opção de lembrar login
    """
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """
        Validação personalizada do formulário de login.
        Verifica status da conta e configura a sessão.
        """
        user = form.get_user()
        if not user.is_active:
            logger.warning(f'Tentativa de login com conta inativa: {user.username}')
            messages.error(self.request,
                           'Conta inativa. Por favor, verifique seu email ou entre em contato com o suporte.')
            return self.form_invalid(form)

        if not user.email_verified and not user.is_superuser:
            logger.warning(f'Tentativa de login sem verificação de email: {user.username}')
            messages.error(self.request,
                           'Por favor, verifique seu email para ativar sua conta.')
            return self.form_invalid(form)

        # Gerencia duração da sessão baseado na opção "lembrar-me"
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)

        logger.info(f'Login bem sucedido para o usuário: {user.username}')
        messages.success(self.request, 'Login realizado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Tratamento de erro para login com mensagens específicas.
        """
        try:
            username = form.cleaned_data.get('username')
            if username:
                user = User.objects.filter(username=username).first()
                if user and not user.is_active:
                    logger.warning(f'Tentativa de login com conta inativa: {username}')
                    messages.error(self.request, 'Conta inativa. Por favor, verifique seu email para ativar sua conta.')
                    return super().form_invalid(form)

            logger.warning('Tentativa de login falhou - Credenciais inválidas')
            messages.error(self.request, 'Usuário ou senha inválidos.')
            return super().form_invalid(form)
        except:
            messages.error(self.request, 'Usuário ou senha inválidos.')
            return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """
    View customizada para logout com registro de evento.
    """
    next_page = 'index'

    def post(self, request, *args, **kwargs):
        """
        Registra evento de logout e adiciona mensagem de sucesso.
        """
        logger.info(f'Logout realizado para o usuário: {request.user.username}')
        messages.success(request, 'Logout realizado com sucesso!')
        return super().post(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'core/password/password_reset_form.html'
    email_template_name = 'core/password/password_reset_email.html'
    subject_template_name = 'core/password/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm

    def post(self, request, *args, **kwargs):
        print("\n=== Método POST de reset de senha chamado ===")
        print("POST data:", request.POST)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        print("\n=== Formulário Inválido ===")
        print("Erros:", form.errors)
        print("Dados:", form.cleaned_data)
        messages.error(self.request, "Por favor, verifique o email informado.")
        return super().form_invalid(form)

    def form_valid(self, form):
        print("\n=== Processando reset de senha ===")
        email = form.cleaned_data.get('email', '')
        print(f"Email informado: {email}")

        if not email:
            print("❌ Email não informado")
            return self.form_invalid(form)

        try:
            user = User.objects.get(email=email.lower().strip())
            print(f"✅ Usuário encontrado: {user.username}")

            context = {
                'user': user,
                'protocol': 'https' if self.request.is_secure() else 'http',
                'domain': self.request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            }

            subject = render_to_string(self.subject_template_name, context).strip()
            text_content = render_to_string(self.email_template_name, context)

            print("\n=== Enviando email ===")
            print(f"De: {settings.DEFAULT_FROM_EMAIL}")
            print(f"Para: {email}")
            print(f"Assunto: {subject}")

            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )

            print("✅ Email enviado com sucesso!")
            messages.success(
                self.request,
                "Email de recuperação enviado! Por favor, verifique sua caixa de entrada."
            )
            return super().form_valid(form)

        except User.DoesNotExist:
            print(f"❌ Usuário não encontrado para o email: {email}")
            messages.info(
                self.request,
                "Se existir uma conta com este email, você receberá as instruções por email."
            )
            return super().form_valid(form)

        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")
            print("\nDetalhes:")
            import traceback
            print(traceback.format_exc())
            messages.error(
                self.request,
                "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
            )
            return self.form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    View para página de confirmação de envio de reset de senha.
    """
    template_name = 'core/password/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    View para confirmação e alteração de nova senha.
    Inclui validação de histórico das últimas 3 senhas.
    """
    template_name = 'core/password/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def post(self, request, *args, **kwargs):
        """Processa a requisição POST para alteração de senha"""
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Registra alteração de senha bem-sucedida e salva no histórico.
        Verifica se a nova senha não está entre as últimas 3 utilizadas.
        """
        try:
            user = form.user
            password = form.cleaned_data.get('new_password1')

            # Verifica se a senha está no histórico
            if user.password_history:
                for old_password in user.password_history:
                    if check_password(password, old_password):
                        messages.error(self.request, PASSWORD_REUSE_ERROR)
                        logger.warning(f'Tentativa de reutilização de senha antiga para o usuário: {user.username}')
                        return self.form_invalid(form)

            # Se chegou aqui, a senha é válida
            user.save_password_to_history(password)

            logger.info(f'Senha alterada com sucesso para o usuário: {user.username}')
            messages.success(self.request, 'Sua senha foi alterada com sucesso!')
            return super().form_valid(form)

        except Exception as e:
            logger.error(f'Erro ao processar alteração de senha: {str(e)}')
            messages.error(self.request,
                           'Ocorreu um erro ao alterar sua senha. Por favor, tente novamente.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Registra erros na alteração de senha.
        """
        if not form.errors:
            # Se não houver erros específicos do formulário, mas chegou aqui
            # provavelmente é devido à validação de histórico
            return super().form_invalid(form)

        logger.warning(f'Erro na alteração de senha. Erros: {form.errors}')
        messages.error(self.request, 'Erro ao alterar a senha. Por favor, verifique os requisitos.')
        return super().form_invalid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    View para página final de reset de senha.
    """
    template_name = 'core/password/password_reset_complete.html'


class EmailVerificationView(View):
    """
    View para verificação de email do usuário.
    """

    def get(self, request, uidb64, token):
        """
        Processa verificação de email através de link único.

        Args:
            request: Requisição HTTP
            uidb64: UID codificado em base64
            token: Token de verificação
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.email_verified = True
                user.is_active = True  # Ativando o usuário
                user.email_verification_token = None
                user.save()
                messages.success(request, 'Email verificado com sucesso! Você já pode fazer login.')
                logger.info(f'Email verificado com sucesso para o usuário: {user.email}')
                return redirect('login')
            else:
                messages.error(request, 'O link de verificação é inválido ou expirou.')
                logger.warning(f'Tentativa de verificação com token inválido para o usuário: {user.email}')
                return redirect('index')

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, 'O link de verificação é inválido.')
            logger.error('Tentativa de verificação com token inválido')
            return redirect('index')


def send_verification_email(request, user):
    """
    Envia email de verificação para o usuário.

    Args:
        request: Requisição HTTP
        user: Usuário para envio de verificação

    Returns:
        bool: True se email enviado com sucesso, False caso contrário
    """
    try:
        # Gera token único para verificação
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        logger.info(f'Gerando token de verificação para usuário: {user.username}')

        # Prepara contexto para template de email
        context = {
            'user': user,
            'domain': request.get_host(),
            'protocol': 'https' if request.is_secure() else 'http',
            'uid': uid,
            'token': token,
        }

        # Configurações de email
        mail_subject = 'Ative sua conta na CG BookStore'
        html_message = render_to_string('core/email/email_verification.html', context)
        plain_message = strip_tags(html_message)

        # Salva token de verificação no usuário
        user.email_verification_token = token
        user.save()

        logger.info(f'Tentando enviar email para: {user.email}')

        # Envia email de verificação
        send_mail(
            subject=mail_subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f'Email de verificação enviado com sucesso para: {user.email}')
        return True

    except Exception as e:
        # Tratamento de erros de envio de email
        logger.error(f'Erro ao enviar email de verificação para {user.email}. Erro: {str(e)}')
        logger.error(f'Detalhes da configuração: EMAIL_BACKEND={settings.EMAIL_BACKEND}')
        return False