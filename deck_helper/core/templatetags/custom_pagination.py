from django import template

register = template.Library()


@register.inclusion_tag('core/tags/pagination.html', takes_context=True, name='formatted_pages')
def page_formatter(context, adjacent_pages: int = 3):
    """
    Кастомный включающий тег шаблона для улучшения пагинации
    :param context: контекст
    :param adjacent_pages: кол-во отображаемых соседних страниц
    :return: переменные контекста для отображения первой, последней и соседних страниц по отношению к текущей
    """
    page = context.get('page_obj')
    paginator = context.get('paginator')

    # Определение соседних страниц (по отношению к текущей)
    first_adj_page = max(page.number - adjacent_pages, 1)
    if first_adj_page <= 3:
        first_adj_page = 1
    last_adj_page = page.number + adjacent_pages + 1
    if last_adj_page >= paginator.num_pages - 1:
        last_adj_page = paginator.num_pages + 1
    adjacent_pages = [n for n in range(first_adj_page, last_adj_page) if n <= paginator.num_pages]

    context.update({'adjacent_pages': adjacent_pages,
                    'show_first': 1 not in adjacent_pages,  # флаг: показывать ли первую страницу отдельно
                    'show_last': paginator.num_pages not in adjacent_pages})

    return context
