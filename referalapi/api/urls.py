from django.urls import include, path
from rest_framework.routers import DefaultRouter as Router

from .views import (CodesViewSet, CustomUserViewSet, ReferalViewSet,
                    RefererViewSet, SendEmail)

router_v1 = Router()
router_v1.register('users', CustomUserViewSet, basename='user')
router_v1.register('code', CodesViewSet, basename='code')
router_v1.register('referals', ReferalViewSet, basename='referal')
router_v1.register(
    r'referer/(?P<user_id>\d+)', RefererViewSet, basename='referer'
)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.jwt')),
    path('send-code-email/', SendEmail.as_view()),
]
