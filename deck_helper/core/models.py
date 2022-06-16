from django.db import models
from django.utils.translation import gettext_lazy as _


class SingletonModel(models.Model):

    objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class HearthstoneState(SingletonModel):
    """ Используется для отслеживания обновлений игры """
    version = models.CharField(max_length=255, default='0.0.0',
                               verbose_name=_('Version'), help_text=_('Current HS version'))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_('Last update time'))
    success = models.BooleanField(default=False, verbose_name=_('Updated successfully'),
                                  help_text=_('Whether the last update was successful'))

    def __str__(self):
        success = 'OK' if self.success else '!!!'
        return f'v{self.version} | {self.last_updated:%d.%m.%Y} ({success})'

    def __eq__(self, other):
        if not isinstance(other, str):
            raise TypeError(f'HearthstoneState сравнивается с типом {type(other)} '
                            f'(допустимые типы: str)')

        if any(not part.isdigit() for part in other.split('.')):
            raise ValueError(f'HearthstoneState сравнивается с некорректной строкой: {other}')

        if len(other.split('.')) < 3:
            raise ValueError(f'HearthstoneState сравнивается с некорректной строкой: {other}')

        significant_self = '.'.join(str(self.version).split('.')[:3])
        significant_other = '.'.join(other.split('.')[:3])
        return significant_self == significant_other
