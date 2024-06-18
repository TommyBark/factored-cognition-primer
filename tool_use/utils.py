import re
import bs4 as bs
import requests
from typing import Optional


def remove_ordinal(query: str) -> str:
    "Remove the ordinal number at the start of a query"
    return re.sub(r"^\d+\.\s", "", query)


def get_url_from_text(text: str) -> Optional[str]:
    search = re.search(r"https?://\S+", text)
    if search is None:
        return None
    return search.group().strip('"')


def get_body_text(url: str) -> str:
    # get the website
    res = requests.get(url)
    # check if the website is accessible
    if res.status_code != 200:
        print("Error: Website not accessible")
        return None
    # parse the website
    soup = bs.BeautifulSoup(res.text, "html.parser")
    # get the body text
    body_text = ""
    for paragraph in soup.find_all("p"):
        body_text += paragraph.text
    return body_text
