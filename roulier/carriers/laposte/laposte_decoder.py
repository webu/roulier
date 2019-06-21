# -*- coding: utf-8 -*-
"""Laposte XML -> Python."""
from lxml import objectify
from roulier.codec import Decoder
from roulier.ws_tools import objectified_to_base_types


class LaposteDecoder(Decoder):
    """Laposte XML -> Python."""

    def decode(self, body, parts, output_format):
        """Laposte XML -> Python."""
        def get_product_inter(msg):
            """Understand a getProductInterResponse."""
            x = {
                "product": msg.product,
                "partnerType": msg.partnerType
            }
            return x

        def generate_label_response(msg):
            """Understand a generateLabelResponse."""
            def get_cid(tag, tree):
                element = tree.find(tag)
                if element is None:
                    return None
                href = element.getchildren()[0].attrib['href']
                # href contains cid:236212...-38932@cfx.apache.org
                return href[len('cid:'):]  # remove prefix
            rep = objectified_to_base_types(msg.labelResponse)
            cn23_cid = get_cid('cn23', msg.labelResponse)
            label_cid = get_cid('label', msg.labelResponse)

            annexes = []

            if cn23_cid:
                annexes.append({
                    "name": 'cn23',
                    "data": parts.get(cn23_cid),
                    "type": "pdf"
                })

            if rep.get('pdfUrl'):
                annexes.append({
                    "name": "label",
                    "data": rep.get('pdfUrl'),
                    "type": "url"
                })
            
            return {
                "tracking": {
                    "number": rep.get('parcelNumber'),
                    "partner": rep.get('parcelNumberPartner'),
                },
                "label": {  # main label
                    "name": "label",
                    "data": parts.get(label_cid),
                    "type": output_format
                },
                "parcels": [{
                    "id": 1,
                    "number": rep.get('parcelNumber'),
                    "reference": "",
                    "label": {  # same as main label
                        "name": "label_1",
                        "data": parts.get(label_cid),
                        "type": output_format,
                    }

                }],
                "annexes": annexes
            }

        xml = objectify.fromstring(body)
        tag = xml.tag
        lookup = {
            "{http://sls.ws.coliposte.fr}getProductInterResponse":
                get_product_inter,
            "{http://sls.ws.coliposte.fr}generateLabelResponse":
                generate_label_response
        }
        return lookup[tag](xml.xpath('//return')[0])
