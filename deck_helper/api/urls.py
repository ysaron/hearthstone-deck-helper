from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'api'

card_router = routers.SimpleRouter()
card_router.register(r'cards', views.CardViewSet, basename='cards')

deck_router = routers.SimpleRouter()
deck_router.register(r'decks', views.DeckViewSet, basename='decks')

urlpatterns = [
    path('', include(card_router.urls)),
    path('', include(deck_router.urls)),
]
