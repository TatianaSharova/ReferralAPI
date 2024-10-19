import requests

from users.constans import HUNTER_API_KEY

from .exceptions import APIError


def check_email(email) -> bool:
    endpoint = f'https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}'

    response = requests.get(endpoint)

    if response.status_code == 200:
        result = response.json()
        print(result)
        if (result.get('data', {}).get('status') == 'valid'
                or result.get('data', {}).get('status') == 'accept_all'):
            return True
        return False
    raise APIError('Ошибка при запросе к API Hunter.io')
