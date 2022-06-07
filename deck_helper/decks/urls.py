from django.urls import path
from . import views


app_name = 'decks'

urlpatterns = [
    path('', views.create_deck, name='index'),
    path('all/', views.NamelessDecksListView.as_view(), name='all_decks'),
    path('my/', views.UserDecksListView.as_view(), name='user_decks'),
    path('<int:deck_id>', views.deck_view, name='deck_detail'),
    path('<int:deck_id>/delete', views.DeckDelete.as_view(), name='deck_delete'),
    path('get_render/', views.get_deck_render, name='deck_render'),
    path('random_deckstring/', views.get_random_deckstring, name='get_random_deckstring'),
]
