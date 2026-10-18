from django.db import transaction
from rest_framework import serializers

from .models import Question, QuestionOption, Topic


class TopicSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False, allow_null=True)
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Topic
        fields = ('id', 'subject', 'name', 'parent', 'questions_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_parent(self, parent):
        org_id = self.context['request'].org_id
        if parent and parent.org_id != org_id:
            raise serializers.ValidationError('Родительская тема из другой организации.')
        if parent and self.instance and parent.id == self.instance.id:
            raise serializers.ValidationError('Тема не может быть родителем самой себя.')
        return parent


class QuestionOptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = QuestionOption
        fields = ('id', 'text', 'is_correct', 'match_target', 'order')


class QuestionSerializer(serializers.ModelSerializer):
    """Полный вопрос с правильными ответами — только для персонала организации."""
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())
    options = QuestionOptionSerializer(many=True, required=False)
    used_in_tests = serializers.IntegerField(source='in_tests.count', read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'topic', 'type', 'text', 'explanation', 'difficulty', 'tolerance', 'version',
                  'is_archived', 'options', 'used_in_tests', 'created_at')
        read_only_fields = ('id', 'version', 'created_at')

    def validate_topic(self, topic):
        if topic.org_id != self.context['request'].org_id:
            raise serializers.ValidationError('Тема из другой организации.')
        return topic

    def validate_difficulty(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Сложность от 1 до 5.')
        return value

    def validate(self, attrs):
        qtype = attrs.get('type') or (self.instance and self.instance.type)
        options = attrs.get('options')
        if options is None and self.instance is None:
            options = []
        if options is None:
            return attrs

        correct = [o for o in options if o.get('is_correct')]
        if qtype in ('single', 'multi') and len(options) < 2:
            raise serializers.ValidationError({'options': 'Нужно минимум два варианта ответа.'})
        if qtype == 'single' and len(correct) != 1:
            raise serializers.ValidationError({'options': 'В вопросе single ровно один правильный вариант.'})
        if qtype == 'multi' and not correct:
            raise serializers.ValidationError({'options': 'Отметьте хотя бы один правильный вариант.'})
        if qtype in ('short', 'number') and not correct:
            raise serializers.ValidationError({'options': 'Добавьте правильный ответ (is_correct=true).'})
        if qtype == 'number':
            for o in correct:
                try:
                    float(str(o['text']).replace(',', '.'))
                except ValueError as exc:
                    raise serializers.ValidationError({'options': 'Правильный ответ должен быть числом.'}) from exc
        if qtype == 'match' and (len(options) < 2 or any(not o.get('match_target') for o in options)):
            raise serializers.ValidationError({'options': 'Для match нужны минимум 2 пары с match_target.'})
        if qtype == 'open':
            attrs['options'] = []
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        options = validated_data.pop('options', [])
        question = Question.objects.create(**validated_data)
        self._save_options(question, options)
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        options = validated_data.pop('options', None)
        content_changed = any(
            k in validated_data and validated_data[k] != getattr(instance, k) for k in ('text', 'type', 'tolerance')
        ) or options is not None
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if content_changed:
            instance.version += 1
        instance.save()
        if options is not None:
            self._save_options(instance, options)
        return instance

    def _save_options(self, question, options):
        keep_ids = []
        for position, data in enumerate(options, start=1):
            data = {**data}
            option_id = data.pop('id', None)
            data.setdefault('order', position)
            if option_id and question.options.filter(id=option_id).exists():
                question.options.filter(id=option_id).update(**data)
                keep_ids.append(option_id)
            else:
                keep_ids.append(QuestionOption.objects.create(question=question, **data).id)
        question.options.exclude(id__in=keep_ids).delete()
