from django.contrib import admin

from .models import HearthstoneState


@admin.register(HearthstoneState)
class StateAdmin(admin.ModelAdmin):
    pass
