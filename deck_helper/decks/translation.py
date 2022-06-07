from modeltranslation.translator import register, TranslationOptions
from .models import Format


@register(Format)
class FormatTranslationOptions(TranslationOptions):
    fields = ('name',)
