from django_filters import compat, RangeFilter, DateTimeFromToRangeFilter
from django_filters.rest_framework import DjangoFilterBackend as BaseDjangoFilterBackend
import warnings


class DjangoFilterBackend(BaseDjangoFilterBackend):
    """ Обеспечивает совместимость RangeFilter с drf-yasg """

    def get_schema_fields(self, view):
        assert compat.coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert compat.coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'

        try:
            queryset = view.get_queryset()
        except Exception as e:
            queryset = None
            warnings.warn(
                f'{view.__class__} is not compatible with schema generation ({e.__class__.__name__}: {e})'
            )

        filterset_class = self.get_filterset_class(view, queryset)

        if not filterset_class:
            return []

        schema_fields = []
        for field_name, field in filterset_class.base_filters.items():
            if type(field) == RangeFilter:
                coreapi_field_names = [f'{field_name}_min', f'{field_name}_max']
            elif type(field) == DateTimeFromToRangeFilter:
                coreapi_field_names = [f'{field_name}_after', f'{field_name}_before']
            else:
                coreapi_field_names = [field_name]
            for f in coreapi_field_names:
                schema_fields.append(
                    compat.coreapi.Field(
                        name=f,
                        required=field.extra['required'],
                        location='query',
                        schema=self.get_coreschema_field(field),
                        description=None,
                        type=None,
                        example=None,
                    )
                )

        return schema_fields


def generate_choicefield_description(model, enum_choice: str) -> str:
    """
    Возвращает описание полей с выбором вариантов для генератора документации к API

    :param model: фильтруемая модель
    :param enum_choice: строка с именем подкласса django.db.models.TextChoices
    """
    enum_choices = getattr(model, enum_choice, None)
    if not enum_choices:
        return 'Description is not provided'
    choices = enum_choices.choices
    choices = '\n'.join([f'value: {val}, description: {desc}' for val, desc in choices if val])
    return choices
