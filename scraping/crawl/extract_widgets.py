import re

from bs4 import BeautifulSoup
from pydantic import BaseModel


class OClocherWidget(BaseModel):
    organization_id: str


BaseWidget = OClocherWidget


def extract_oclocher_widgets(html: str) -> list[OClocherWidget]:
    soup = BeautifulSoup(html, 'html.parser')
    widgets = []

    for iframes in soup.find_all('iframe'):
        src_url = iframes.get('src')
        if not src_url:
            continue

        match = re.search(r"widget.oclocher.app/organization/([^/]+)/", src_url)
        if not match:
            continue
        organization_id = match.group(1)
        widgets.append(OClocherWidget(organization_id=organization_id))

    return widgets


def extract_widgets(html: str) -> list[BaseWidget]:
    return extract_oclocher_widgets(html)
