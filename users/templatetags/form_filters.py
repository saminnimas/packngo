from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Add a CSS class to a form field widget."""
    if not hasattr(field, 'as_widget'):  # Check if it's a valid form field
        return field  # Return unchanged if not a field (e.g., a string)
    existing_classes = field.field.widget.attrs.get('class', '')
    new_classes = f"{existing_classes} {css_class}".strip()
    return field.as_widget(attrs={'class': new_classes})