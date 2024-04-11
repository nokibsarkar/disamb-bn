import random, requests
from html.parser import HTMLParser
from xml.etree import ElementTree
# xpath to select all the li as children of ol.special
_DISAMBIG_ENTRY_XPATH = ".//ol[@class='special']/li/a"
class _MyHTMLParser(HTMLParser):
    """
    Build a tree from the HTML source 
    """
    def __init__(self):
        super().__init__()
        self.stack = []
        self.tree = None

    def handle_starttag(self, tag, attrs):
        elem = ElementTree.Element(tag, dict(attrs))
        if self.stack:
            self.stack[-1].append(elem)
        self.stack.append(elem)

    def handle_endtag(self, tag):
        self.stack.pop()

    def handle_data(self, data):
        if self.stack:
            self.stack[-1].text = data

    def handle_startendtag(self, tag, attrs):
        elem = ElementTree.Element(tag, dict(attrs))
        if self.stack:
            self.stack[-1].append(elem)

    def feed(self, data):
        super().feed(data)
        self.tree = self.stack[0]

    def close(self):
        super().close()
        self.tree = self.stack[0]
        

class Disambig:
    seed = 89
    @staticmethod
    def _get_page(language : str, offset : int = 0):
        url = f"https://{language}.wikipedia.org/w/index.php?title=Special:DisambiguationPageLinks&limit=20&offset={offset}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    @staticmethod
    def get_disambiguation(language : str):
        selected_page = None
        while selected_page is None:
            limit = random.randint(0, 500)
            text = Disambig._get_page(language, limit)
            if text:
                selected_page = Disambig._get_page_list(text)
        return selected_page
    @staticmethod
    def _get_page_list(text : str):
        parser = _MyHTMLParser()
        parser.feed(text)
        li_element = parser.tree.find(_DISAMBIG_ENTRY_XPATH)
        return li_element.text
    