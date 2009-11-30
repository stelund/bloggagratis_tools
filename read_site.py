#!/usr/bin/env python
"""
The script to read a site
"""
import urllib2
import sys
import os
import re
import pprint
import datetime
import wp_export
import pytz
from htmlentitydefs import name2codepoint

SWEDEN_TIMEZONE = pytz.timezone('Europe/Stockholm')
BLOG = u'tantalexandra'
IMAGES_URL = 'http://stefanlundstrom.se/static/' + BLOG + '_images/'
MONTHS = {u'jan':1,
          u'feb':2,
          u'mars':3,
          u'april':4,
          u'maj':5,
          u'juni':6,
          u'juli':7,
          u'aug':8,
          u'sept':9,
          u'okt':10,
          u'nov':11,
          u'november':11,
          u'december':12,
          u'dec':12 }

def read_date(datestr):
    day_str, time_str = datestr.replace(u'&nbsp;',u' ').lower().split(u' kl ') 

    if u'idag' in day_str:
        day  = datetime.datetime.now()
    elif u'ig&aring;r' in day_str:
        day  = datetime.datetime.now() - datetime.timedelta(days=1)
    elif u'f&ouml;rrg&aring;r' in day_str:
        day = datetime.datetime.now() - datetime.timedelta(days=1)
    else:
        d, m, y = day_str.split()
        day = datetime.datetime(day=int(d), month=MONTHS[m], year=int(y))

    hour, minute = time_str.split(u':')
    return SWEDEN_TIMEZONE.localize(datetime.datetime(year=day.year, month=day.month, day=day.day, hour=int(hour), minute=int(minute)))

def get_page(path):
    filename = BLOG + u'/' + path.strip(u'/').replace(u'/', u'_') + u'.html'
    if os.path.exists(filename):
        fp = file(filename, 'rb')
        data = fp.read()
        fp.close()
        return data.decode('ISO-8859-1')
    try:
        url = urllib2.urlopen(u'http://%s.bloggagratis.se/%s' % (BLOG, path))
        data = url.read()
        url.close()
    except urllib2.URLError:
        print 'Failed to get page %s' % path
        return None
    fp = file(filename, 'wb')
    fp.write(data)
    fp.close()
    return data.decode('ISO-8859-1')

BLOG_RULES = {
    u'text': (False, re.compile(r'<div class="inlagg_text">(?P<text>.*?)<a id="kommentarer"')),
    u'title': (False, re.compile(r'<h1><a href="http://.+bloggagratis\.se/.+?" title="(?P<title>.+?)"')),
    u'author,date': (False, re.compile(r'av <a href="http://.+bloggagratis\.se/presentation/">(?P<author>.+?)</a> (?P<date>.+?)\n')),
    u'comments': (True, re.compile(r'<div class="kommentarer"><div style="margin:0;padding:0px 5px 0px 5px">\n<p>(?P<comments>.+?)</p>\n</div>\n<div style="text-align: right; margin: 0; padding: 0px 0px 0px 0px">av (?P<commentor_date>.+?)</div>'))
}

def parse_page(url, rules):
    page = get_page(url)

    info = {}
    for part, regex in rules.iteritems():
        matchs = regex[1].findall(page)
        if matchs:
            for match in matchs:
                if regex[0]:
                    if part not in info:
                        info[part] = []
                    info[part].append(match)
                else:
                    info[part] = match
        elif not regex[0]:
            print 'Matching %s failed in page %s' % (part, url)
            print page
            sys.exit(1)
    return info

def parse_blog_page(url):
    info = parse_page(url, BLOG_RULES)
    if u'comments' in info:
        new_comments = []
        for comment_text, commentor in info['comments']:
            if u'<a' in commentor:
                match = re.compile(u'<a href="(?P<url>.+?)" title=".*?" target="_blank">(?P<author>.+?)</a> (?P<date>.+)').search(commentor)
                if match:
                    comment = {
                        u'text' : unicode(unescape_html(comment_text)),
                        u'url' : match.group('url'),
                        u'author' : match.group('author'),
                        u'date' : read_date(match.group('date')),
                        }
                else:
                    print 'Bad commentor %s in page %s' % (commentor, url)
                    comment = { 'text' : commentor }
            else:
                if 'idag' in commentor or 'ig&aring;r' in commentor or 'f&ouml;rrg&aring;r' in commentor:
                    author, d1, d2, d3 = commentor.rsplit(' ',3)
                    date = '%s %s %s' % (d1, d2, d3)
                else:
                    author, d1, d2, d3, d4, d5 = commentor.rsplit(' ',5)
                    date = '%s %s %s %s %s' % (d1, d2, d3, d4, d5)
                comment = {
                    u'text' : comment_text,
                    u'author' : author,
                    u'date' : read_date(date),
                    u'url' : '',
                    }
            new_comments.append(comment)
        info[u'comments'] = new_comments
    else:
        info[u'comments'] = []

    if u'author,date' in info:
        info[u'date'] = read_date(info[u'author,date'][1])
        info[u'author'] = unescape_html(info[u'author,date'][0])
        del info[u'author,date']

    if u'text' in info:
        info[u'text'] = unescape_html(info[u'text'])
    if u'title' in info:
        info[u'title'] = unescape_html(info[u'title'])

    return info

