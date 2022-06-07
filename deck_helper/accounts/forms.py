from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class RegisterUserForm(auth_forms.UserCreationForm):

    email = forms.EmailField(label=_('Email'),
                             widget=forms.EmailInput(attrs={'class': 'form-input'}))
    username = forms.CharField(label=_('Nickname'),
                               widget=forms.TextInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label=_('Password'),
                                widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label=_('Password (again)'),
                                widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if email != settings.TEST_EMAIL and User.objects.filter(email=email).exists():
            msg = _('Email %(email)s already registered.') % {'email': email}
            raise ValidationError(msg)
        return email


class LoginUserForm(auth_forms.AuthenticationForm):

    username = forms.CharField(label=_('Nickname'), widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={'class': 'form-input'}))
