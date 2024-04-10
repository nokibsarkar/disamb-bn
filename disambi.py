import re
from requests import Session
from urllib.parse import quote
sess = Session()

WIKILINK_PATTERN = re.compile('\[\[(?P<target>[^\]\|#]+)(?P<extension>[^\]]+)?\]\]')
DISAMBIGUABLE_CLASS = 'disambiguable'
DOUBLE_QUOTE = '"'
SINGLE_QUOTE = "'"
UNDER_SCORE = "_"
SPACE = " "
DOUBLE_QUOTE_BACKSLASHED = '\\"'

DISAMBIGUABLE_BY_TITLE_BASE_LENGTH = 132
MAX_URL_LENGTH = 2*2048
MAX_AVAILABLE_URL_LENGTH = MAX_URL_LENGTH - DISAMBIGUABLE_BY_TITLE_BASE_LENGTH
class Server:
    language : str = "bn"
    access_token : str = ""
    sess = Session()
    url : str = f"https://{language}.wikipedia.org/w/api.php"
    def __init__(self, language : str = "bn", access_token : str = ""):
        self.language = language 
        self.url = f"https://{language}.wikipedia.org/w/api.php"
        self.access_token = access_token
        self.sess.headers.update({
            'Authorization' : f'Bearer {access_token}',
        })
    @staticmethod
    def encode_html_entity(content : str):
        content = content.replace('&', '&amp;')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        return content
    def get(self, params : dict) -> dict:
        response = None
        try:
            response = self.sess.get(self.url, params=params)
            return response.json()
        except Exception as e:
            if response:
                print(response.text)
            return {}
    def get_csrf_token(self) -> str:
        params = {
            'action' : 'query',
            'meta' : 'tokens',
            'format' : 'json',
            'type' : 'csrf',
        }
        response = self.get(params)
        return response['query']['tokens']['csrftoken']
    def post(self, params : dict) -> dict:
        response = self.sess.post(self.url, data=params)
        return response.json()
    @staticmethod
    def get_canonical(target : str) -> str:
        return target.strip().replace(UNDER_SCORE, SPACE)
    @staticmethod
    def get_checkables(content : str) -> "set[str]":
        checkables = set()
        for match in WIKILINK_PATTERN.finditer(content):
            target = match.group('target')
            canonical = Server.get_canonical(target)
            checkables.add(canonical)
        return checkables
    @staticmethod
    def replace_generator(candidates : set):
        def replace_and_index(match : re.Match):
            target : str = match.group('target')
            canonical : str = Server.get_canonical(target)
            if canonical not in candidates:
                return match.group(0)
            BACKSLASHED_TARGET = canonical.replace(DOUBLE_QUOTE, DOUBLE_QUOTE_BACKSLASHED)
            extension : str = match.group('extension')
            content_to_be_replaced = f'[[<span class="{DISAMBIGUABLE_CLASS}" data-index="{BACKSLASHED_TARGET}">{target}</span>{extension or ""}]]'
            return content_to_be_replaced
        return replace_and_index
    
    def determine_disambiguables(self, title : str) -> "set[str]":
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageprops",
            "titles": title,
            "generator": "links",
            "formatversion": "2",
            "ppprop": "disambiguation",
            "gpllimit": "max",
            "redirects": 1
        }
        response = self.get(params)
        redirects = response['query'].get('redirects', [])
        candidates = set(page['from'] for page in redirects)
        pages = response['query']['pages']
        for page in pages:
            if "pageprops" in page:
                candidates.add(page['title'])
        return candidates
    def determine_disambiguables_by_title(self, titles : list) -> "set[str]":
        titles = list(titles)
        last_index = 0
        title_count = len(titles)
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageprops",
            "titles": "",
            "formatversion": "2",
            "ppprop": "disambiguation",
            "redirects": 1
        }
        candidates = set()
        while last_index < title_count:
            title_joined_length = 0
            title_ = set()
            while last_index < title_count:
                quoted = quote(titles[last_index])
                if title_joined_length + len(quoted) < MAX_AVAILABLE_URL_LENGTH:
                    title_.add(titles[last_index])
                    title_joined_length += len(quoted)
                    last_index += 1
                else:
                    break
            params['titles'] = "|".join(title_)
            t = True
            while t:
                response = self.get(params)
                pages = response['query']['pages']
                candidates.update(page['title'] for page in pages if "pageprops" in page)
                candidates.update(page['from'] for page in response['query'].get('redirects', []))
                t = 'continue' in response
                if t:
                    params.update(response['continue'])
                
        return candidates
    def get_page_content(self, title : str) -> str:
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "formatversion": "2",
            "rvslots": "main"
        }
        response = self.get(params)
        pages = response['query']['pages']
        page = pages[0]
        if 'missing' in page:
            return
        content = page['revisions'][0]['slots']['main']['content']
        return content

    def main(self, title):
        content = self.get_page_content(title)
        if content is not None:
            content = Server.encode_html_entity(content)
            candidates = self.determine_disambiguables(title)
            replace_and_index = Server.replace_generator(candidates)
            content = WIKILINK_PATTERN.sub(replace_and_index, content)
            response = {
                "title": title,
                "content": content.replace("\n", "<br>"),
                "candidates": list(candidates),
                "csrftoken": "csrftoken",
                "language": "bn",
                "disambiguable_class": DISAMBIGUABLE_CLASS,
                "user" : None
            }
        else:
            response = response = {
                "title": title,
                "content": None,
                "candidates": [],
                "csrftoken": "csrftoken",
                "language": "bn",
                "disambiguable_class": DISAMBIGUABLE_CLASS,
                "user" : None
            }
        return response
    def edit(self, title, text, summary):
        csrf = self.get_csrf_token()
        params = {
            'action' : 'edit',
            'title' : title,
            'text' : text,
            "summary" : summary,
            'format' : 'json',
            'token' : csrf,
        }
        response = self.post(params)
        return response
        pass

if __name__ == "__main__":
    server = Server()
    server.main()
