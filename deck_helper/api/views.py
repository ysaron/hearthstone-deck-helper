from rest_framework import viewsets, mixins

from . import serializers
from .services.filters import CardFilter, DeckFilter
from .services.utils import DjangoFilterBackend
from cards.models import Card
from decks.models import Deck


class CardViewSet(viewsets.ReadOnlyModelViewSet):
    """ Getting Hearthstone cards """
    queryset = Card.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CardFilter
    lookup_field = 'dbf_id'

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.CardListSerializer
        elif self.action == 'retrieve':
            return serializers.CardDetailSerializer


class DeckViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = DeckFilter

    def get_serializer_class(self):
        match self.action:
            case 'list':
                return serializers.DeckListSerializer
            case 'create':
                return serializers.DeckCreateSerializer
            case _:
                return serializers.DeckDetailSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk:
            return Deck.nameless.filter(pk=pk)
        return Deck.nameless.all()
