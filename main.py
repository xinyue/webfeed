import lxml.html
import webapp2
import logging
import json
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import urlfetch

class Link(ndb.Model):
    url = ndb.StringProperty(indexed=True)

def get_urls(html, to_prefix, xpath):
    urls = html.xpath(xpath)
    matching_urls = []
    for url in urls:
        logging.debug('URL: %s' % url)
        if url.startswith(to_prefix):
            matching_urls.append(str(url))
    return matching_urls

def get_html(url):
    html = lxml.html.fromstring(urlfetch.fetch(url, validate_certificate=False).content)
    logging.debug('Downloaded %s' % url)
    html.make_links_absolute(url)
    return html

def get_title(html):
    page_title = html.xpath("//title")[0].text.encode('utf-8')
    logging.debug('Title: %s' % page_title)
    return page_title

def get_json(url):
    return json.loads(urlfetch.fetch(url, validate_certificate=False).content)

def get_hn_post(post_id):
    url = 'https://hacker-news.firebaseio.com/v0/item/%s.json' % post_id
    return get_json(url)

def main(from_url, xpath, to_prefix, replace_with, attach_url_prefix, from_email, to_email, subject_prefix):
    logging.getLogger().setLevel(logging.DEBUG)
    urls = get_urls(get_html(from_url), to_prefix, xpath)
    for url in urls:
        if len(Link.query(Link.url == url).fetch(1)) == 0:
            html = get_html(url)
            title = get_title(html)
            subject = "[%s] %s" % (subject_prefix, title)
            attach_url = None
            if attach_url_prefix is not None:
                attach_urls = get_urls(html, attach_url_prefix)
                if (len(attach_urls) > 0):
                    attach_url = attach_urls[0]
            if replace_with is not None:
                body = url.replace(to_prefix, replace_with)
            else:
                body = url
            if attach_url is not None:
                body += "\n\n%s" % attach_url
            mail.send_mail(from_email, to_email, subject, body)
            Link(url=url).put()

class Bluesnews(webapp2.RequestHandler):
    def get(self):
        main(from_url='http://bluesnews.com',
             xpath='//a/@href',
             to_prefix='https://www.youtube.com',
             replace_with=None,
             attach_url_prefix=None,
             from_email='Bluesnews Youtube Watcher <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='bluesnews')

class Piratebay(webapp2.RequestHandler):
    def get(self):
        main(from_url='https://thepiratebay.se/top/207',
             xpath='//a/@href',
             to_prefix='https://thepiratebay.se/torrent',
             replace_with='https://pirateproxy.tv/torrent',
             attach_url_prefix='http://www.imdb.com',
             from_email='PirateBay Watcher <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='piratebay')

class Redlettermedia(webapp2.RequestHandler):
    def get(self):
        main(from_url='http://redlettermedia.com',
             xpath='//iframe/@src',
             to_prefix='https://www.youtube.com/embed/',
             replace_with='https://www.youtube.com/watch?v=',
             attach_url_prefix=None,
             from_email='RedLetterMedia Watcher <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='redlettermedia')

class Hackernews(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        top_post_ids = get_json('https://hacker-news.firebaseio.com/v0/topstories.json')
        for i in xrange(30):
            post_id = top_post_ids[i]
            post = get_hn_post(post_id)
            self.response.write('%s - %s\n' % (post['title'], post['score']))
            if int(post['score']) >= 60:
                self.response.write('+ qualifies\n')
                if len(Link.query(Link.url == post['url']).fetch(1)) == 0:
                    self.response.write('+ not seen, emailing\n')
                    hn_url = 'https://news.ycombinator.com/item?id=%s' % post['id']
                    subject = "[hackernews] %s" % post['title']
                    body = '%s\n\n%s' % (hn_url, post['url'])
                    from_email = 'Hacker News Watcher <mtrencseni@gmail.com>'
                    to_email = 'Marton Trencseni <mtrencseni@gmail.com>'
                    mail.send_mail(from_email, to_email, subject, body)
                    Link(url=post['url']).put()
                    self.response.write('+ saved\n')
                else:
                    self.response.write('- already seen\n')
            else:
                self.response.write('- does not qualify\n')

app = webapp2.WSGIApplication([
    ('/bluesnews', Bluesnews),
    ('/piratebay', Piratebay),
    ('/redlettermedia', Redlettermedia),
    ('/hackernews', Hackernews),
], debug=True)
