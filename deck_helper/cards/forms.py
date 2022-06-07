from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Card, CardClass, Tribe, CardSet, Mechanic


class CardSearchFilterForm(forms.Form):
    """ Форма фильтрации и поиска карт Hearthstone """
    name = forms.CharField(required=False, label=_('Name'))

    collectible = forms.NullBooleanField(required=False, label=_('Collectible'))

    CARD_TYPES = Card.CardTypes.choices
    card_type = forms.ChoiceField(choices=CARD_TYPES, required=False, label=_('Type'))

    CARD_CLASSES = CardClass.objects.all()
    card_class = forms.ModelChoiceField(queryset=CARD_CLASSES, required=False, label=_('Class'))

    CARD_SETS = CardSet.objects.all()
    card_set = forms.ModelChoiceField(queryset=CARD_SETS, required=False, label=_('Set'))

    RARITIES = Card.Rarities.choices
    rarity = forms.ChoiceField(choices=RARITIES, required=False, label=_('Rarity'))

    TRIBES = Tribe.objects.all()
    tribe = forms.ModelChoiceField(queryset=TRIBES, required=False, label=_('Tribe'))

    MECHANICS = Mechanic.objects.filter(hidden=False)
    mechanic = forms.ModelChoiceField(queryset=MECHANICS, required=False, label=_('Mechanics'))

    name.widget.attrs.update({'class': 'form-input', 'placeholder': _('Enter card name')})
    rarity.widget.attrs.update({'class': 'form-input'})
    collectible.widget.attrs.update({'class': 'form-input'})
    card_type.widget.attrs.update({'class': 'form-input'})
    tribe.widget.attrs.update({'class': 'form-input'})
    card_class.widget.attrs.update({'class': 'form-input'})
    card_set.widget.attrs.update({'class': 'form-input'})
    mechanic.widget.attrs.update({'class': 'form-input'})
