from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Récupère un élément d'un dictionnaire par sa clé.
    Utilisation: {{ dict|get_item:key }}
    """
    if dictionary is None or key is None:
        return None
    
    # Si c'est un dictionnaire
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    
    # Si c'est une liste et key est un entier
    if isinstance(dictionary, list) and isinstance(key, int):
        try:
            return dictionary[key]
        except IndexError:
            return None
    
    # Si c'est un objet avec un attribut
    if hasattr(dictionary, str(key)):
        return getattr(dictionary, str(key))
    
    return None


@register.filter
def multiply(value, arg):
    """Multiplie deux nombres"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """Soustrait deux nombres"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def get_category_name(categories, category_id):
    """
    Récupère le nom d'une catégorie par son ID
    """
    if not categories or not category_id:
        return "Catégorie"
    
    for cat in categories:
        if cat.id == category_id:
            return cat.nom
    
    return "Catégorie"


@register.simple_tag
def get_category_name_tag(categories, category_id):
    """
    Version simple tag pour récupérer le nom d'une catégorie
    """
    if not categories or not category_id:
        return "Catégorie"
    
    for cat in categories:
        if cat.id == category_id:
            return cat.nom
    
    return "Catégorie"