import datetime as dt

import requests
from django.utils import timezone

from users.constans import HUNTER_API_KEY

from .exceptions import APIError


def check_email(email) -> bool:
    '''
    Проверяет действительность почты через сервис hunter.io.
    '''
    endpoint = f'https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}'

    response = requests.get(endpoint)

    if response.status_code == 200:
        result = response.json()
        if (result.get('data', {}).get('status') == 'valid'
                or result.get('data', {}).get('status') == 'accept_all'):
            return True
        return False
    raise APIError(f'Ошибка при запросе к API Hunter.io,'
                   f'статус код ответа: {response.status_code}.')


def get_timeout(expires_at: dt.date) -> dt.timedelta:
    '''
    Возвращает временной промежуток, равный сроку жизни кода.
    '''
    if timezone.now() < expires_at:
        return expires_at - timezone.now()
    return dt.timedelta(seconds=0)
