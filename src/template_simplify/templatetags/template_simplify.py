import re
from typing import Any, Optional

from django import template
from django.db.models.base import Model
from django.template import Node, TemplateSyntaxError

register = template.Library()


@register.simple_tag
def dom_id(instance: Any, prefix: Optional[str] = "") -> str:
    """
    Generate a unique identifier for a Django model instance, class, or even Python object.

    Args:
        instance (Any): The instance or class for which the identifier is generated.
        prefix (Optional[str]): An optional prefix to prepend to the identifier. Defaults to an empty string.

    Returns:
        str: The generated identifier.

    Raises:
        Exception: If the model instance does not have either the `to_key` or `pk` attribute.

    Note:
        - If `instance` is a Django model instance, the identifier is generated based on the `to_key` or `pk` attribute.
        - If `instance` is a Django model class, the identifier is generated as `new_<class_name>`.
        - If `instance` is neither a model instance nor a model class, the identifier is generated based on the `to_key`
          attribute if available, otherwise it uses the string representation of the instance.
        - The `prefix` argument can be used to prepend a prefix to the generated identifier.
    """
    if not isinstance(instance, type) and isinstance(instance, Model):
        # Django model instance
        if hasattr(instance, "to_key") and getattr(instance, "to_key"):  # noqa: B009
            identifier = f"{instance.__class__.__name__.lower()}_{instance.to_key}"
        elif hasattr(instance, "pk") and getattr(instance, "pk"):  # noqa: B009
            identifier = f"{instance.__class__.__name__.lower()}_{instance.pk}"
        else:
            raise Exception(
                f"Model instance must have either to_key or pk attribute {instance}"
            )
    elif isinstance(instance, type) and issubclass(instance, Model):
        # Django model class
        identifier = f"new_{instance.__name__.lower()}"
    else:
        if hasattr(instance, "to_key") and getattr(instance, "to_key"):  # noqa: B009
            # Developer can still use to_key property to generate the identifier
            identifier = f"{instance.to_key}"
        else:
            # Use the string representation
            identifier = str(instance)

    if prefix:
        identifier = f"{prefix}_{identifier}"

    return identifier


ATTRIBUTE_RE = re.compile(
    r"""
    (?P<attr>
        [@\w:_\.\/-]+
    )
    (?P<sign>
        \+?=
    )
    (?P<value>
    ['"]? # start quote
        [^"']*
    ['"]? # end quote
    )
""",
    re.VERBOSE | re.UNICODE,
)


VALUE_RE = re.compile(
    r"""
    ['"]            # start quote (required)
    (?P<value>
        [^"']*      # match any character except quotes
    )
    ['"]            # end quote (required)
    """,
    re.VERBOSE | re.UNICODE,
)


@register.tag
def class_names(parser, token):
    error_msg = f"{token.split_contents()[0]!r} tag requires " "a list of css classes"
    try:
        bits = token.split_contents()
        tag_name = bits[0]  # noqa
        attr_list = bits[1:]
    except ValueError as exc:
        raise TemplateSyntaxError(error_msg) from exc

    css_ls = []
    css_dict = {}
    for pair in attr_list:
        attribute_match = ATTRIBUTE_RE.match(pair) or VALUE_RE.match(pair)

        if attribute_match:
            dct = attribute_match.groupdict()
            attr = dct.get("attr", None)
            # sign = dct.get("sign", None)
            value = parser.compile_filter(dct["value"])
            if attr:
                css_dict[attr] = value
            else:
                css_ls.append(value)
        else:
            raise TemplateSyntaxError("class_names found supported token: " + f"{pair}")

    return ClassNamesNode(css_ls=css_ls, css_dict=css_dict)


class ClassNamesNode(Node):
    def __init__(self, css_ls, css_dict):
        self.css_ls = css_ls
        self.css_dict = css_dict

    def render(self, context):
        final_css = []

        # for common css classes
        for value in self.css_ls:
            final_css.append(value.token)

        # for conditionals
        for attr, expression in self.css_dict.items():
            real_value = expression.resolve(context)
            if real_value:
                final_css.append(attr)

        return " ".join(final_css)
