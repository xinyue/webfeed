import lxml.html
import webapp2
import logging
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import urlfetch

class Link(ndb.Model):
    url = ndb.StringProperty(indexed=True)

def get_urls(from_url, to_prefix):
    html = lxml.html.fromstring(urlfetch.fetch(from_url, validate_certificate=False).content)
    logging.debug('Downloaded %s' % from_url)
    html.make_links_absolute(from_url)
    urls = html.xpath('//a/@href')
    matching_urls = []
    for url in urls:
        logging.debug('URL: %s' % url)
        if url.startswith(to_prefix):
            matching_urls.append(str(url))
    return matching_urls

def get_page_title(url):
    html = lxml.html.fromstring(urlfetch.fetch(url, validate_certificate=False).content)
    logging.debug('Downloaded %s' % url)
    page_title = html.xpath("//title")[0].text
    logging.debug('Title: %s' % page_title)
    return str(page_title)

def main(from_url, to_prefix, from_email, to_email, subject_prefix):
    logging.getLogger().setLevel(logging.DEBUG)
    urls = get_urls(from_url, to_prefix)
    for url in urls:
        if len(Link.query(Link.url == url).fetch(1)) == 0:
            title = get_page_title(url)
            subject = "[%s] %s" % (subject_prefix, title)
            body = url
            mail.send_mail(from_email, to_email, subject, body)
            Link(url=url).put()

class Bluesnews(webapp2.RequestHandler):
    def get(self):
        main(from_url='http://bluesnews.com',
             to_prefix='https://www.youtube.com',
             from_email='Bluesnews Youtube Watcher <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='bluesnews')

class PirateBay(webapp2.RequestHandler):
    def get(self):
        main(from_url='https://thepiratebay.se/top/207',
             to_prefix='https://thepiratebay.se/torrent',
             from_email='PirateBay Watcher <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='pirate_bay')

app = webapp2.WSGIApplication([
    ('/bluesnews', Bluesnews),
    ('/pirate_bay', PirateBay),
], debug=True)
