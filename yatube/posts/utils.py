from django.core.paginator import Paginator

POST_PER_PAGE = 10


def get_paginator_helper(request, post_list):
    paginator = Paginator(
        post_list,
        POST_PER_PAGE,
    )
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
