import warnings
import weakref
from twisted.trial import unittest
from scrapy.http import TextResponse, HtmlResponse, XmlResponse
from scrapy.selector import Selector
from lxml import etree


class SelectorTestCase(unittest.TestCase):

    def test_simple_selection(self):
        """Simple selector tests"""
        body = b"<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        response = TextResponse(url="http://example.com", body=body, encoding='utf-8')
        sel = Selector(response)

        xl = sel.xpath('//input')
        self.assertEqual(2, len(xl))
        for x in xl:
            assert isinstance(x, Selector)

        self.assertEqual(sel.xpath('//input').getall(),
                         [x.get() for x in sel.xpath('//input')])

        self.assertEqual([x.get() for x in sel.xpath("//input[@name='a']/@name")],
                         [u'a'])
        self.assertEqual([x.get() for x in sel.xpath("number(concat(//input[@name='a']/@value, //input[@name='b']/@value))")],
                         [u'12.0'])

        self.assertEqual(sel.xpath("concat('xpath', 'rules')").getall(),
                         [u'xpathrules'])
        self.assertEqual([x.get() for x in sel.xpath("concat(//input[@name='a']/@value, //input[@name='b']/@value)")],
                         [u'12'])

    def test_root_base_url(self):
        body = b'<html><form action="/path"><input name="a" /></form></html>'
        url = "http://example.com"
        response = TextResponse(url=url, body=body, encoding='utf-8')
        sel = Selector(response)
        self.assertEqual(url, sel.root.base)

    def test_flavor_detection(self):
        text = b'<div><img src="a.jpg"><p>Hello</div>'
        sel = Selector(XmlResponse('http://example.com', body=text, encoding='utf-8'))
        self.assertEqual(sel.type, 'xml')
        self.assertEqual(sel.xpath("//div").getall(),
                         [u'<div><img src="a.jpg"><p>Hello</p></img></div>'])

        sel = Selector(HtmlResponse('http://example.com', body=text, encoding='utf-8'))
        self.assertEqual(sel.type, 'html')
        self.assertEqual(sel.xpath("//div").getall(),
                         [u'<div><img src="a.jpg"><p>Hello</p></div>'])

    def test_http_header_encoding_precedence(self):
        # u'\xa3'     = pound symbol in unicode
        # u'\xc2\xa3' = pound symbol in utf-8
        # u'\xa3'     = pound symbol in latin-1 (iso-8859-1)

        meta = u'<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'
        head = u'<head>' + meta + u'</head>'
        body_content = u'<span id="blank">\xa3</span>'
        body = u'<body>' + body_content + u'</body>'
        html = u'<html>' + head + body + u'</html>'
        encoding = 'utf-8'
        html_utf8 = html.encode(encoding)

        headers = {'Content-Type': ['text/html; charset=utf-8']}
        response = HtmlResponse(url="http://example.com", headers=headers, body=html_utf8)
        x = Selector(response)
        self.assertEqual(x.xpath("//span[@id='blank']/text()").getall(),
                          [u'\xa3'])

    def test_badly_encoded_body(self):
        # \xe9 alone isn't valid utf8 sequence
        r1 = TextResponse('http://www.example.com',
                          body=b'<html><p>an Jos\xe9 de</p><html>',
                          encoding='utf-8')
        Selector(r1).xpath('//text()').getall()

    def test_weakref_slots(self):
        """Check that classes are using slots and are weak-referenceable"""
        x = Selector(text='')
        weakref.ref(x)
        assert not hasattr(x, '__dict__'), "%s does not use __slots__" % \
            x.__class__.__name__

    def test_selector_bad_args(self):
        with self.assertRaisesRegexp(ValueError, 'received both response and text'):
            Selector(TextResponse(url='http://example.com', body=b''), text=u'')
