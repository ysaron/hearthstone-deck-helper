from django_filters import rest_framework as filters

from cards.models import Card, CardClass, CardSet
from decks.models import Deck, Format
from .utils import generate_choicefield_description as gcd


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    BaseInFilter - валидация разделенных запятыми входящих значений
    CharFilter - фильтрация по тексту (по умолчанию фильтрация по id)
    """
    pass


class CardFilter(filters.FilterSet):

    card_id = filters.CharFilter()
    dbf_id = filters.NumberFilter()
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    classes = CharInFilter(field_name='card_class__name', lookup_expr='in', help_text='Comma-separated class names')
    ctype = filters.ChoiceFilter(field_name='card_type', choices=Card.CardTypes.choices,
                                 help_text=gcd(Card, 'CardTypes'))
    cset = filters.ModelChoiceFilter(queryset=CardSet.objects.all(), field_name='card_set', to_field_name='name',
                                     help_text='Card Set name')
    rarity = filters.ChoiceFilter(choices=Card.Rarities.choices, help_text=gcd(Card, 'Rarities'))
    cost = filters.RangeFilter()
    attack = filters.RangeFilter()
    health = filters.RangeFilter()
    armor = filters.RangeFilter()
    durability = filters.RangeFilter()

    class Meta:
        model = Card
        fields = ('card_id', 'dbf_id', 'name', 'classes', 'ctype', 'cset', 'rarity', 'cost', 'attack', 'health',
                  'durability', 'armor')


class DeckFilter(filters.FilterSet):

    dclass = filters.ModelChoiceFilter(queryset=CardClass.objects.filter(collectible=True),
                                       field_name='deck_class', to_field_name='name', help_text='Class name')
    dformat = filters.ModelChoiceFilter(queryset=Format.objects.all(),
                                        field_name='deck_format', to_field_name='name', help_text='Format name')
    date = filters.DateTimeFromToRangeFilter(field_name='created', help_text='Creation date (dd.mm.yyyy)')
    cards = filters.CharFilter(field_name='cards', method='filter_decks_by_cards',
                               help_text='Comma-separated "dbf_id" values')

    class Meta:
        model = Deck
        fields = ('dformat', 'dclass', 'date', 'cards')

    def filter_decks_by_cards(self, queryset, name, value):
        """ Позволяет фильтровать колоды по картам, указывая их dbf_id через запятую """

        for dbf_id in value.split(","):
            queryset = queryset.filter(cards__dbf_id=dbf_id)

        return queryset
