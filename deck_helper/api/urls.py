from django.urls import path
from . import views

app_name = 'api'


urlpatterns = [
    path('cards/', views.CardViewSet.as_view({'get': 'list'})),
    path('cards/<int:dbf_id>/', views.CardViewSet.as_view({'get': 'retrieve'})),
    path('decks/', views.DeckListAPIView.as_view()),
    path('decks/<int:pk>/', views.DeckDetailAPIView.as_view()),
    path('decode_deck/', views.DecodeDeckAPIView.as_view()),
]
