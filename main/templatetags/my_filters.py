from django import template

register = template.Library()


@register.filter
def index(List, i):
    return List[int(i)]


@register.filter
def to_underscore(value):
    return value.replace(" ", "_")


# @register.filter
# def lookup(d, key):
#     return d[key]
