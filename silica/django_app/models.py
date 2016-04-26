"""
The MIT License (MIT)

Copyright (c) 2016 Zagaran, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

@author: Zags (Benjamin Zagorsky)
"""

import json

from django.db import models
from django.core import serializers
from itertools import chain

class BaseModel(models.Model):
    class Meta:
        abstract = True
    
    @classmethod
    def READABLE_ATTRS(cls, type_filter=None, type_exclude=None):
        return cls._attrs_filter(lambda f: f.serialize,
                                 type_filter=type_filter, type_exclude=type_exclude)
    
    @classmethod
    def WRITEABLE_ATTRS(cls, type_filter=None, type_exclude=None):
        return cls._attrs_filter(lambda f: f.serialize and f.editable,
                                 type_filter=type_filter, type_exclude=type_exclude)
    
    @classmethod
    def READONLY_ATTRS(cls, type_filter=None, type_exclude=None):
        return cls._attrs_filter(lambda f: f.serialize and not f.editable,
                                 type_filter=type_filter, type_exclude=type_exclude)
    
    @classmethod
    def _attrs_filter(cls, filter_function, type_filter=None, type_exclude=None):
        def combined_filter(f):
            if not filter_function:
                return False
            if type_filter is not None and not isinstance(f, type_filter):
                return False
            if type_exclude is not None and isinstance(f, type_exclude):
                return False
            return True
        return [f.name for f in chain(cls._meta.fields, cls._meta.many_to_many) if combined_filter(f)]
    
    @classmethod
    def create_from_json(cls, json_str):
        model = json.loads(json_str)
        params_dict = model["fields"]
        many_to_many_dict = cls.prep_many_to_many_save(params_dict)
        # _clean_json_payload pops the m2m fields
        params_dict = cls._clean_json_payload(params_dict)
        ret = cls.objects.create(**params_dict)
        # we have to do many to many field separately because obj does not exist yet otherwise
        ret.do_many_to_many_save(many_to_many_dict)
        return ret

    @classmethod
    def get_foreign_key_fields(cls):
        return {f.name: f.related_model for f in cls._meta.fields if isinstance(f, models.ForeignKey)}

    @classmethod
    def get_many_to_many_fields(cls):
        return {f.name: f.related_model for f in cls._meta.many_to_many}

    @classmethod
    def _clean_json_payload(cls, params_dict):
        writeables = cls.WRITEABLE_ATTRS()
        date_fixes = cls.WRITEABLE_ATTRS(type_filter=models.DateField, type_exclude=models.DateTimeField)
        foreign_key_fields = cls.get_foreign_key_fields()
        many_to_many_fields = cls.get_many_to_many_fields()
        for key in params_dict.keys():
            if key not in writeables or key in many_to_many_fields:
                # pop the not-writable and m2m fields
                params_dict.pop(key)
            if key in date_fixes:
                # Strip part the time portion of the ISO timestamp
                params_dict[key] = params_dict[key].split("T")[0]
            if key in foreign_key_fields:
                params_dict[key] = foreign_key_fields[key].objects.get(pk=params_dict[key])
        return params_dict

    @classmethod
    def prep_many_to_many_save(cls, params_dict):
        many_to_many_dict = {}
        many_to_many_fields = cls.get_many_to_many_fields()
        for key in params_dict.keys():
            if key in many_to_many_fields:
                many_to_many_dict[key] = many_to_many_fields[key].objects.filter(pk__in=params_dict[key])
        return many_to_many_dict

    def do_many_to_many_save(self, many_to_many_dict):
        for field, objs in many_to_many_dict.iteritems():
            getattr(self, field).set(objs)

    def update(self, update_dict=None, **kwargs):
        """ Helper method to update objects """
        if not update_dict:
            update_dict = kwargs
        update_fields = set()
        for k, v in update_dict.iteritems():
            setattr(self, k, v)
            update_fields.add(k)
        self.save(update_fields=update_fields)
    
    def to_json(self):
        """ Returns a json representation of the object """
        # Serialize takes a list; we want just a single object
        return serializers.serialize("json", [self])[1:-1]
    
    def update_from_json(self, update_json):
        model = json.loads(update_json)
        params_dict = model["fields"]
        many_to_many_dict = self.prep_many_to_many_save(params_dict)
        params_dict = self._clean_json_payload(params_dict)
        self.update(params_dict)
        self.do_many_to_many_save(many_to_many_dict)


class TimestampedModel(BaseModel):
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
    updated_on = models.DateTimeField(auto_now=True, editable=False)
    
    class Meta:
        abstract = True
    
    def update(self, update_dict=None, **kwargs):
        """ Helper method to update objects """
        if not update_dict:
            update_dict = kwargs
        update_fields = {"updated_on"}
        for k, v in update_dict.iteritems():
            setattr(self, k, v)
            update_fields.add(k)
        self.save(update_fields=update_fields)
