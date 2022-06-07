from django.urls import path
from .views import CardListView, CardDetailView


app_name = 'cards'      # пространство имен urlpatterns

urlpatterns = [
    path('list/', CardListView.as_view(), name='card_list'),
    path('detail/<slug:card_slug>', CardDetailView.as_view(), name='card_detail'),
]
