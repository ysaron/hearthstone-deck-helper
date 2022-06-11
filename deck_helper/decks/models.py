from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.urls.base import reverse_lazy
from django.contrib.auth.models import User

from cards.models import Card, CardClass
from core.exceptions import UnsupportedCards
from core.services.deck_codes import parse_deckstring


class IncluSionManager(models.QuerySet):

    def nameless(self):
        return self.filter(deck__name='')

    def named(self):
        return self.exclude(deck__name='')


class NamelessDeckManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(name='').prefetch_related('deck_class', 'deck_format')


class NamedDeckManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().exclude(name='').prefetch_related('deck_class', 'deck_format')


class Format(models.Model):
    """ Формат обычного режима игры Hearthstone """

    name = models.CharField(max_length=255, default=_('Unknown'), verbose_name=_('Name'))
    numerical_designation = models.PositiveSmallIntegerField(verbose_name=_('Format code'), default=0)

    objects = models.Manager()

    class Meta:
        verbose_name = _('Format')
        verbose_name_plural = _('Formats')

    def __str__(self):
        return 'unknown' if self.numerical_designation == 0 else self.name


class Deck(models.Model):
    """ Колода Hearthstone """

    name = models.CharField(max_length=255, default='', blank=True, verbose_name=_('Name'),
                            help_text=_('User-definable name'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='decks', null=True, blank=True,
                             verbose_name=_('User'))
    string = models.TextField(max_length=1500, verbose_name=_('Deck code'),
                              help_text=_('The string used to identify the cards that make up the deck.'))
    cards = models.ManyToManyField(Card, through='Inclusion', verbose_name=_('Cards'),
                                   help_text=_('The cards that make up the deck.'))
    deck_class = models.ForeignKey(CardClass, on_delete=models.CASCADE, related_name='decks', verbose_name=_('Class'),
                                   help_text=_('The class for which the deck is built.'))
    deck_format = models.ForeignKey(Format, on_delete=models.CASCADE,
                                    related_name='decks', verbose_name=_('Format'),
                                    help_text=_('The format for which the deck is intended.'))
    created = models.DateTimeField(default=now, verbose_name=_('Time of creation'))

    nameless = NamelessDeckManager()
    objects = models.Manager()
    named = NamedDeckManager()

    class Meta:
        verbose_name = _('Deck')
        verbose_name_plural = _('Decks')
        ordering = ['-created']

    def __str__(self):
        kinda_name = self.name if self.name else f'id_{self.pk}'
        return f'{kinda_name} ({self.deck_format}, {self.deck_class})'

    @classmethod
    def from_deckstring(cls, deckstring: str, *, named: bool = False):
        """ Создает экземпляр колоды из кода, сохраняет и возвращает его """

        # если точно такая же колода уже есть в БД - она же и возвращается вместо создания нового экземпляра
        nameless_deck = Deck.nameless.filter(string=deckstring)
        if not named and nameless_deck.exists():
            return nameless_deck.first()

        instance = cls()
        cards, heroes, format_ = parse_deckstring(deckstring)
        instance.deck_class = Card.objects.get(dbf_id=heroes[0]).card_class.all().first()
        instance.deck_format = Format.objects.get(numerical_designation=format_)
        instance.string = deckstring
        instance.save()
        for dbf_id, number in cards:
            try:
                card = Card.includibles.get(dbf_id=dbf_id)
            except Card.DoesNotExist:
                msg = _('No card data (id %(id)s)') % {'id': dbf_id}
                raise UnsupportedCards(msg)
            ci = Inclusion(deck=instance, card=card, number=number)
            ci.save()
            instance.cards.add(card)

        return instance

    @property
    def is_named(self):
        """ Возвращает True, если колода была сохранена пользователем """
        return self.name != '' and self.user is not None

    @property
    def included_cards(self):
        """ Queryset 'cards', дополненный данными о количестве экземпляров в колоде """

        decklist = self.cards.all().prefetch_related(
            'card_class',
            'tribe',
            'mechanic',
        ).select_related(
            'card_set',
        ).annotate(
            number=models.F('inclusions__number'),
        )
        return decklist.order_by('cost', 'name')

    def get_deckstring_form(self):
        """ Возвращает форму, используемую для копирования кода колоды """
        from .forms import DeckStringCopyForm  # импорт здесь во избежание перекрестного импорта
        return DeckStringCopyForm(initial={'deckstring': self.string})

    @property
    def craft_cost(self):
        """
        Возвращает суммарную стоимость (во внутриигровой валюте)
        создания карт из колоды (в обычном и золотом варианте)
        """
        craft_cost, craft_cost_gold = 0, 0
        rarities = Card.Rarities
        prices = {rarities.UNKNOWN: (0, 0),
                  rarities.NO_RARITY: (0, 0),
                  rarities.COMMON: (40, 400),
                  rarities.RARE: (100, 800),
                  rarities.EPIC: (100, 1600),
                  rarities.LEGENDARY: (1600, 3200)}
        for card in self.included_cards:
            craft_cost += prices[card.rarity][0] * card.number
            craft_cost_gold += prices[card.rarity][1] * card.number
        return {'basic': craft_cost, 'gold': craft_cost_gold}

    def __get_statistics(self, field: str) -> list[dict]:
        """
        Возвращает данные о количестве карт в колоде,
        соответствующих различным значением поля field
        """
        lst = []
        result = []
        for card in self.included_cards:
            try:
                data = getattr(card, field)
            except AttributeError:
                return []  # отразится в шаблоне как отсутствие данных

            if field == 'card_type':
                verbose_data = Card.CardTypes(data)
            elif field == 'rarity':
                verbose_data = Card.Rarities(data)
            else:
                verbose_data = data

            if verbose_data not in lst:
                lst.append(verbose_data)
                result.append({'name': verbose_data, 'data': data, 'num_cards': card.number})
            else:
                d = next(stat for stat in result if stat['name'] == verbose_data)
                d['num_cards'] += card.number

        return sorted(result, key=lambda stat: stat['num_cards'], reverse=True)

    @property
    def sets_statistics(self):
        """
        Возвращает данные о наборах карт, используемых в колоде,
        и о кол-ве карт каждого набора
        """
        return self.__get_statistics('card_set')

    @property
    def types_statistics(self):
        """ Возвращает данные о типах карт в колоде и кол-ве карт каждого типа """
        return self.__get_statistics('card_type')

    @property
    def rarity_statistics(self):
        """ Возвращает данные о редкостях карт в колоде и кол-ве карт каждой редкости """
        return self.__get_statistics('rarity')

    @property
    def mechanics_statistics(self):
        """
        Возвращает данные о механиках Hearthstone, использующихся
        картами колоды, и о кол-ве этих карт на каждую механику
        """
        mechanics = []
        result: list[dict] = []
        for card in self.included_cards:
            for mech in card.mechanic.all():
                if mech not in mechanics:
                    mechanics.append(mech)
                    result.append({'mech': mech, 'num_cards': card.number})
                else:
                    m = next(m for m in result if m['mech'] == mech)
                    m['num_cards'] += card.number

        result.sort(key=lambda mech_: mech_['num_cards'], reverse=True)
        return result

    def get_absolute_url(self):
        return reverse_lazy('decks:deck_detail', kwargs={'deck_id': self.pk})


class Inclusion(models.Model):
    """ Параметры вхождения карты в колоду (Intermediate Model) """
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='inclusions')
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='inclusions')
    number = models.PositiveSmallIntegerField(verbose_name=_('Amount'),
                                              help_text=_('The number of card inclusions in the deck.'))

    objects = IncluSionManager.as_manager()


class Render(models.Model):
    """ Детализированное изображение колоды """

    class Languages(models.TextChoices):
        ENGLISH = 'en', 'English'
        RUSSIAN = 'ru', 'Русский'

    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='renders', verbose_name=_('Deck'))
    render = models.ImageField(verbose_name=_('Render'), upload_to='decks/', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_('Name'), default='', blank=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Time of creation'))
    language = models.CharField(max_length=2, choices=Languages.choices, default=Languages.ENGLISH)

    objects = models.Manager()
