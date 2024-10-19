from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from referalapi.settings import EMAIL_HOST_USER
from users.models import Codes, Refers, User

from .permissions import IsAuthor
from .serializers import (CodeSerializer, ReferalSerializer,
                          UserCreationSerializer)


class CustomUserViewSet(viewsets.ModelViewSet):
    '''
    ViewSet для регистрации новых пользователей.
    '''
    queryset = User.objects.all()
    serializer_class = UserCreationSerializer
    http_method_names = ['post',]
    permission_classes = (AllowAny,)

    def perform_create(self, serializer, *args, **kwargs):
        serializer.save(*args, **kwargs)


class CodesViewSet(viewsets.ModelViewSet):
    '''
    ViewSet для создания, удаления, чтения и редактирования
    реферального кода. Все CRUD действия может выполнять только
    создатель кода. На чтение выдается только собственный код юзера.
    '''
    serializer_class = CodeSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']
    permission_classes = (IsAuthor,)
    queryset = Codes.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if self.request.method in permissions.SAFE_METHODS:
            return Codes.objects.filter(user=self.request.user)
        return Codes.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {'detail': 'Упс, у вас еще нет своего кода.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return super().list(request, *args, **kwargs)


class ReferalViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    '''
    ViewSet для просмотра списка своих рефералов.
    '''
    model = Refers
    serializer_class = ReferalSerializer

    def get_queryset(self):
        return Refers.objects.filter(referer=self.request.user)


class RefererViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    '''
    ViewSet для просмотра списка рефералов по id реферера.
    '''
    model = Refers
    serializer_class = ReferalSerializer
    queryset = Refers.objects.all()

    def get_referer(self):
        return get_object_or_404(User, pk=self.kwargs.get('user_id'))

    def get_queryset(self):
        referer = self.get_referer()
        return Refers.objects.filter(referer=referer)


class SendEmail(APIView):
    '''
    View для отправки email с реферальным кодом юзера
    на его почту по запросу.
    '''

    def get(self, request):
        user = request.user
        email = user.email
        try:
            ref_code = Codes.objects.get(user=user)
        except Codes.DoesNotExist:
            return Response(
                {'detail': 'У вас нет своего реферального кода!'},
                status=status.HTTP_404_NOT_FOUND
            )

        send_mail(
            subject='Your referral code',
            message=f'Ваш реферальный код: {ref_code.code}',
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {'detail': 'Реферальный код отправлен на вашу почту.'},
            status=status.HTTP_200_OK
        )