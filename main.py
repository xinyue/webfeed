import traceback
import lxml.html
import webapp2
import logging
import json
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import urlfetch

class Link(ndb.Model):
    url = ndb.StringProperty(indexed=True)

pirate_bay_proxies = [
    'https://thepiratebay.se',
    'https://pirateproxy.tv',
    'http://tpb.portalimg.com/?load=',
    'https://thepiratebay.run/?load=',
    'https://pbp.wtf',
    'https://bayproxy.link',
    'https://tpb.press'
    ]
pi = 0

def url_fetch(url):
    # huge hack
    global pi
    for i in xrange(len(pirate_bay_proxies)):
        try:
            url = url.replace('https://thepiratebay.se', pirate_bay_proxies[pi])
            return urlfetch.fetch(url, validate_certificate=False).content
        except Exception, e:
            logging.debug('url_fetch exception: %s' % e)
            # try another proxy
            pi = (pi + 1) % len(pirate_bay_proxies)
    raise Exception

def get_urls(html, to_prefix, xpath='//a/@href'):
    urls = html.xpath(xpath)
    matching_urls = []
    for url in urls:
        logging.debug('URL: %s' % url)
        if url.startswith(to_prefix):
            matching_urls.append(str(url))
    return matching_urls

def get_html(url):
    html = lxml.html.fromstring(url_fetch(url))
    logging.debug('Downloaded %s' % url)
    html.make_links_absolute(url)
    return html

def get_title(html):
    page_title = html.xpath("//title")[0].text.encode('utf-8')
    logging.debug('Title: %s' % page_title)
    return page_title

def get_json(url):
    return json.loads(url_fetch(url))

def get_hn_post(post_id):
    url = 'https://hacker-news.firebaseio.com/v0/item/%s.json' % post_id
    return get_json(url)

def main(from_url, xpath, to_prefix, replace_with, attach_url_prefix, from_email, to_email, subject_prefix):
    logging.getLogger().setLevel(logging.DEBUG)
    urls = get_urls(get_html(from_url), to_prefix, xpath)
    for url in urls:
        try:
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
                    if replace_with == '__PIRATEBAY__':
                        body = url.replace(to_prefix, pirate_bay_proxies[pi] + '/torrent')
                    else:
                        body = url.replace(to_prefix, replace_with)
                else:
                    body = url
                if attach_url is not None:
                    body += "\n\n%s" % attach_url
                mail.send_mail(from_email, to_email, subject, body)
                Link(url=url).put()
        except Exception, err:
            logging.debug('Exception while fetching %s' % url)
            logging.debug(traceback.format_exc())

class Backreaction(webapp2.RequestHandler):
    def get(self):
        main(from_url='https://backreaction.blogspot.com',
             xpath='//h3/a/@href',
             to_prefix='https://backreaction.blogspot.com/',
             replace_with=None,
             attach_url_prefix=None,
             from_email='Webfeed <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='backreaction')

class Simplystatistics(webapp2.RequestHandler):
    def get(self):
        main(from_url='http://simplystatistics.org/',
             xpath='//h1/a/@href',
             to_prefix='http://simplystatistics.org/',
             replace_with=None,
             attach_url_prefix=None,
             from_email='Webfeed <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='simplystatistics')

class Evanmiller(webapp2.RequestHandler):
    def get(self):
        main(from_url='http://www.evanmiller.org/',
             xpath='//a/@href',
             to_prefix='http://www.evanmiller.org/',
             replace_with=None,
             attach_url_prefix=None,
             from_email='Webfeed <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='evanmiller')

class Bluesnews(webapp2.RequestHandler):
    def get(self):
        main(from_url='http://bluesnews.com',
             xpath='//a/@href',
             to_prefix='https://www.youtube.com',
             replace_with=None,
             attach_url_prefix=None,
             from_email='Webfeed <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='bluesnews')

class PiratebayMovies(webapp2.RequestHandler):
    def get(self):
        main(from_url='https://thepiratebay.se/top/207',
             xpath='//a/@href',
             to_prefix='https://thepiratebay.se/torrent',
             replace_with='__PIRATEBAY__',
             attach_url_prefix='http://www.imdb.com',
             from_email='Webfeed <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='piratebay movies')

class PiratebayGames(webapp2.RequestHandler):
    def get(self):
        main(from_url='https://thepiratebay.se/top/401',
             xpath='//a/@href',
             to_prefix='https://thepiratebay.se/torrent',
             replace_with='__PIRATEBAY__',
             attach_url_prefix=None,
             from_email='Webfeed <mtrencseni@gmail.com>',
             to_email='Marton Trencseni <mtrencseni@gmail.com>',
             subject_prefix='piratebay games')

class Redlettermedia(webapp2.RequestHandler):
    def get(self):
        main(from_url='http://redlettermedia.com',
             xpath='//iframe/@src',
             to_prefix='https://www.youtube.com/embed/',
             replace_with='https://www.youtube.com/watch?v=',
             attach_url_prefix=None,
             from_email='Webfeed <mtrencseni@gmail.com>',
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
                    from_email='Webfeed <mtrencseni@gmail.com>',
                    to_email = 'Marton Trencseni <mtrencseni@gmail.com>'
                    mail.send_mail(from_email, to_email, subject, body)
                    Link(url=post['url']).put()
                    self.response.write('+ saved\n')
                else:
                    self.response.write('- already seen\n')
            else:
                self.response.write('- does not qualify\n')

app = webapp2.WSGIApplication([
    ('/backreaction', Backreaction),
    ('/simplystatistics', Simplystatistics),
    ('/evanmiller', Evanmiller),
    ('/bluesnews', Bluesnews),
    ('/piratebay_movies', PiratebayMovies),
    ('/piratebay_games', PiratebayGames),
    ('/redlettermedia', Redlettermedia),
    ('/hackernews', Hackernews),
], debug=True)
