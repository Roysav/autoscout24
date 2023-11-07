import urllib.parse
from typing import Optional

import requests
import parsel
import dataclasses
from .utils import _url_repr


_BASE_URL = 'https://autoscout24.com'


@dataclasses.dataclass(slots=True, frozen=True)
class Maker:
    id: str
    name: str


@dataclasses.dataclass(slots=True, frozen=True)
class Model:
    id: int
    name: str


@dataclasses.dataclass
class ListingsPage:
    """represent a scraped page data for the path:
    https://autoscout24.com/lst/{maker}/{model}?...
    """

    maker: Maker
    model: Model
    listings: list
    url: str
    page: int = 1
    prev_url: Optional[str] = None  # url of the previous page
    next_url: Optional[str] = None  # url of the next page


def get_models(maker: Maker) -> list[Model]:
    response = requests.get(f"{_BASE_URL}/as24-home/api/taxonomy/cars/makes/{maker.id}/models")
    response.raise_for_status()

    return [
        Model(id=value['id'], name=value['name'])
        for value in response.json()['models']['model']['values']
    ]


def get_makers() -> list[Maker]:
    response = requests.get(f'{_BASE_URL}')
    response.raise_for_status()

    selector = parsel.Selector(response.text)

    options = selector.css('select#make optgroup option')
    return [
        Maker(
            id=option.attrib['value'],
            name=option.css('::text').get(),
        )
        for option in options
    ]


def _listings_url(maker: Maker, model: Model, **options):
    return (
        f'{_BASE_URL}/lst/'
        f'{_url_repr(maker.name)}/'
        f'{_url_repr(model.name)}?'
        f'{urllib.parse.urlencode(options)}'
    )


def _parse_data_dict(article_attrs: dict[str, str]):
    """
    :param article_attrs: dict of the <article/> element attributes .i.e {"class": "class1 class2", "data-maker": "bmw"}
    :return: only keys starting with "data-" and rename "data-*" -> "*"
        .i.e the key "data-maker" will be renamed as just "maker"
    """
    data = {}
    for key, value in article_attrs.items():
        if key.startswith('data-'):
            new_key = key.replace('data-', '', 1)
            data[new_key] = value
    return data


def _parse_listing_page(page_html: str) -> list[dict]:
    """
    :param page_html: html of the entire page
    :return: a `ListingsPage` object
    """
    selector = parsel.Selector(page_html)
    listings_data = []
    for article in selector.css('article'):
        data = _parse_data_dict(article.attrib)
        listings_data.append(data)
    return listings_data


def get_listings(maker: Maker, model: Model, **options):
    response = requests.get(_listings_url(maker, model, **options))
    response.raise_for_status()

    page_html = response.text
    return _parse_listing_page(page_html)
