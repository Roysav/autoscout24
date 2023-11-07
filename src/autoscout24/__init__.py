from typing import Optional

import requests
import parsel
import dataclasses
from .utils import _url_repr


_BASE_URL = 'https://autoscout24.com'


@dataclasses.dataclass
class Maker:
    id: str
    name: str


@dataclasses.dataclass
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




