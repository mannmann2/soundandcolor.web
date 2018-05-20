from django import template
register = template.Library()

@register.filter
def index(value, i):
    return value[int(i)]