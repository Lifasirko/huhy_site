from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def query_update(context, **kwargs):
    """
    Оновлює поточні GET-параметри (context.request.GET) заданими параметрами (kwargs)
    і повертає URL-кодований рядок.
    """
    request = context['request']
    updated = request.GET.copy()
    for key, value in kwargs.items():
        updated[key] = value
    return updated.urlencode()
