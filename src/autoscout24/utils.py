def _url_repr(st__: str) -> str:
    """
    :param st__: string of either model name or maker name
    :return: the model | maker name in urls inside autoscout24

    >>> _url_repr("Bmw")
    ... "bmw"

    >>> _url_repr("7 Series (All)")
    ... "7-series-(all)"

    """
    return st__.lower().replace(' ', '-')

