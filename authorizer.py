import os, requests, urllib.parse
import urllib.parse
VERIFIER_OAUTH_CLIENT_ID = os.getenv('OAUTH_APPLICATION_KEY')
VERIFIER_OAUTH_CLIENT_SECRET = os.getenv('OAUTH_APPLICATION_SECRET')
HOSTNAME = os.getenv('TOOL_HOSTNAME')
META_OAUTH_AUTHORIZE_URL = 'https://meta.wikimedia.org/w/rest.php/oauth2/authorize'
META_OAUTH_ACCESS_TOKEN_URL = 'https://meta.wikimedia.org/w/rest.php/oauth2/access_token'
META_PROFILE_URL = 'https://meta.wikimedia.org/w/rest.php/oauth2/resource/profile'
COOKIE_NAME = 'auth'
def get_login_url(redirect_uri : str = '/'):
    
    endpoint = META_OAUTH_AUTHORIZE_URL
    params = {
        'response_type' : 'code',
        'client_id' : VERIFIER_OAUTH_CLIENT_ID,
        'state' :  urllib.parse.quote_plus(redirect_uri),
        'redirect_uri' : f'{HOSTNAME}/user/callback',
    }
    
    url = endpoint + '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
    print(url)
    return url
    pass
def get_csrf_token(language, access_token : str):
    url = f"https://{language}.wikipedia.org/w/api.php"
    params = {
        'action' : 'query',
        'meta' : 'tokens',
        'format' : 'json',
        'type' : 'csrf',
    }
    headers = {
        'Authorization' : f'Bearer {access_token}',
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json()['query']['tokens']['csrftoken']
