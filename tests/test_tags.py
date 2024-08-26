import pytest
from django.template import Context, Template

from tests.testapp.models import TodoItem
from tests.utils import assert_dom_equal
from template_simplify import dom_id

pytestmark = pytest.mark.django_db


def render(template, context):
    return Template(template).render(Context(context))


class TestDomId:
    def test_instance(self, todo):
        result = dom_id(todo)
        assert "todoitem_1" == result

        setattr(todo, "to_key", "test_1")  # noqa: B010
        result = dom_id(todo)
        assert "todoitem_test_1" == result

    def test_model(self):
        result = dom_id(TodoItem)
        assert "new_todoitem" == result

    def test_string(self):
        result = dom_id("test")
        assert "test" == result

    def test_prefix(self, todo):
        result = dom_id(todo, "test")
        assert "test_todoitem_1" == result

    def test_value_override(self):
        template = """
        {% load template_simplify %}

        {% dom_id first as dom_id %}
        <div id="{{ dom_id }}"></div>

        {% dom_id second as dom_id %}
        <div id="{{ dom_id }}"></div>

        <div id="{{ dom_id }}"></div>
        """
        output = render(
            template,
            {
                "first": "first",
                "second": "second",
            },
        ).strip()
        assert_dom_equal(
            output,
            '<div id="first"></div> <div id="second"></div> <div id="second"></div>',
        )


class TestClassNames:
    def test_logic(self):
        template = """
        {% load template_simplify %}

        <div class="{% class_names test1=True 'test2' "test3" test5=False ring-slate-900/5=True dark:bg-slate-800=True %}"></div>
        """
        output = render(template, {}).strip()
        assert_dom_equal(
            output,
            '<div class="test1 test2 test3 ring-slate-900/5 dark:bg-slate-800"></div>',
        )

