from rest_framework import serializers

from .models import Question, QuestionOption, Voting, QuestionOrder
from base.serializers import KeySerializer, AuthSerializer

class QuestionOrderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = QuestionOrder
        fields = ('order_number','number','option')

class QuestionOptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('number', 'option')


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    options = QuestionOptionSerializer(many=True)
    order_options = QuestionOrderSerializer(many=True)
    class Meta:
        model = Question
        fields = ('desc', 'options', 'order_options', 'is_yes_no_question')


class VotingSerializer(serializers.HyperlinkedModelSerializer):
    question = QuestionSerializer(many=False)
    pub_key = KeySerializer()
    auths = AuthSerializer(many=True)

    class Meta:
        model = Voting
        fields = ('id', 'name', 'desc', 'question', 'slug', 'start_date',
                  'end_date', 'pub_key', 'auths', 'tally', 'postproc')


class SimpleVotingSerializer(serializers.HyperlinkedModelSerializer):
    question = QuestionSerializer(many=False)

    class Meta:
        model = Voting
        fields = ('name', 'desc', 'question', 'slug', 'start_date', 'end_date')
