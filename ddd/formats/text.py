# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2023

import logging
from abc import abstractclassmethod, abstractstaticmethod

from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.formats.json import DDDJSONFormat

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDTextTemplateFormatBase():
    """
    Generates a text document for the given scene, using a template.

    This is an abstract class, a subclass is used for a particular template engine.
    """

    @staticmethod
    def export_text(obj, path_prefix="", instance_mesh=True, instance_marker=False):

        from ddd.ddd import D1D2D3

        # Export to JSON first, to have a data structure to work with
        # TODO: FIXME: is this needed? shall we expose the data directly?
        data = DDDJSONFormat.export_data(obj, path_prefix, "", instance_mesh, instance_marker)

        # Get jinja template from ddd property
        template_path = obj.get('ddd:output:text:template:path', None)
        template_content = obj.get('ddd:output:text:template:content', None)
        
        if template_path:
            # Read template from file
            with open(template_path, "r") as f:
                template_content = f.read()
        if not template_content:
            raise DDDException("No template provided for text output.")
        
        # Render template
        template_engine_format_class = DDDTextMakoTemplateFormat
        text = template_engine_format_class.render_template(template_content, obj, data)

        return text
    
    @abstractstaticmethod
    def render_template(template_content, obj, data):
        """
        Renders a template using the given data.
        """
        raise NotImplementedError("Abstract method.")



class DDDTextMakoTemplateFormat(DDDTextTemplateFormatBase):
    """
    Generates a text document for the given scene, using a template.

    Uses Mako as rendering engine.
    """

    # TODO: remember to check word-wrapping + indenting for long texts, etc,
    DEFAULT_TEMPLATE = """
        <% for task in data['pipeline']['tasks']: %>
        ${ task['name'] }
        <% if task['description']: %>
            ${ task['description'] }
        <% endif %>
        <% endfor %>
    """

    @staticmethod
    def render_template(template_content, obj, data):
        """
        Renders a Mako template using the given data.
        """
        from io import StringIO

        from mako.runtime import Context
        from mako.template import Template

        template = Template(template_content)
        buf = StringIO()
        ctx = Context(buf, obj=obj, data=data)
        template.render_context(ctx)
        text = buf.getvalue()
        return text


class DDDTextJinjaTemplateFormat(DDDTextTemplateFormatBase):
    """
    Generates a text document for the given scene, using a template.

    Uses Jinja2 as rendering engine.
    """

    # TODO: remember to check word-wrapping + indenting for long texts, etc,
    DEFAULT_TEMPLATE = """
        {%- filter wordwrap(width=72, break_long_words=False) -%}
        {% block greeting -%}
        {% trans full_name = _(user.full_name) %}Hello {{ full_name }},{% endtrans %}
        {% endblock -%}
        
        {{ obj.name }} ({{ obj.id }}) is a {{ obj.get('ddd:category') }}.
    """

    @staticmethod
    def render_template(template_content, obj, data):
        """
        Renders a template using the given data.
        """
        import jinja2
        template = jinja2.Template(template_content)
        text = template.render(obj=obj, data=data)
        return text