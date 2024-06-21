import os

from rest_framework import pagination


class StandardPageNumberPagination(pagination.PageNumberPagination):
    page_size: int = int(os.environ["PAGE_SIZE"])
    max_page_size: int = int(os.environ["MAXIMUM_PAGE_SIZE"])
    page_query_param: str = "page"
    page_size_query_param = "page_size"
