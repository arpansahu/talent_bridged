from django import template

register = template.Library()


@register.filter
def calculate_percentage(pages, read, *args):
    return ((read/pages) * 100)

@register.filter
def other_member(members, current_member):
    return members.exclude(id=current_member.id).first()