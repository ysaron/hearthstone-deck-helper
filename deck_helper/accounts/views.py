from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import generic

from .forms import RegisterUserForm, LoginUserForm
from .tokens import account_activation_token


class SignUp(generic.CreateView):
    """ Создание нового пользователя """
    form_class = RegisterUserForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:signin')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'title': _('Registration')}
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        site = get_current_site(self.request)
        mail_subject = _('Account activation | Hearthstone Deck Helper')
        message = render_to_string(template_name='accounts/acc_active_email.html',
                                   context={'user': user,
                                            'domain': site.domain,
                                            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                                            'token': account_activation_token.make_token(user)})
        to_email = form.cleaned_data.get('email')
        email = EmailMessage(subject=mail_subject,
                             body=message,
                             to=[to_email])
        email.content_subtype = 'html'
        email.send()

        return render(request=self.request,
                      context={'title': _('Check your email')},
                      template_name='accounts/acc_active_done.html')


def activate(request, uidb64, token):
    """ Активация аккаунта юзера после перехода по ссылке в email """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request,
                      context={'title': _('The account is activated')},
                      template_name='accounts/acc_active_complete.html')

    return render(request,
                  context={'title': _('Activation has failed')},
                  template_name='accounts/acc_active_complete.html')


class SignIn(auth_views.LoginView):
    """ Авторизация зарегистрированного пользователя """
    form_class = LoginUserForm
    template_name = 'accounts/signin.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'title': _('Authorization')}
        return context

    def get_success_url(self):
        if next_url := self.request.GET.get('next'):
            return next_url
        return reverse_lazy('home')


def signout_user(request):
    """ Выход из учетной записи """
    logout(request)
    return redirect(reverse_lazy('accounts:signin'))


class ChangePassword(auth_views.PasswordResetView):
    """ Запрос email для отправки инструкций по смене пароля """
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:change_password_emailed')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'title': _('Change password'),
                    'label': _('Email')}
        return context


class ChangePasswordEmailed(auth_views.PasswordResetDoneView):
    """ Уведомление об отправке инструкций """
    template_name = 'accounts/password_reset_done.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'title': _('Check your email')}
        return context


class ChangePasswordConfirm(auth_views.PasswordResetConfirmView):
    """ Задание нового пароля """
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:change_password_complete')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'title': _('New password')}
        return context


class ChangePasswordComplete(auth_views.PasswordResetCompleteView):
    """ Уведомление о смене пароля """
    template_name = 'accounts/password_reset_complete.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {'title': _('The password has been changed')}
        return context
