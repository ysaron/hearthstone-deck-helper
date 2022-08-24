from django.views import generic
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

from .models import Card
from .forms import CardSearchFilterForm
from core.mixins import CacheMixin


class CardListView(CacheMixin, generic.ListView):
    """ Список карт Hearthsone """
    model = Card
    context_object_name = 'cards'
    template_name = 'cards/card_list.html'
    paginate_by = 100

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        prev_values = {'name': self.request.GET.get('name', ''),
                       'rarity': self.request.GET.get('rarity', ''),
                       'collectible': self.request.GET.get('collectible', ''),
                       'card_type': self.request.GET.get('card_type', ''),
                       'tribe': self.request.GET.get('tribe', ''),
                       'card_class': self.request.GET.get('card_class', ''),
                       'card_set': self.request.GET.get('card_set', ''),
                       'mechanic': self.request.GET.get('mechanic')}

        context |= {'title': _('Hearthstone cards'),
                    'form': CardSearchFilterForm(initial=prev_values)}
        return context

    def get_queryset(self):
        """ Реализация динамического поиска по картам """
        name = self.request.GET.get('name')
        rarity = self.request.GET.get('rarity')

        collectible_raw = self.request.GET.get('collectible', 'unknown')
        collectible = {
            'unknown': None,
            'true': True,
            'false': False,
        }.get(collectible_raw)

        card_type = self.request.GET.get('card_type')
        tribe = self.request.GET.get('tribe')
        card_class = self.request.GET.get('card_class')
        card_set = self.request.GET.get('card_set')
        mechanic = self.request.GET.get('mechanic')

        # Оптимизация: вместо множества SQL-запросов - один сложный
        object_list = self.model.objects.prefetch_related('card_set', 'tribe', 'card_class', 'mechanic')

        if name:
            object_list = object_list.search_by_name(name)
        if rarity:
            object_list = object_list.search_by_rarity(rarity)
        if collectible is not None:
            object_list = object_list.search_collectible(collectible)
            if collectible:
                object_list = object_list.exclude(card_set__service_name='Hero Skins')
        if card_type:
            object_list = object_list.search_by_type(card_type)
        if tribe:
            object_list = object_list.search_by_tribe(tribe)
        if card_class:
            object_list = object_list.search_by_class(card_class)
        if card_set:
            object_list = object_list.search_by_set(card_set)
        if mechanic:
            object_list = object_list.search_by_mechanic(mechanic)
        return object_list


class CardDetailView(CacheMixin, generic.DetailView):
    """ Детальная информация о карте Hearthstone """
    model = Card
    slug_url_kwarg = 'card_slug'
    context_object_name = 'card'
    template_name = 'cards/card_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inclusions = self.object.inclusions.nameless().order_by('-deck__created')
        paginator = Paginator(inclusions, 9)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context |= {
            'title': context['object'],
            'c_types': Card.CardTypes,
            'paginator': paginator,
            'page_obj': page_obj,
        }
        return context
