from rest_framework.pagination import PageNumberPagination
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from . import views, queries
from django.conf import settings
import threading
from urllib.parse import parse_qs, urlparse, urlunparse, urlencode

PAGE_SIZE = 10

ads_initial_postition = settings.ADS_INITIAL_POSITION
interval_between_ads = settings.INTERVAL_BETWEEN_ADS
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
        self.page, _ = self.custom_page(queryset, request)
        list_page = list(self.page)
        self.insert_ads(request, list_page)
        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True
        if remainder == 0:
                threading.Timer(
                    1.0,
                    views.create_recommendations,
                    args=(request,)
                
                ).start()
        self.request = request
        return list_page
    
    def custom_page_number(self, request, paginator):
        page_number = self.get_page_number(request, paginator)
        count = int(paginator.num_pages)
        now = int(page_number)
        remainder = now % count
        self.get_next_link
        if now > count:
            if remainder == 0:
                return count
            else:
                return remainder
        else:
            try:
                return page_number
            except InvalidPage as exc:
                msg = self.invalid_page_message.format(
                    page_number=page_number, message=str(exc)
                )
                raise NotFound(msg)
    def custom_page(self, queryset, request):
        page_size = self.get_page_size(request)
        paginator = self.django_paginator_class(queryset, page_size)
        page_number = int(self.get_page_number(request, paginator))
        num = self.custom_page_number(request, paginator)
        return paginator.page(num), page_number
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
    def insert_ads(self, request, list_page):
        ads_count = PAGE_SIZE // 3
        post_count = len(list_page)
        additional = PAGE_SIZE - post_count
        if post_count < PAGE_SIZE:
            ads_count = additional
        posts = list_page
        page, num = self.custom_page(posts, request)
        paged_ads = self.get_paginated_ads(request, ads_count, page, num)
        # Generate ad positions: 2, 5, 9, 15, 18, 22, ...
        if additional > 0:
            #if recommendation has less values than page size
            ad_positions = [i for i in range(ads_initial_postition, additional*interval_between_ads + 1, interval_between_ads)]
        else: 
            #if recommendation is full
            ad_positions = [i for i in range(ads_initial_postition, PAGE_SIZE + 1, interval_between_ads)]
        ad_index = 0
        number_of_ads = len(paged_ads)
        for position in ad_positions:
            if ad_index < number_of_ads:
                ad = paged_ads[ad_index]
                if position <= len(posts):
                    posts.insert(position - 1, ad)
                else:
                    posts.append(ad)
                ad_index += 1
    def get_paginated_ads(self, request, count, page, page_number):
        if page is not None:
            if page_number <= 0:
                raise NotFound('Invalid page number')
            limit = count
            offset = (page_number - 1) * count
            e = limit + offset
            
            category = request.query_params.get('category')
            if category is not None:
                return queries.get_ad_for_category(request.user, category)
            else:
                return queries.get_ad_by_category(request.user)[offset:e]        
        return None
    
similar_pk = None
class SimilarPages(RecommendedPages):
    def get_paginated_ads(self, request, count, page, page_number):
        if page is not None:
            if page_number <= 0:
                raise NotFound('Invalid page number')
            limit = count
            offset = (page_number - 1) * count
            e = limit + offset
            pk = similar_pk
            print(pk)
            ads = queries.get_similar_ads(request.user, pk)[offset:e]
            return ads
        
        return None

