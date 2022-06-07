from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .services.statistics import get_statistics_context


def contact(request: HttpRequest):
    if request.GET.get('email') and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        response = {'email': settings.EMAIL_HOST_USER}
        return JsonResponse(response)

    return redirect(reverse_lazy('decks:index'))


def statistics(request: HttpRequest):
    context = {
        'title': _('Statistics'),
        'statistics': get_statistics_context(),
    }
    return render(request=request, template_name='core/statistics.html', context=context)


def api_greeting(request: HttpRequest):
    context = {'title': 'API'}
    return render(request, template_name='core/api.html', context=context)
