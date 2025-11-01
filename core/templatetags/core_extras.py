from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """
    Custom template filter to get value from dictionary by key
    Usage: {{ my_dict|dict_get:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, 0)
