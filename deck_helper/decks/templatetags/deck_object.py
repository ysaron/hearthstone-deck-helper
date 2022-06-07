from django import template

register = template.Library()


@register.inclusion_tag('decks/tags/deck-accordion.html', takes_context=True, name='deck_obj')
def deck_accordion(context, deck):
    context.update({'deck': deck})
    return context
