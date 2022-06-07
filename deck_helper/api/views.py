from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CardListSerializer, CardDetailSerializer, DeckSerializer
from .services.filters import CardFilter, DeckFilter
from .services.utils import DjangoFilterBackend
from core.services.deck_codes import get_clean_deckstring
from core.exceptions import DecodeError, UnsupportedCards
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
            return CardListSerializer
        elif self.action == 'retrieve':
            return CardDetailSerializer


class DeckListAPIView(generics.ListAPIView):
    """ Getting a list of decks """

    queryset = Deck.nameless.all()
    serializer_class = DeckSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = DeckFilter


class DeckDetailAPIView(generics.RetrieveAPIView):
    """ Getting a specific deck """
    queryset = Deck.nameless.all()
    serializer_class = DeckSerializer


class DecodeDeckAPIView(APIView):
    """ Decoding the deck from code """

    def post(self, request):
        if deckstring := request.data.get('d'):
            try:
                deckstring = get_clean_deckstring(deckstring)
                deck = Deck.from_deckstring(deckstring)
                serializer = DeckSerializer(deck)
                return Response(serializer.data)
            except DecodeError as de:
                return Response({'error': str(de)})
            except UnsupportedCards as u:
                return Response({'error': str(u)})

        return Response()
