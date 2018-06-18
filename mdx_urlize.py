# encoding: utf-8
"""A more liberal autolinker

Inspired by Django's urlize function.

Positive examples:

>>> import markdown
>>> md = markdown.Markdown(extensions=['urlize'])

>>> md.convert('http://example.com/')
u'<p><a href="http://example.com/">http://example.com/</a></p>'

>>> md.convert('go to http://example.com')
u'<p>go to <a href="http://example.com">http://example.com</a></p>'

>>> md.convert('example.com')
u'<p><a href="http://example.com">example.com</a></p>'

>>> md.convert('example.net')
u'<p><a href="http://example.net">example.net</a></p>'

>>> md.convert('www.example.us')
u'<p><a href="http://www.example.us">www.example.us</a></p>'

>>> md.convert('(www.example.us/path/?name=val)')
u'<p>(<a href="http://www.example.us/path/?name=val">www.example.us/path/?name=val</a>)</p>'

>>> md.convert('go to <http://example.com> now!')
u'<p>go to <a href="http://example.com">http://example.com</a> now!</p>'

Negative examples:

>>> md.convert('del.icio.us')
u'<p>del.icio.us</p>'

"""

import markdown

# Global Vars
URLIZE_RE = '(%s)' % '|'.join([
    r'(?im)((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>，。（）]+|\([^\s()<>，。（）]+\))+(?:\([^\s()<>，。（）]+\)|[^\u4e00-\u9fa5，。（）\s`!()\[\]{};:\'".,<>?]))'
])

class UrlizePattern(markdown.inlinepatterns.Pattern):
    """ Return a link Element given an autolink (`http://example/com`). """
    def handleMatch(self, m):
        url = m.group(2)
        
        if url.startswith('<'):
            url = url[1:-1]
            
        text = url
        
        if not url.split('://')[0] in ('http','https','ftp'):
            if '@' in url and not '/' in url:
                url = 'mailto:' + url
            else:
                url = 'http://' + url
    
        el = markdown.util.etree.Element("a")
        el.set('href', url)
        el.set('target', '_blank')
        el.text = markdown.util.AtomicString(text)
        return el

class UrlizeExtension(markdown.Extension):
    """ Urlize Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Replace autolink with UrlizePattern """
        md.inlinePatterns['autolink'] = UrlizePattern(URLIZE_RE, md)

def makeExtension(*args, **kwargs):
    return UrlizeExtension(*args, **kwargs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
