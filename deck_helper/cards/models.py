from django.db import models
from django.db.models import Model, Manager, QuerySet, Q
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class CardQuerySet(QuerySet):

    def search_by_name(self, name):
        return self.filter(name__icontains=name)

    def search_by_rarity(self, rarity):
        return self.filter(rarity=rarity)

    def search_collectible(self, is_collectible: bool):
        return self.filter(collectible=is_collectible)

    def search_by_type(self, type_):
        return self.filter(card_type=type_)

    def search_by_tribe(self, tribe):
        try:
            supertribe = Tribe.objects.get(service_name='All')
            return self.filter(Q(tribe=tribe) | Q(tribe=supertribe))
        except Tribe.DoesNotExist:
            return self.filter(tribe=tribe)

    def search_by_class(self, class_):
        return self.filter(card_class=class_)

    def search_by_set(self, set_):
        return self.filter(card_set=set_)

    def search_by_mechanic(self, mechanic):
        return self.filter(mechanic=mechanic)


class IncludibleCardManager(Manager):
    """ Доступ к картам, которые можно включить в колоду """

    def get_queryset(self):
        return super().get_queryset().filter(Q(collectible=True) & ~Q(card_set__service_name='Hero Skins'))


class CardClass(Model):
    """ Модель игрового класса (Маг, Паладин и т.д.) """

    name = models.CharField(max_length=255, verbose_name=_('Name'))
    service_name = models.CharField(max_length=255, verbose_name='Service', default='', help_text='(!)',
                                    unique=True)
    collectible = models.BooleanField(default=False, verbose_name=_('Collectible'))
    image = models.ImageField(verbose_name=_('Image'), upload_to='classes/', null=True, blank=True)

    objects = Manager()

    class Meta:
        verbose_name = _('Class')
        verbose_name_plural = _('Classes')

    def __str__(self):
        return self.name if self.collectible else f'[{self.name}]'


class Tribe(Model):
    """ Модель расы (мурлок, демон и т.д.) """

    name = models.CharField(max_length=255, verbose_name=_('Name'))
    service_name = models.CharField(max_length=255, verbose_name='Service', default='', help_text='(!)',
                                    unique=True)

    objects = Manager()

    class Meta:
        verbose_name = _('Tribe')
        verbose_name_plural = _('Tribes')

    def __str__(self):
        return self.name


class CardSet(Model):
    """ Модель набора карт Hearthstone """
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    service_name = models.CharField(max_length=255, verbose_name='Service', default='', help_text='(!)', blank=True)
    set_format = models.ForeignKey('decks.Format', on_delete=models.CASCADE,
                                   related_name='sets', verbose_name=_('Format'))

    objects = Manager()

    class Meta:
        verbose_name = _('Set')
        verbose_name_plural = _('Sets')

    def __str__(self):
        return self.name


class Mechanic(Model):
    """ Модель механики карт """
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    service_name = models.CharField(max_length=255, verbose_name='Service', default='', help_text='(!)', blank=True)
    hidden = models.BooleanField(default=False, verbose_name=_('Hidden'))

    objects = Manager()

    class Meta:
        verbose_name = _('Mechanic')
        verbose_name_plural = _('Mechanics')

    def __str__(self):
        return self.name


