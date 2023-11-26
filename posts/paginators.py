from rest_framework.pagination import PageNumberPagination
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from . import views
import threading
from urllib.parse import parse_qs, urlparse, urlunparse, urlencode

PAGE_SIZE = 2
class Pages(PageNumberPagination):
    page_size = PAGE_SIZE

class RecommendedPages(PageNumberPagination):
    page_size = PAGE_SIZE
    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)
        count = int(paginator.num_pages)
        now = int(page_number)
        remainder = now % count
        self.get_next_link
        if now > count:
            if remainder == 0:
                self.page = paginator.page(count)
            else:
                self.page = paginator.page(remainder)
        else:
            try:
                self.page = paginator.page(page_number)
            except InvalidPage as exc:
                msg = self.invalid_page_message.format(
                    page_number=page_number, message=str(exc)
                )
                raise NotFound(msg)
        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True
        list_page = list(self.page)
        if remainder == 0:
                threading.Timer(
                    1.0,
                    views.create_recommendations,
                    args=(request,)
                
                ).start()
        self.request = request
        return list_page
    def get_previous_link(self):
        if not self.page.has_previous():
            return self.get_page_at(self.page.paginator.num_pages)
        return super().get_previous_link()
    def get_next_link(self):
        if not self.page.has_next():
            return self.get_page_at(1)
        return super().get_next_link()
    def get_page_at(self, pageNumber):
        url = self.request.build_absolute_uri()
        url_parts = list(urlparse(url))
        qparams = parse_qs(url_parts[4])
        qparams.pop(self.page_query_param, None)
        qparams[self.page_query_param] = pageNumber
        url_parts[4] = urlencode(qparams, doseq=True)
    
        return urlunparse(url_parts)
   