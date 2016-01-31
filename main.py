import webapp2
#import httplib2
from google.appengine.api import urlfetch
from BeautifulSoup import BeautifulSoup, SoupStrainer
import lxml
from lxml import etree
from google.appengine.ext import ndb
from google.appengine.api import mail

class Link(ndb.Model):
    url = ndb.StringProperty(indexed=True)

def get_urls(from_url='http://bluesnews.com', to_domain='https://www.youtube.com'):
    result = urlfetch.fetch(from_url)
    urls = []
    for link in BeautifulSoup(result.content, parseOnlyThese=SoupStrainer('a')):
        if link.has_key('href'):
            if link['href'].startswith(to_domain):
                urls.append(link['href'])
    return urls

def get_youtube_title(url):
    youtube = etree.HTML(urlfetch.fetch(url).content)
    video_title = youtube.xpath("//span[@id='eow-title']/@title")
    return ''.join(video_title)

def main():
    urls = get_urls()
    for url in urls:
        if len(Link.query(Link.url == url).fetch(1)) == 0:
            title = get_youtube_title(url)
            mail.send_mail("Bluesnews Youtube Watcher <mtrencseni@gmail.com>",
                           "Marton Trencseni <mtrencseni@gmail.com>",
                           "[bluesnews] %s" % title, url)
            Link(url=url).put()

class MainPage(webapp2.RequestHandler):
    def get(self):
        main()

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
