from django import template

from companies.models import Company

register = template.Library()


@register.filter
def pagination_url_replace(page, request):
    """
    Add other GET params to the Url on pagination
    :param page: page number
    :param request: current request
    :return: new url
    """

    dict_ = request.GET.copy()
    dict_['page'] = page

    return dict_.urlencode()
