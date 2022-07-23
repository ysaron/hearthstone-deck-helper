from rest_framework import serializers

from cards.models import Card
from decks.models import Deck, Inclusion


class FilterCardListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        data = data.filter(collectible=True)
        return super().to_representation(data)

    def update(self, instance, validated_data):
        pass


class BaseCardSerializer(serializers.ModelSerializer):

    card_type = serializers.CharField(source='get_card_type_display')
    card_set = serializers.SlugRelatedField(slug_field='name', read_only=True)
    card_class = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    rarity = serializers.CharField(source='get_rarity_display')
    tribe = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    spell_school = serializers.CharField(source='get_spell_school_display')
    mechanic = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)


class CardListSerializer(BaseCardSerializer):

    class Meta:
        list_serializer_class = FilterCardListSerializer
        model = Card
        fields = ('dbf_id', 'card_id', 'name', 'collectible', 'card_type', 'card_class', 'rarity')
        ref_name = 'CardList'


class CardDetailSerializer(BaseCardSerializer):

    class Meta:
        model = Card
        fields = ('dbf_id', 'card_id', 'name', 'collectible', 'battlegrounds',
                  'card_type', 'cost', 'attack', 'health', 'durability', 'armor',
                  'card_class', 'card_set', 'text', 'flavor', 'rarity', 'tribe',
                  'spell_school', 'artist', 'mechanic')
        ref_name = 'Card'


class CardInDeckSerializer(BaseCardSerializer):

    class Meta:
        model = Card
        fields = ('dbf_id', 'card_id', 'name', 'card_type', 'cost', 'attack',
                  'health', 'durability', 'armor', 'card_class', 'card_set', 'rarity')
        ref_name = 'CardInDeck'


class InclusionSerializer(serializers.ModelSerializer):
    """ Сериализация списка карт в колоде """

    card = CardInDeckSerializer()

    class Meta:
        model = Inclusion
        fields = ('card', 'number')
        ref_name = 'CardInclusion'


class DeckSerializer(serializers.ModelSerializer):

    deck_class = serializers.SlugRelatedField(slug_field='name', read_only=True)
    deck_format = serializers.SlugRelatedField(slug_field='name', read_only=True)
    cards = serializers.SerializerMethodField()
    created = serializers.DateTimeField(format='%d.%m.%Y')

    def get_cards(self, instance):
        cards = instance.inclusions.all().order_by('card__cost', 'card__name')
        return InclusionSerializer(cards, many=True).data


class DeckListSerializer(DeckSerializer):

    class Meta:
        model = Deck
        fields = ('id', 'deck_format', 'deck_class', 'string', 'created')


class DeckDetailSerializer(DeckSerializer):

    class Meta:
        model = Deck
        fields = ('id', 'deck_format', 'deck_class', 'string', 'created', 'cards')
