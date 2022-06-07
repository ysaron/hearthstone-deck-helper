from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),                 # регистрация аккаунта
    path('activate/<uidb64>_<token>/', views.activate, name='activate'),    # активация аккаунта
    path('signin/', views.SignIn.as_view(), name='signin'),                 # авторизация
    path('signout/', views.signout_user, name='signout'),                   # выход из аккаунта
    path('change-password/', views.ChangePassword.as_view(), name='change_password'),
    path(
        'change-password-emailed/',
        views.ChangePasswordEmailed.as_view(),
        name='change_password_emailed',
    ),
    path(
        'change-password-confirm/<uidb64>_<token>/',
        views.ChangePasswordConfirm.as_view(),
        name='change_password_confirm',
    ),
    path(
        'change-password-complete/',
        views.ChangePasswordComplete.as_view(),
        name='change_password_complete',
    ),
]
