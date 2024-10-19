from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .constans import CODE_MAX_LENGTH, EMAIL_LENGTH, USER_MAX_LENGTH


class User(AbstractUser):
    '''
    Переопределенная модель юзера.
    '''
    password = models.CharField('Пароль', default=None,
                                max_length=USER_MAX_LENGTH)
    first_name = models.CharField('Имя', max_length=USER_MAX_LENGTH,
                                  blank=True)
    last_name = models.CharField('Фамилия', max_length=USER_MAX_LENGTH,
                                 blank=True)
    email = models.EmailField('E-mail', max_length=EMAIL_LENGTH, unique=True)

    class Meta:
        ordering = ('-date_joined',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Refers(models.Model):
    '''
    Модель связи рефереров с рефералами.
    '''
    referer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='referer')
    referal = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='referal')

    class Meta:
        ordering = ('referer',)
        verbose_name = 'Рефералка'
        verbose_name_plural = 'Рефералки'
        constraints = [
            models.UniqueConstraint(
                fields=['referer', 'referal'],
                name='unique_refer'
            ),
        ]

    def __str__(self):
        return f'{self.referal} зарегистрировался по рефералке {self.referer}.'


class Codes(models.Model):
    '''
    Модель для реферальных кодов.
    '''
    code = models.CharField('Реферальный код', max_length=CODE_MAX_LENGTH,
                            unique=True, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='code')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    expires_at = models.DateTimeField('Дата конца действия кода',
                                      blank=True, null=True)
    live_days = models.PositiveIntegerField('Срок действия кода', blank=False)

    @property
    @extend_schema_field(serializers.BooleanField)
    def is_expired(self):
        '''Проверка, истек ли срок действия кода.'''
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        '''Автоматически устанавливаем expires_at при сохранении.'''
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=self.live_days)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'Реферальный код'
        verbose_name_plural = 'Реферальные коды'
        constraints = [
            models.UniqueConstraint(
                fields=['code', 'user'],
                name='unique_refer_codes'
            ),
        ]

    def __str__(self):
        return f'{self.code} - реферальный код {self.user.username}.'
