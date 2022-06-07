from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from random import choice

from .models import Deck
from .forms import DeckstringForm, DeckFilterForm, DeckSaveForm
from core.services.deck_codes import get_clean_deckstring
from core.services.deck_utils import find_similar_decks, get_render
from core.exceptions import DecodeError, UnsupportedCards


def create_deck(request: HttpRequest):
    """ Расшифровка кода колоды; ее отображение """

    deck, deckstring_form, deck_save_form = None, None, None
    title = _('Decoding')

    if request.method == 'POST':
        if 'deckstring' in request.POST:        # код колоды отправлен с формы DeckstringForm
            deckstring_form = DeckstringForm(request.POST)
            if deckstring_form.is_valid():
                try:
                    deckstring = deckstring_form.cleaned_data['deckstring']
                    deckstring = get_clean_deckstring(deckstring)
                    with transaction.atomic():
                        deck = Deck.from_deckstring(deckstring)
                        deck_name_init = f'{deck.deck_class}-{deck.pk}'
                        deck_save_form = DeckSaveForm(initial={'string_to_save': deckstring,
                                                               'deck_name': deck_name_init})
                        title = deck
                except DecodeError as de:
                    msg = _('Error: %(error)s') % {'error': de}
                    deckstring_form.add_error(None, msg)
                except UnsupportedCards as u:
                    msg = _('%(error)s. The database will be updated shortly.') % {'error': u}
                    deckstring_form.add_error(None, msg)
        if 'deck_name' in request.POST:         # название колоды отправлено с формы DeckSaveForm
            deck = Deck.from_deckstring(request.POST['string_to_save'], named=True)
            deck.user = request.user
            deck.name = request.POST['deck_name']
            deck.save()
            return redirect(deck)
    else:
        deckstring_form = DeckstringForm()

    context = {'title': title,
               'deckstring_form': deckstring_form,
               'deck_save_form': deck_save_form,
               'deck': deck,
               'similar': find_similar_decks(deck)}

    return render(request, template_name='decks/deck_detail.html', context=context)


def get_random_deckstring(request: HttpRequest):
    """ AJAX-view для получения случайного кода колоды из базы """
    if request.GET.get('deckstring') == 'random' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        deck = choice(Deck.nameless.all())
        response = {'deckstring': deck.string}
        return JsonResponse(response)

    return redirect(reverse_lazy('decks:index'))


def get_deck_render(request: HttpRequest):
    """ AJAX-view для получения рендера колоды """
    if all([
        request.GET.get('render'),
        deck_id := request.GET.get('deck_id'),
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest',
    ]):
        response = get_render(deck_id, name=request.GET.get('name'), language=request.GET.get('language'))
        return JsonResponse(response)

    return redirect(reverse_lazy('decks:index'))


class NamelessDecksListView(generic.ListView):
    """ Вывод списка всех имеющихся в базе уникальных колод """
    model = Deck
    context_object_name = 'decks'
    template_name = 'decks/deck_list.html'
    paginate_by = 18

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        search_initial_values = {'deck_class': self.request.GET.get('deck_class', ''),
                                 'deck_format': self.request.GET.get('deck_format', '')}

        context |= {'title': _('Decks'),
                    'form': DeckFilterForm(initial=search_initial_values)}
        return context

    def get_queryset(self):
        deck_class = self.request.GET.get('deck_class')
        deck_format = self.request.GET.get('deck_format')

        object_list = self.model.nameless.all()
        if deck_class:
            object_list = object_list.filter(deck_class=deck_class)
        if deck_format:
            object_list = object_list.filter(deck_format=deck_format)

        return object_list


class UserDecksListView(LoginRequiredMixin, generic.ListView):
    """ Вывод списка сохраненных текущим пользователем колод """

    model = Deck
    context_object_name = 'decks'
    template_name = 'decks/deck_list.html'
    paginate_by = 18
    login_url = '/accounts/signin/'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        search_initial_values = {'deck_class': self.request.GET.get('deck_class', ''),
                                 'deck_format': self.request.GET.get('deck_format', '')}

        context |= {'title': _('Decks'),
                    'form': DeckFilterForm(initial=search_initial_values)}
        return context

    def get_queryset(self):

        deck_class = self.request.GET.get('deck_class')
        deck_format = self.request.GET.get('deck_format')

        object_list = self.model.named.filter(user=self.request.user)
        if deck_class:
            object_list = object_list.filter(deck_class=deck_class)
        if deck_format:
            object_list = object_list.filter(deck_format=deck_format)

        return object_list


def deck_view(request, deck_id):
    """ Просмотр конкретной колоды """

    deck = Deck.objects.get(id=deck_id)
    deck_name_init = '' if deck.is_named else f'{deck.deck_class}-{deck.pk}'
    deck_save_form = DeckSaveForm(initial={'string_to_save': deck.string, 'deck_name': deck_name_init})

    # --- Ограничение доступа к именованным колодам ------------------------
    if deck.is_named:
        if not request.user.is_authenticated or deck.user != request.user:
            raise PermissionDenied()

    if request.method == 'POST':
        if deck.is_named:
            # доступно переименование и удаление колоды
            if new_name := request.POST['deck_name'].strip():
                deck.name = new_name
                deck.save()
        else:
            # доступно сохранение колоды (т.е. создание именованного экземпляра той же колоды)
            deck_to_save = Deck.from_deckstring(request.POST['string_to_save'], named=True)
            deck_to_save.user = request.user
            deck_to_save.name = request.POST['deck_name']
            deck_to_save.save()
            return redirect(deck_to_save)

    context = {'title': deck,
               'deck': deck,
               'deck_save_form': deck_save_form,
               'similar': find_similar_decks(deck)}

    return render(request, template_name='decks/deck_detail.html', context=context)


class DeckDelete(SuccessMessageMixin, generic.DeleteView):

    model = Deck
    pk_url_kwarg = 'deck_id'
    success_url = reverse_lazy('decks:user_decks')
    success_message = _('Deck has been removed')

    def get_queryset(self):
        return self.model.named.all()

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message % obj.__dict__)
        return super(DeckDelete, self).delete(request, *args, **kwargs)
