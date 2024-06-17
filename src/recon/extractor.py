import re
import requests
from typing import List, Union


class LinkExtractor:
    def __init__(self, url=None, method="GET") -> None:
        self.url = url
        self.method = method

    def extract(
        self,
        cookies: Union[dict, None] = None, 
        headers: Union[dict, None] = None
    ):
        response = requests.request(
            method=self.method, 
            url=self.url, 
            cookies=cookies, 
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve links: {response.status_code}")

        js_content = response.text
        url_pattern = re.compile(
            r'(?:"|\')((?:http|https)://[^\s"\']+|/[^"\']+)(?:"|\')'
        )
        
        # Extraindo URLs
        urls = url_pattern.findall(js_content)
        
        return set(urls)
