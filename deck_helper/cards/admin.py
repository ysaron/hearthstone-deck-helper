from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Card, CardClass, Tribe, CardSet, Mechanic


@admin.register(Card)
class CardAdmin(TranslationAdmin):
    list_display = ('name', 'card_type', 'display_card_class', 'card_set', 'creation_date')
    list_filter = ('card_type', 'card_class', 'cost', 'collectible', 'card_set')
    fieldsets = (
        (
            'General',
            {
                'fields': (
                    ('name_en', 'name_ru', 'slug', 'collectible'),
                    ('card_id', 'dbf_id'),
                    ('image_en', 'image_ru', 'thumbnail'),
                )
            }
        ),
        (
            'Categories',
            {
                'fields': (
                    ('card_type', 'card_class'),
                    ('rarity', 'tribe'),
                    'card_set',
                )
            }
        ),
        (
            'Stats',
            {
                'fields': (
                    'cost',
                    ('attack', 'health', 'armor', 'durability'),
                )
            }
        ),
        (
            'Text',
            {
                'fields': (
                    'text',
                    'flavor',
                )
            }
        ),
        (
            None,
            {
                'fields': (
                    ('artist',),
                    ('mechanic',),
                )
            }
        ),
    )
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('card_id', 'dbf_id', 'collectible', 'artist', 'card_type', 'card_set')
    filter_horizontal = ('card_class', 'tribe')
    search_fields = ('name', 'card_set__name', 'text')
    save_on_top = True


@admin.register(CardClass)
class CardClassAdmin(TranslationAdmin):
    pass


@admin.register(Tribe)
class TribeAdmin(TranslationAdmin):
    pass


@admin.register(CardSet)
class CardSetAdmin(TranslationAdmin):
    pass


@admin.register(Mechanic)
class MechanicAdmin(TranslationAdmin):
    pass