class BaseCard(Model):
    """ Абстрактная модель карты Hearthstone """

    class CardTypes(models.TextChoices):
        UNKNOWN = '', _('---------')
        MINION = 'M', _('Minion')
        SPELL = 'S', _('Spell')
        HERO = 'H', _('Hero')
        WEAPON = 'W', _('Weapon')
        HEROPOWER = 'HP', _('Hero power')

    class Rarities(models.TextChoices):
        UNKNOWN = '', _('---------')
        NO_RARITY = 'NO', _('No rarity')
        COMMON = 'C', _('Common')
        RARE = 'R', _('Rare')
        EPIC = 'E', _('Epic')
        LEGENDARY = 'L', _('Legendary')

    class SpellSchools(models.TextChoices):
        UNKNOWN = '', _('---------')
        HOLY = 'H', _('Holy')
        SHADOW = 'SH', _('Shadow')
        NATURE = 'N', _('Nature')
        FEL = 'F', _('Fel')
        FIRE = 'FI', _('Fire')
        FROST = 'FR', _('Frost')
        ARCANE = 'A', _('Arcane')

    name = models.CharField(max_length=255, verbose_name=_('Name'))
    service_name = models.CharField(max_length=255, default='')
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name='URL')
    card_type = models.CharField(max_length=2, choices=CardTypes.choices, default=CardTypes.UNKNOWN,
                                 verbose_name=_('Type'))
    card_class = models.ManyToManyField(CardClass, verbose_name=_('Class'))
    cost = models.SmallIntegerField(blank=True, null=True, default=0, verbose_name=_('Mana cost'),
                                    validators=[MinValueValidator(0)])
    attack = models.SmallIntegerField(blank=True, null=True, default=0, verbose_name=_('Attack'),
                                      help_text=_('For minions and weapons only.'),
                                      validators=[MinValueValidator(0)])
    health = models.SmallIntegerField(blank=True, null=True, default=0, verbose_name=_('Health'),
                                      help_text=_('For minions only.'),
                                      validators=[MinValueValidator(0)])
    durability = models.SmallIntegerField(blank=True, null=True, default=0, verbose_name=_('Durability'),
                                          help_text=_('For weapons only.'),
                                          validators=[MinValueValidator(0)])
    armor = models.SmallIntegerField(blank=True, null=True, default=0, verbose_name=_('Armor'),
                                     help_text=_('For hero cards only.'),
                                     validators=[MinValueValidator(0)])
    text = models.TextField(max_length=1000, blank=True, default='', verbose_name=_('Text'),
                            help_text=_('The text of the card that defines its properties.'))
    flavor = models.TextField(max_length=1000, blank=True, default='', verbose_name=_('Flavor'),
                              help_text=_('Free text.'))
    rarity = models.CharField(max_length=2, choices=Rarities.choices, verbose_name=_('Rarity'),
                              default=Rarities.UNKNOWN)
    tribe = models.ManyToManyField(Tribe, blank=True, verbose_name=_('Tribe'), help_text=_('For creatures only.'))
    spell_school = models.CharField(max_length=2, choices=SpellSchools.choices, default=SpellSchools.UNKNOWN,
                                    verbose_name=_('Spell school'), blank=True, help_text=_('For spells only.'))
    creation_date = models.DateTimeField(null=True, blank=True, auto_now_add=True,
                                         verbose_name=_('Date of creation'))
    battlegrounds = models.BooleanField(default=False, verbose_name=_('Battlegrounds card'))
    mercenaries = models.BooleanField(default=False, verbose_name=_('Mercenaries card'))
    mechanic = models.ManyToManyField(Mechanic, blank=True, verbose_name=_('Mechanics'),
                                      help_text=_('Card mechanics'))

    class Meta:
        abstract = True

    def display_card_class(self):
        """
        Создает строку для поля card_class.
        Необходимо для отображения поля типа ManyToMany в списке в админ-панели
        """
        return ', '.join([cardclass.name for cardclass in self.card_class.all()])

    display_card_class.short_description = _('Class')


class Card(BaseCard):
    """ Модель карты Hearthstone """

    dbf_id = models.IntegerField(primary_key=True, unique=True, help_text=_('Integer ID of an existing card'))
    card_id = models.CharField(max_length=255, default='', help_text=_('String ID of an existing card'))
    card_set = models.ForeignKey(CardSet, on_delete=models.SET_NULL, null=True, verbose_name=_('Set'),
                                 related_name='cardsets')
    artist = models.CharField(max_length=255, blank=True, verbose_name=_('Artist'))
    collectible = models.BooleanField(default=True, verbose_name=_('Collectible'))

    image_en = models.ImageField(verbose_name=_('Image (enUS)'), help_text=_('Rendered card image (en)'),
                                 upload_to='cards/en/', null=True, blank=True)
    image_ru = models.ImageField(verbose_name=_('Image (ruRU)'), help_text=_('Rendered card image (ru)'),
                                 upload_to='cards/ru/', null=True, blank=True)
    thumbnail = models.ImageField(verbose_name=_('Thumbnail'), help_text=_('Card thumbnail to display in the deck'),
                                  upload_to='cards/thumbnails/', null=True, blank=True)

    objects = CardQuerySet.as_manager()
    includibles = IncludibleCardManager()

    class Meta:
        verbose_name = _('Hearthstone card')
        verbose_name_plural = _('Hearthstone cards')
        ordering = ['-cost']

    def __str__(self):
        return self.name if self.collectible else f'[{self.name}]'

    def get_absolute_url(self):
        return reverse_lazy('cards:card_detail', kwargs={'card_slug': self.slug})
