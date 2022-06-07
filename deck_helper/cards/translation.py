from modeltranslation.translator import register, TranslationOptions
from .models import Card, CardClass, Tribe, CardSet, Mechanic


@register(Card)
class CardTranslationOptions(TranslationOptions):
    fields = ('name', 'text', 'flavor')


@register(CardClass)
class CardClassTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Tribe)
class TribeTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(CardSet)
class CardSetTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Mechanic)
class MechanicTranslationOptions(TranslationOptions):
    fields = ('name',)
