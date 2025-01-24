# apps/core/views/auth.py

import logging
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
from ..models import User

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
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

        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)

        logger.info(f'Login bem sucedido para o usuário: {user.username}')
        messages.success(self.request, 'Login realizado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
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
    next_page = 'index'

    def post(self, request, *args, **kwargs):
        logger.info(f'Logout realizado para o usuário: {request.user.username}')
        messages.success(request, 'Logout realizado com sucesso!')
        return super().post(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'core/password/password_reset_form.html'
    email_template_name = 'core/password/password_reset_email.html'
    subject_template_name = 'core/password/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        logger.info(f'Solicitação de reset de senha para o email: {form.cleaned_data["email"]}')
        messages.success(self.request,
                         'Se o email existir em nossa base, você receberá as instruções para redefinir sua senha.')
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f'Formulário de reset de senha inválido. Erros: {form.errors}')
        messages.error(self.request, 'Erro ao processar a solicitação. Por favor, verifique os dados informados.')
        return super().form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'core/password/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'core/password/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        logger.info('Senha alterada com sucesso')
        messages.success(self.request, 'Sua senha foi alterada com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f'Erro na alteração de senha. Erros: {form.errors}')
        messages.error(self.request, 'Erro ao alterar a senha. Por favor, verifique os requisitos.')
        return super().form_invalid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'core/password/password_reset_complete.html'


class EmailVerificationView(View):
    def get(self, request, uidb64, token):
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
    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        logger.info(f'Gerando token de verificação para usuário: {user.username}')

        context = {
            'user': user,
            'domain': request.get_host(),
            'protocol': 'https' if request.is_secure() else 'http',
            'uid': uid,
            'token': token,
        }

        mail_subject = 'Ative sua conta na CG BookStore'
        html_message = render_to_string('core/email/email_verification.html', context)
        plain_message = strip_tags(html_message)

        user.email_verification_token = token
        user.save()

        logger.info(f'Tentando enviar email para: {user.email}')

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
        logger.error(f'Erro ao enviar email de verificação para {user.email}. Erro: {str(e)}')
        logger.error(f'Detalhes da configuração: EMAIL_BACKEND={settings.EMAIL_BACKEND}')
        return False