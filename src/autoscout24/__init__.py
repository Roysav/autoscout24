import urllib.parse
from typing import Optional

import requests
import parsel
import dataclasses
from .utils import _url_repr
import caseconverter
import pydantic


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


class ListingModel(pydantic.BaseModel):
    testid: str
    guid: str
    customer_id: str = pydantic.Field(..., alias='customer-id')
    vehicle_type: str = pydantic.Field(..., alias='vehicle-type')
    price_label: str = pydantic.Field(..., alias='price-label')
    source: str
    position: str
    price: int
    make: str
    leads_range: str = pydantic.Field(..., alias='leads-range')
    image_content: str = pydantic.Field(..., alias='image-content')
    seller_type: str = pydantic.Field(..., alias='seller-type')
    otp: str
    listing_country: str = pydantic.Field(..., alias='listing-country')
    listing_zip_code: str = pydantic.Field(..., alias='listing-zip-code')
    mileage: str
    fuel_type: str = pydantic.Field(..., alias='fuel-type')
    model: str
    first_registration: str = pydantic.Field(..., alias='first-registration')
    is_smyle_eligible: str = pydantic.Field(..., alias='is-smyle-eligible')
    ownership_models: str = pydantic.Field(..., alias='ownership-models')
    order_bucket: str = pydantic.Field(..., alias='order-bucket')


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
        f'{caseconverter.kebabcase(maker.name)}/'
        f'{caseconverter.kebabcase(model.name)}?'
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


def _parse_listing_page(page_html: str) -> list[ListingModel]:
    """
    :param page_html: html of the entire page
    :return: a `ListingsPage` object
    """
    selector = parsel.Selector(page_html)
    listings = []
    for article in selector.css('article'):
        data = _parse_data_dict(article.attrib)
        listing = ListingModel(**data)
        listings.append(listing)
    return listings


def get_listings(maker: Maker, model: Model, **options):
    response = requests.get(_listings_url(maker, model, **options))
    response.raise_for_status()

    page_html = response.text
    return _parse_listing_page(page_html)
