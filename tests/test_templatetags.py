
from django import forms
from django.db import models
from django.test import TestCase
from django.template import Context, Template
from silica.django_app.models import BaseModel


class Thingy(object):
    """ a class for tests """
    name = ""
    description = ""

    def __init__(self, name, description=""):
        self.name = name
        self.description = description


class PlainModelThingy(models.Model):
    """ a model for tests """
    name = models.CharField()
    created_on = models.DateTimeField(auto_now_add=True)


class SilicaModelThingy(BaseModel):
    """ a silica model for tests """
    name = models.CharField()
    created_on = models.DateTimeField(auto_now_add=True)


class SampleForm(forms.Form):
    """ a django form for tests """
    name = forms.CharField(label='Your name', max_length=100)


class TagHelper(TestCase):
    """ base class for templatetag tests """

    def tag_test(self, template, context, output):
        t = Template('{% load silica %}'+template)
        c = Context(context)
        self.assertEqual(t.render(c), output)


class FilterTagTests(TagHelper):
    """ basic integration tests for django filter templatetags """

    def test_getattr_tag(self):
        thingy = Thingy(name=u"Ned")
        template = "{{ thingy|getattr:'name' }}"
        context = {'thingy': thingy}
        output = u"Ned"
        self.tag_test(template, context, output)

    def test_getitem_tag(self):
        thingy = {'name': u"Fred", 'label': u"Foo"}
        template = "{{ thingy|getitem:'label' }}"
        context = {'thingy': thingy}
        output = u"Foo"
        self.tag_test(template, context, output)

    def test_title_space_tag(self):
        template = "{{ title|title_space }}"
        context = {'title': "Hi_There"}
        output = u"Hi There"
        self.tag_test(template, context, output)
        # spaces are left intact
        context = {'title': "Hello There"}
        output = u"Hello There"
        self.tag_test(template, context, output)
        # String is expressed in title case
        context = {'title': "HOW_are_yOu?"}
        output = u"How Are You?"
        self.tag_test(template, context, output)

    def test_get_django_field_tag(self):
        # TODO test different field types
        thingy = SilicaModelThingy(name="Wood chip")
        template = "{{ thingy|get_django_field:'name' }}"
        context = {'thingy': thingy}
        output = u"Wood chip"
        self.tag_test(template, context, output)


class AngularModelTagTests(TagHelper):
    """ basic integration tests for angular_model tag """

    def test_empty_model_renders_empty(self):
        template = "{% angular_model model model_name params %}"
        context = {'model_name': 'larry', 'model': None}
        output = "<script>\nwindow.larry = {};\n</script>\n"
        self.tag_test(template, context, output)

    def test_ordinary_model_raises_exception(self):
        thingy = PlainModelThingy(name="Carl Perkins")
        template = "{% angular_model model model_name params %}"
        context = {'model_name': 'carl', 'model': thingy}
        output = "<script>\nwindow.carl = {};\n</script>\n"
        # TODO: is this the appropriate behavior?
        with self.assertRaises(AttributeError):
            self.tag_test(template, context, output)

    def test_silica_model_renders_correctly(self):
        # TODO: use a more complex model here
        # TODO: add unit tests for the BaseModel.to_json method
        thingy = SilicaModelThingy(name="Carl Perkins")
        template = "{% angular_model model model_name params %}"
        context = {'model_name': 'carl', 'model': thingy}
        output = (u'<script>\nwindow.carl = {"fields": {"created_on": null, '
                  u'"name": "Carl Perkins"}, '
                  u'"model": "tests.silicamodelthingy", '
                  u'"pk": null};\nwindow.carl.fields.created_on '
                  u'= new Date(window.carl.fields.created_on);\n</script>\n')
        self.tag_test(template, context, output)


class AngularInputFieldTagTests(TagHelper):
    """ basic integration tests for angular_input_field tag """
    # TODO: add unit tests
    # TODO: test unbound form and other edge cases

    def test_angular_input_field(self):
        my_form = SampleForm()
        template = u'{% angular_input_field my_form.name model_name params %}'
        context = {'my_form': my_form,
                   'model_name': 'yourname',
                   'params': {}}
        output = (u'<input class="form-control" id="id_name" maxlength="100" '
                  u'name="name" ng-model="yourname.fields.name" '
                  u'required="true" type="text" />')
        self.tag_test(template, context, output)
        # repeat test, with bound form
        my_form = SampleForm({'name': 'Joe Bloggs'})
        self.tag_test(template, context, output)
