from bs4 import BeautifulSoup

def html_to_text(html_content):
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    return soup.get_text(
        separator=" ",
        strip=True
    )