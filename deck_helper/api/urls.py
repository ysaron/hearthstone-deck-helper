from django.urls import path
from . import views

app_name = 'api'


urlpatterns = [
    path('cards/', views.CardViewSet.as_view({'get': 'list'}), name='card_list'),
    path('cards/<int:dbf_id>/', views.CardViewSet.as_view({'get': 'retrieve'}), name='card_retrieve'),
    path('decks/', views.DeckListAPIView.as_view(), name='deck_list'),
    path('decks/<int:pk>/', views.DeckDetailAPIView.as_view(), name='deck_retrieve'),
    path('decode_deck/', views.DecodeDeckAPIView.as_view(), name='deck_decode'),
]
