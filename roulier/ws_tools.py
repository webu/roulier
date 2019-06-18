# -*- coding: utf-8 -*-
"""Utilities for WS."""
from lxml import etree
from lxml.objectify import BoolElement
from lxml.objectify import FloatElement
from lxml.objectify import IntElement
from lxml.objectify import NoneElement
from lxml.objectify import NumberElement
from lxml.objectify import ObjectifiedDataElement
from lxml.objectify import ObjectifiedElement

from jinja2 import Environment, PackageLoader
from zplgrf import GRF
from PIL import Image
from io import BytesIO
import email.parser
import re
import base64


def remove_empty_tags(xml, ouput_as_string=True):
    """Remove empty tags with xslt transformation.

    param: xml a string or a etree type
    return: unicode string or lxml.etree._XSLTResultTree
    """
    # use Jinja env for getting the path of template file
    # pkg_resouces may be an alternative, but we already
    # have Jinja
    env = Environment(
        loader=PackageLoader('roulier', 'templates'),
        extensions=['jinja2.ext.with_'])
    template = env.get_template("remove_empty_tags.xsl")
    xsl = etree.parse(open(template.filename))
    transform = etree.XSLT(xsl)

    if isinstance(xml, basestring):
        xml = etree.fromstring(xml)
    # else we asume xml is an lxml.etree
    if ouput_as_string:
        return unicode(transform(xml))
    else:
        return transform(xml)


def get_parts(response):
    """Extract parts from headers.

    Params:
        response: a request object
    Returns:
        an array of content-ids
    """
    head_lines = ''
    for k, v in response.raw.getheaders().iteritems():
        head_lines += str(k) + ':' + str(v) + '\n'

    full = head_lines + response.content

    parser = email.parser.Parser()
    decoded_reply = parser.parsestr(full)
    parts = {}
    start = decoded_reply.get_param('start').lstrip('<').rstrip('>')
    i = 0
    for part in decoded_reply.get_payload():
        cid = part.get('content-Id', '').lstrip('<').rstrip('>')
        if (not start or start == cid) and 'start' not in parts:
            parts['start'] = part.get_payload()
        else:
            parts[cid or 'Attachment%d' % i] = part.get_payload()
        i += 1
    return parts


def png_to_zpl(png, rotate):
    u"""Transform a PNG in a suitable format for ZPL.

    .png is converted to GRF format.
    Printing a Portable Network Graphics (PNG) with zpl instructions (like DY)
    is possible but hard (the spec is not really understandable).

    params:
        png : base64 encoded png
        rotate: boolean if true, rotate 90°

    returns:
        a ^GFA instruction with the image.
    """
    def base64_to_png(data):
        return BytesIO(base64.b64decode(data))

    def get_grf(png, rotate):
        u"""Get a GRF from a png.

        params:
            png: BytesIO stream
            rotate: rotate 90° if true
        """
        if rotate:
            png_bytes = BytesIO()
            (Image
                .open(png)
                .rotate(90, expand=True)
                .save(png_bytes, format="PNG"))
            png = png_bytes.getvalue()
            png_bytes.close()

        return GRF.from_image(png, 'DEMO')

    def build_gfa(grf):
        zpl = grf.to_zpl_line(compression=2)

        m = re.search('\~DGR:DEMO.GRF,(\d+),(\d+),(.*)$', zpl)
        size = m.group(1)
        width = m.group(2)
        payload = m.group(3)

        return '''^XA^FO00,00
^GFA,%(size)s,%(size)s,%(width)s,,%(payload)s^XZ''' % (
            {'size': size, 'width': width, 'payload': payload}
        )

    with base64_to_png(png) as png_stream:
        grf = get_grf(png_stream, rotate)
        zpl = build_gfa(grf)
    return zpl


def objectified_to_base_types(obj):
    # handle only ObjectifiedElement from lxml 
    # or multi-value structure that may contain ObjectifiedElements
    if not isinstance(obj, (list, tuple, set, dict, ObjectifiedElement)):
        return obj

    if isinstance(obj, IntElement):
        return int(obj)
    if isinstance(obj, (NumberElement, FloatElement)):
        return float(obj)
    if isinstance(obj, BoolElement):
        return bool(obj)
    if isinstance(obj, NoneElement):
        return None
    if isinstance(obj, ObjectifiedDataElement):
        return str(obj)

    if hasattr(obj, 'getchildren'):
        children_dict = {}
        for c in obj.iterchildren():
            # Manage lists
            if c.tag in children_dict:
                children_dict = [children_dict[c.tag], objectified_to_base_types(c)]
            else:
                children_dict[c.tag] = objectified_to_base_types(c)
            
        return children_dict
    if isinstance(obj, list):
        return [objectified_to_base_types(o) for o in obj]
    # Let python chose the str (__repr__ or __str__) of the obj if no structure is matched
    return '%s' % obj