def read_index():
    page = get_page(u'')

    archive_section = page.split(u'<h2>Arkiv</h2>',1)[1].split(u'<div class="menyrubrik">',1)[0]
    
    permalinks = re.compile(u'<h1><a href="http://.+?bloggagratis.se/(?P<url>.+?)" title="')
    
    indexes = []
    monthly_views = re.compile(u'http://.+?.bloggagratis.se/(?P<date>.+?)"').findall(archive_section)
    for m in monthly_views:
        for index in range(20):
            m_page = get_page(m + u'sida-%d/' % (index+1))
            if not permalinks.search(m_page):
                break
            for permalink in permalinks.findall(m_page):
                indexes.append(permalink)
                
    return indexes

def unescape_html(html):
    "unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
    return re.sub(u'&(%s);' % u'|'.join(name2codepoint),
                  lambda m: unichr(name2codepoint[m.group(1)]), html)

def read_categories():
    page = get_page(u'')

    categories_section = page.split(u'<h2>Kategorier</h2>',1)[1].split(u'<div class="menyrubrik">',1)[0]
    
    permalinks = re.compile(u'<h1><a href="http://.+?bloggagratis.se/(?P<url>.+?)" title="')

    pages = {}
    categories = []
    for (cat_view, cat_html) in re.compile(u'bloggagratis.se/(?P<url>.+?)">(?P<category>.+?)</a>').findall(categories_section):
        cat = unescape_html(cat_html)
        for index in range(200):
            c_page = get_page(cat_view + u'sida-%d/' % (index+1))
            if not permalinks.search(c_page):
                break
            for permalink in permalinks.findall(c_page):
                if permalink in pages:
                    pages[permalink].append(cat)
                else:
                    pages[permalink] = [cat]
                
        categories.append(cat)
   
    return categories, pages

def download_image(filename):
                   
    safe_filename = filename.replace(u'/', u'_')
    if safe_filename.endswith('_'):
        safe_filename = safe_filename[:-1]
        if '.' not in safe_filename[-5:]:
            safe_filename = safe_filename + '.' + re.compile(r'\.(?P<extension>.+)_').search(safe_filename).group('extension')
    if not os.path.exists(os.path.join(BLOG + u'_images', safe_filename)):
        try:
            url = urllib2.urlopen(u'http://data.bloggplatsen.se/bild/%s' % filename)
            data = url.read()
            url.close()
            print 'Downloaded %s' % filename
        except urllib2.URLError:
            print 'Failed read read %s' % filename
            return None
        fp = file(os.path.join(BLOG + u'_images', safe_filename), u'wb')
        fp.write(data)
        fp.close()
        
    return safe_filename

def read_images(article):
    images = []
    for filename in re.compile(u'http://data.bloggplatsen.se/bild/(?P<filnamn>.+?)"').findall(article['text']):
        path = 'missing' #download_image(filename)

        images.append( {
                u'filename' : filename,
                u'url' : u'http://data.bloggplatsen.se/bild/%s?%s-bild_%d.jpg' % (filename, wp_export.nicename(article[u'title']), len(images)+1),
                #IMAGES_URL + path,
                u'path' : path,
                u'date' : article[u'date'],
                u'categories' : [],
                u'height' : 0,
                u'width' : 0,
                u'name' : '%s - bild %d' % (article[u'title'], len(images) + 1),
                } )

    for image in images:
        article['text'] = article['text'].replace('http://data.bloggplatsen.se/bild/%s' % image[u'filename'], 
                                                  image[u'url'])

    return images

def main():
    if not os.path.exists(BLOG):
        os.mkdir(BLOG)

    if not os.path.exists(BLOG + u'_images'):
        os.mkdir(BLOG + u'_images')
     
    indexes = read_index()
    articles = []
    images = []
    post_id = 0
    categories, category_lookup = read_categories()
    for permalink in indexes:
        info = parse_blog_page(permalink)
        info[u'categories'] = category_lookup.get(permalink, [])
        print u'Processing %s' % permalink
        info['post_id'] = post_id
        post_id = post_id + 1
        articles.append(info)
        post_images = read_images(info)
        for img in post_images:
            img['post_parent'] = info['post_id']
            img['post_id'] = post_id
            post_id = post_id + 1
        images.extend(post_images)

    bloginfo = {u'site_url':u'http://stefanlundstrom.se:5122', 'static_url' : 'http://data.bloggplatsen.se/bild/'}
    wp_export.export(articles, images, categories, bloginfo, u'out.xml')


if __name__ == '__main__':
    main()                 



