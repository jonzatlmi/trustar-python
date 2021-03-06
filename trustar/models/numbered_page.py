# python 2 backwards compatibility
from __future__ import print_function

# package imports
from .base import ModelBase
from .page import Page
from ..utils import get_time_based_page_generator

# external imports
import math


class NumberedPage(Page):
    """
    This class models a page of items that would be found in the body of a response from an endpoint that uses number-
    based pagination. Not all paginated endpoints will use ``page_number``. For instance, the |get_reports_page|
    method requires pagination to be performed by continuously adjusting the ``from`` and ``to`` parameters.

    :ivar items: The list of items of the page; i.e. a list of indicators, reports, etc.
    :ivar page_number: The number of the page out of all total pages, indexed from 0.  i.e. if there are
        4 total pages of size 25, then page 0 will contain the first 25 elements, page 1 will contain the next 25, etc.
    :ivar page_size: The size of the page that was request.  Note that, if this is the last page, then this might
        not equal len(items).  For instance, if pages of size 25 were requested, there are 107 total elements, and
        this is the last page, then page_size will be 25 even though the page only contains 7 elements.
    :ivar total_elements: The total number of elements on the server, e.g. the total number of elements across all
        pages.  Note that it is possible for this value to change between pages, since data can change between queries.
    """

    def __init__(self, items=None, page_number=None, page_size=None, total_elements=None, has_next=None):
        super(NumberedPage, self).__init__(items=items)
        self.page_number = page_number
        self.page_size = page_size
        self.total_elements = total_elements
        self.has_next = has_next

    def get_total_pages(self):
        """
        :return: The total number of pages on the server.
        """

        if self.total_elements is None or self.page_size is None:
            return

        return math.ceil(float(self.total_elements) / float(self.page_size))

    def has_more_pages(self):
        """
        :return: ``True`` if there are more pages available on the server.
        """

        # if has_next property exists, it represents whether more pages exist
        if self.has_next is not None:
            return self.has_next

        # otherwise, try to compute whether or not more pages exist
        total_pages = self.get_total_pages()
        if self.page_number is None or total_pages is None:
            return
        else:
            return self.page_number + 1 < total_pages

    @staticmethod
    def from_dict(page, content_type=None):
        """
        Create a |NumberedPage| object from a dictionary.  This method is intended for internal use, to construct a
        |NumberedPage| object from the body of a response json from a paginated endpoint.

        :param page: The dictionary.
        :param content_type: The class that the contents should be deserialized into.
        :return: The resulting |NumberedPage| object.
        """

        result = NumberedPage(items=page.get('items'),
                      page_number=page.get('pageNumber'),
                      page_size=page.get('pageSize'),
                      total_elements=page.get('totalElements'),
                      has_next=page.get('hasNext'))

        if content_type is not None:
            if not issubclass(content_type, ModelBase):
                raise ValueError("'content_type' must be a subclass of ModelBase.")

            result.items = [content_type.from_dict(item) for item in result.items]

        return result

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of the page.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A dictionary representation of the page.
        """

        items = []

        # attempt to replace each item with its dictionary representation if possible
        for item in self.items:
            if hasattr(item, 'to_dict'):
                items.append(item.to_dict(remove_nones=remove_nones))
            else:
                items.append(item)

        return {
            'items': items,
            'pageNumber': self.page_number,
            'pageSize': self.page_size,
            'totalElements': self.total_elements,
            'hasNext': self.has_next
        }

    @staticmethod
    def get_page_generator(func, start_page=0, page_size=None):
        """
        Constructs a generator for retrieving pages from a paginated endpoint.  This method is intended for internal
        use.

        :param func: Should take parameters ``page_number`` and ``page_size`` and return the corresponding |NumberedPage| object.
        :param start_page: The page to start on.
        :param page_size: The size of each page.
        :return: A generator that generates each successive page.
        """

        # initialize starting values
        page_number = start_page
        more_pages = True

        # continuously request the next page as long as more pages exist
        while more_pages:

            # get next page
            page = func(page_number=page_number, page_size=page_size)

            yield page

            # determine whether more pages exist
            more_pages = page.has_more_pages()
            page_number += 1

    @staticmethod
    def get_time_based_page_generator(get_page, get_next_to_time, from_time=None, to_time=None):
        return get_time_based_page_generator(get_page=get_page,
                                             get_next_to_time=lambda page, to_time: get_next_to_time(page.items, to_time),
                                             from_time=from_time,
                                             to_time=to_time)
