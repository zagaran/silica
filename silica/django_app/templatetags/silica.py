from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html, mark_safe
from django.forms import DateField, DateTimeField, ModelChoiceField, ModelMultipleChoiceField
from django.db import models

import json

register = template.Library()

@register.filter(name="getattr")
def template_getattr(obj, attr_name):
    return getattr(obj, attr_name)

@register.filter(name="getitem")
def template_getitem(obj, item_name):
    return obj[item_name]

@register.filter(name="title_space")
@stringfilter
def title_space(string):
    return string.replace("_", " ").title()

@register.filter(name="get_django_field")
def template_get_django_field(obj, field):
    val = getattr(obj, field)
    if field in obj.get_many_to_many_fields():
        return val.all()
    return val

@register.simple_tag(name="angular_model")
def angular_model(model, angular_model_name, extra_params={}):
    # returns javascript that preprocesses obj before attaching it to window where angular controller can grab it
    # TODO: would like to use ng-init instead of this
    # TODO: prevent dates from showing up one day off in certain timezones
    # TODO: prepend namespace strings to window variables
    # TODO: don't rely on JS date parsing
    ret = "<script>\n"
    if model is None:
        ret += "window.%s = {};\n" % (angular_model_name)
    else:
        # cast foreign key and m2m fields to be strings
        json_ret = model.to_json()
        model_dict = json.loads(json_ret)
        fk_fields = model.get_foreign_key_fields()
        m2m_fields = model.get_many_to_many_fields()
        for field, val in model_dict["fields"].iteritems():
            if field in fk_fields:
               model_dict["fields"][field] = str(val)
            if field in m2m_fields:
                model_dict["fields"][field] = map(str, val)
        ret += "window.%s = %s;\n" % (angular_model_name, json.dumps(model_dict))
        # adds converter for datetime fields
        for field in model.READABLE_ATTRS(type_filter=models.DateField):
            # DateTimeFields are instances of DateFields
            ret += ("window.%s.fields.%s = new Date(window.%s.fields.%s);\n" %
                    (angular_model_name, field, angular_model_name, field))
    # date_fields = model.WRITEABLE_ATTRS(type_filter=models.DateField, type_exclude=models.DateTimeField)
    # date_fields = json.dumps(date_fields)
    # ret += "window.%s.date_fields = %s" % (angular_model_name, date_fields)
    ret += "</script>\n"
    return mark_safe(ret)


@register.simple_tag(name="angular_input_field")
def angular_input_field(form_field, angular_model_name, extra_params={}):
    # TODO: Integrate with angular form validation
    # TODO: Add time picker https://angular-ui.github.io/bootstrap
    # TODO: ng-options
    # TODO: angular side toLocaleDateString() for DateField
    # TODO: ng validation messages for more than just required
    # TODO: figure out what to do about angular's timezone support
    # TODO: test extra params
    # TODO: fix double datepicker on chrome
    # TODO: Investigate converting dates in angular controller http://stackoverflow.com/a/15346236/2800876
    
    try:
        form_field_value = form_field.value
        form_field.value = lambda: None
        attrs = {"ng-model": "%s.fields.%s" % (angular_model_name, form_field.name),
                 "class": "form-control"}
        if form_field.field.required:
            attrs["required"] = "true"
        if isinstance(form_field.field, DateTimeField):
            separator = extra_params.pop("silica_datetime_separator", "")
            widget1 = _get_datepicker(form_field, attrs, extra_params)
            attrs["type"] = "time"
            attrs.update(extra_params)
            widget2 = form_field.as_widget(attrs=attrs)
            return format_html(widget1 + separator + widget2)
        if isinstance(form_field.field, DateField):
            return format_html(_get_datepicker(form_field, attrs, extra_params))
        if isinstance(form_field.field, ModelChoiceField):
            pass
            #return format_html(_get_datepicker(form_field, attrs, extra_params))
        if isinstance(form_field.field, ModelMultipleChoiceField):
            pass
            #return format_html(_get_datepicker(form_field, attrs, extra_params))
        attrs.update(extra_params)
        return format_html(form_field.as_widget(attrs=attrs))
    finally:
        form_field.value = form_field_value

def _get_datepicker(form_field, attrs, extra_params):
    attrs = dict(attrs)
    calendar_button = extra_params.pop("silica_calendar_button", True)
    attrs["type"] = "date"
    attrs["placeholder"] = "yyyy-mm-dd"
    attrs["uib-datepicker-popup"] = ""
    attrs["datepicker-options"] = "dateOptions"
    attrs["is-open"] = "_calendar_widgets[%s]" % id(form_field)
    attrs["ng-click"] = "_calendar_widgets[%s]=true" % id(form_field)
    # attrs["class"] += " datepicker"
    attrs.update(extra_params)
    ret = form_field.as_widget(attrs=attrs)
    if calendar_button:
        ret = """<div class="input-group">""" + ret
        ret += """<span class="input-group-btn"><button type="button" class="btn btn-default" ng-click="_calendar_widgets[%s]=true">
                  <i class="glyphicon glyphicon-calendar"></i></button></span>""" % id(form_field)
        ret += "</div>"
    return ret
