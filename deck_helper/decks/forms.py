from django import forms
from django.utils.translation import gettext_lazy as _

from cards.models import CardClass
from .models import Format


class DeckstringForm(forms.Form):
    # max_length=1500, т.к. такой длины могут быть коды колод непосредственно из клиента игры
    deckstring = forms.CharField(max_length=1500, label=_('Deckstring'), widget=forms.TextInput)
    deckstring.widget.attrs.update({'class': 'form-input',
                                    'id': 'form-deckstring',
                                    'placeholder': _('Deck code')})


class DeckStringCopyForm(forms.Form):
    """ Форма, показываемая при невозможности копирования кода через navigator.clipboard """
    deckstring = forms.CharField(max_length=30)
    deckstring.widget.attrs.update({'class': 'deck-control-element'})


class DeckSaveForm(forms.Form):
    deck_name = forms.CharField(max_length=30, label=_('Name'), required=False)
    string_to_save = forms.CharField(max_length=255)

    deck_name.widget.attrs.update({'class': 'deck-control-element', 'placeholder': _('Name')})
    string_to_save.widget.attrs.update({'style': 'display: none;', 'id': 'deckstringData'})


class DeckFilterForm(forms.Form):
    CARD_CLASSES = CardClass.objects.filter(collectible=True).exclude(service_name='Neutral')
    deck_class = forms.ModelChoiceField(queryset=CARD_CLASSES, required=False, label=_('Class'))

    FORMATS = Format.objects.exclude(numerical_designation=0)
    deck_format = forms.ModelChoiceField(queryset=FORMATS, required=False, label=_('Format'))

    deck_class.widget.attrs.update({'class': 'form-input'})
    deck_format.widget.attrs.update({'class': 'form-input'})
