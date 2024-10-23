from datetime import timedelta

from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.core.cache import cache
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.settings import api_settings

from users.models import Codes, Refers, User

from .utils import check_email, get_timeout


class UserCreationSerializer(UserCreateSerializer):
    '''Serializer для создания пользователя.'''
    referral_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'username', 'referral_code')

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)

        if referral_code:
            code = cache.get(f'{referral_code}')
            if not code:
                try:
                    code = Codes.objects.get(code=referral_code)
                    cache.set(f'{referral_code}',
                              {
                                  'id': code.id,
                                  'code': code.code,
                                  'user': code.user.id,
                                  'created_at': code.created_at,
                                  'live_days': code.live_days,
                                  'expires_at': code.expires_at,
                                  'is_expired': code.is_expired
                              },
                              timeout=timedelta(days=1).total_seconds())
                    if code.is_expired:
                        raise serializers.ValidationError(
                            'Срок годности реферального кода истек.'
                        )
                    code = cache.get(f'{code.code}')
                except Codes.DoesNotExist:
                    raise serializers.ValidationError(
                        'Реферальный код недействителен.'
                    )

            if code['is_expired'] is True:
                raise serializers.ValidationError(
                    'Срок годности реферального кода истек!'
                )
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
        )

        if referral_code:
            Refers.objects.create(
                referer_id=code['user'],
                referal=user
            )
        return user

    def validate_email(self, value):
        '''Проверка email на существование через Hunter.io'''
        is_valid = check_email(value)
        if not is_valid:
            raise serializers.ValidationError('Этот email недействителен.')
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        username = attrs.get('username')
        email = attrs.get('email')

        user = User(username=username, email=email, password=password)

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {'password': serializer_error[
                    api_settings.NON_FIELD_ERRORS_KEY
                ]}
            )
        return attrs


class CodeSerializer(serializers.ModelSerializer):
    '''
    Serializer для создания реферального кода.
    '''
    user = SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Codes
        fields = ('id', 'code', 'user', 'created_at',
                  'live_days', 'expires_at', 'is_expired')
        read_only_fields = ('user', 'expires_at')

    def validate(self, data):
        if self.context.get('request').method == 'POST':
            user = self.context['request'].user

            code = cache.get(f'user_{user.id}')
            if code:
                raise serializers.ValidationError(
                    'Одновременно можно иметь только 1 код!'
                )
            code = user.code.filter(user=user)
            if code.exists():
                raise serializers.ValidationError(
                    'Одновременно можно иметь только 1 код!'
                )

        return data

    def create(self, validated_data):
        code = Codes.objects.create(**validated_data)

        cache.set(
            f'{code.code}',
            {
                'id': code.id,
                'code': code.code,
                'user': code.user.id,
                'created_at': code.created_at,
                'live_days': code.live_days,
                'expires_at': code.expires_at,
                'is_expired': code.is_expired
            },
            timeout=timedelta(days=code.live_days).total_seconds()
        )
        cache.set(
            f'user_{code.user.id}',
            code.code,
            timeout=timedelta(days=code.live_days).total_seconds()
        )

        return code

    def update(self, instance, validated_data):
        if 'live_days' in validated_data:
            new_live_days = validated_data['live_days']
            instance.expires_at = instance.created_at + timedelta(
                days=new_live_days
            )

            timeout = get_timeout(instance.expires_at)

            cache.set(
                f'{instance.code}',
                {
                    'id': instance.id,
                    'code': instance.code,
                    'user': instance.user.id,
                    'created_at': instance.created_at,
                    'live_days': new_live_days,
                    'expires_at': instance.expires_at,
                    'is_expired': instance.is_expired
                },
                timeout=timeout.total_seconds()
            )
            cache.set(
                f'user_{instance.user.id}',
                instance.code,
                timeout=timeout.total_seconds()
            )

        return super().update(instance, validated_data)


class UserReferalSerializer(serializers.ModelSerializer):
    '''
    Serializer для отображения списка рефералов.
    '''

    class Meta:
        model = User
        fields = ('username', 'date_joined')


class ReferalSerializer(serializers.ModelSerializer):
    '''
    Serializer для просмотра списка собственных рефералов пользователя и
    для просмотра рефералов пользователя по id.
    '''
    referal = UserReferalSerializer()

    class Meta:
        model = Refers
        fields = ('referal',)
