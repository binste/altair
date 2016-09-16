import os
import sys
import shutil
import warnings
import json

import traitlets

from os.path import abspath, join, dirname
sys.path.insert(1, abspath(join(dirname(__file__), '..')))
import altair

# Create a jinja filter to build an altair table
from jinja2 import Environment, Undefined, filters
from jinja2.filters import environmentfilter, make_attrgetter


@environmentfilter
def sphinx_table(env, iterable, columns, title_map=None):
    """Filter to generate a sphinx table"""
    title_map = title_map or {}

    rows = [[str(make_attrgetter(env, column)(row)) for column in columns]
            for row in iterable]
    titles = [title_map.get(col, col) for col in columns]
    lengths = [[len(item) for item in row] for row in rows]
    maxlengths = [max(col) for col in zip(*lengths)]

    def pad(row, fill=' '):
        return '  '.join(item.ljust(length, fill)
                         for item, length in zip(row, maxlengths))

    div = pad(['=', '=', '='], '=')

    return '\n'.join([div, pad(titles), div] + list(map(pad, rows)) + [div])


build_env = Environment()
build_env.filters['sphinx_table'] = sphinx_table


API_TEMPLATE = """
.. This document is auto-generated by the altair_apidoc extension. Do not modify directly.

.. API-reference:

Altair API Reference
====================

The following tables list the traits of Altairs fundamental objects.
Each Altair object mirrors a *definition* within the Vega-Lite schema, and
the attributes of the object mirror the available fields within the Vega-Lite
specification.

{% for group in objects|groupby('category') %}
{{ group.grouper[1] }}
{% for c in group.grouper[1] %}-{% endfor %}

{% for obj in group.list %}

.. _API-{{ obj.name }}:

{{ obj.name }}
{% for c in obj.name %}~{% endfor %}

{% if obj.description %}{{ obj.description }}{% endif %}

{{ obj.traits | sphinx_table(columns, title_map) }}

{% endfor %}
{% endfor %}
"""


# This holds info for how to build links to the Vega-Lite documentation
VEGALITE_DOC_URL = 'http://vega.github.io/vega-lite/docs/'
VEGALITE_DOC_PAGES = {'config': 'config.html#top-level-config',
                      'cellconfig': 'config.html#cell-config',
                      'markconfig': 'config.html#mark-config',
                      'scaleconfig': 'config.html#scale-config',
                      'axisconfig': 'config.html#axis-config',
                      'legendconfig': 'config.html#legend-config',
                      'facetconfig': 'config.html#facet-config'}

for attr in ['data', 'transform', 'mark', 'encoding', 'aggregate', 'bin',
             'sort', 'timeunit', 'scale', 'axis', 'legend']:
    VEGALITE_DOC_PAGES[attr] = attr + '.html'

for channel in ['color', 'column', 'detail', 'opacity', 'order', 'path',
                'row', 'shape', 'size', 'text', 'x', 'y']:
    VEGALITE_DOC_PAGES[channel] = 'encoding.html#def'


def _get_trait_info(name, trait):
    """Get a dictionary of info for an object trait"""
    type_ = trait.info()
    help_ = trait.help

    if isinstance(trait, traitlets.List):
        trait_info = _get_trait_info('', trait._trait)
        type_ = 'list of {0}'.format(trait_info['type'])
    elif isinstance(trait, traitlets.Enum):
        values = trait.values
        if all(isinstance(val, str) for val in values):
            type_ = 'string'
            help_ += ' One of {0}.'.format(values)
    elif isinstance(trait, traitlets.Union):
        trait_info = [_get_trait_info('', t) for t in trait.trait_types]
        type_ = ' or '.join(info['type'] for info in trait_info)
        help_ += '/'.join([info['help'] for info in trait_info
                           if info['help'] != '--'])
    elif isinstance(trait, traitlets.Instance):
        if issubclass(trait.klass, traitlets.HasTraits):
            type_ = ':ref:`API-{0}`'.format(trait.klass.__name__)

    type_ = type_.replace('a ', '')
    type_ = type_.replace('unicode string', 'string')
    return {'name': name, 'help': help_ or '--', 'type': type_ or '--'}


def _get_category(obj):
    """Get the category of an altair object"""
    from altair.schema._wrappers import named_channels, channel_collections

    name = obj.__name__

    if 'Chart' in name:
        return (0, 'Top Level Objects')
    elif name in dir(named_channels):
        return (2, 'Encoding Channels')
    elif name in dir(channel_collections):
        # out of order because encoding channels also appear here
        return (1, 'Channel Collections')
    elif 'Config' in name:
        return (3, 'Config Objects')
    else:
        return (4, 'Other Objects')


def _get_object_info(obj):
    """Get a dictionary of info for an object, suitable for the template"""
    D = {}
    name = obj.__name__
    D['name'] = name

    if name.lower() in VEGALITE_DOC_PAGES:
        url = VEGALITE_DOC_URL + VEGALITE_DOC_PAGES[name.lower()]
        D['description'] = ("(See also Vega-Lite's Documentation for "
                            "`{0} <{1}>`_)".format(name, url))

    D['traits'] = [_get_trait_info(name, trait)
                   for name, trait in sorted(obj.class_traits().items())]

    D['category'] = _get_category(obj)

    return D


def altair_nbdoc(obj):
    """Generate documentation for all objects in the namespace"""
    if obj is altair:
        for sub_obj in dir(obj):
            if not sub_obj.startswith('_'):
                # yield from altair_nbdoc(getattr(obj, sub_obj))
                for sub_sub_obj in altair_nbdoc(getattr(obj, sub_obj)):
                    yield sub_sub_obj
    elif isinstance(obj, type) and issubclass(obj, traitlets.HasTraits):
        yield _get_object_info(obj)


def create_doc_page(filename):
    is_toplevel = lambda obj: 'Chart' in obj['name']
    content = sorted(altair_nbdoc(altair),
                     key=lambda x: (x['category'], x['name']))

    columns = ['name', 'type', 'help']
    title_map = {'name':'Trait', 'type':'Type', 'help':'Description'}

    api_template = build_env.from_string(API_TEMPLATE)
    content = api_template.render(objects=content,
                                  columns=columns,
                                  title_map=title_map)

    with open(filename, 'w') as f:
        f.write(content)


def main(app):
    filename = app.builder.config.altair_api_file
    create_doc_page(filename)


def setup(app):
    app.connect('builder-inited', main)
    app.add_config_value('altair_api_file', 'API-reference.rst', 'env')
