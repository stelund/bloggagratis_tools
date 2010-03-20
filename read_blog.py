#!/usr/bin/env python
"""
The script to read a site
"""
import urllib2
import sys
import os
import re
import datetime
import wp_export
import pytz
import optparse
from htmlentitydefs import name2codepoint

SWEDEN_TIMEZONE = pytz.timezone('Europe/Stockholm')
TEMPDIR = None
BLOG = None
MONTHS = {u'jan':1,
          u'januari':1,
          u'feb':2,
          u'februari':2,
          u'mar':3,
          u'mars':3,
          u'apr':4,
          u'april':4,
          u'maj':5,
          u'jun':6,
          u'juni':6,
          u'juli':7,
          u'jul':7,
          u'aug':8,
          u'augusti':8,
          u'sept':9,
          u'september':9,
          u'okt':10,
          u'oktober':10,
          u'nov':11,
          u'november':11,
          u'dec':12,
          u'december':12 }

def read_date(datestr):
    # new format
    if 'kl' not in datestr:
        # Torsdag 18 mars 18:37
        match = re.compile(u'.* (?P<day>\\d+) (?P<month>.+?) (?P<year>\\d\\d\\d\\d) (?P<hour>\\d\\d):(?P<minute>\\d\\d)').search(datestr)
        if match:
            year = int(match.group('year'))
        else:
            match = re.compile(u'.* (?P<day>\\d+) (?P<month>.+?) (?P<hour>\\d\\d):(?P<minute>\\d\\d)').search(datestr)
            year = datetime.datetime.now().year
            if not match:
                print 'Failed to match date str "%s"' % datestr
                return None
        minute = int(match.group('minute'))
        hour = int(match.group('hour'))
        day = int(match.group('day'))
        month = MONTHS[match.group('month').lower()]
        return SWEDEN_TIMEZONE.localize(datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute))

    # old format
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
    filename = TEMPDIR + u'/' + path.strip(u'/').replace(u'/', u'_') + u'.html'
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
    u'author,date': (False, re.compile(r'[Aa]v <a href="http://.+bloggagratis\.se/presentation/">(?P<author>.+?)</a> (?P<date>.+?)\n')),
    u'comments': (True, re.compile(r'<div class="kommentarer"><div style="margin:0;padding:0px 5px 0px 5px">\n<p>(?P<comments>.+?)</p></div>\n<div style="text-align: right; margin: 0; padding: 0px 0px 0px 0px">av (?P<commentor_date>.+?)</div>'))
}

def parse_page(pagename, rules):
    page = get_page(pagename).replace(u'</p>\n', u'</p>')

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
            print u'Matching %s failed in page from page %s' % (part, pagename)
            print repr(page)
            sys.exit(1)
    return info

def parse_blog_page(page):
    info = parse_page(page, BLOG_RULES)
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
                    print u'Bad commentor %s in page %s' % (commentor, page)
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

    info[u'date'] = read_date(info[u'author,date'][1])
    info[u'author'] = unescape_html(info[u'author,date'][0])
    del info[u'author,date']

    info[u'page'] = page
    info[u'text'] = unescape_html(info[u'text'])

    info[u'links'] = []
    for page in re.compile(u'href="http://%s.bloggagratis.se/(?P<page>20.+?)"' % BLOG).findall(info[u'text']):
        info[u'links'].append({ u'url' : u'http://%s.bloggagratis.se/%s' % (BLOG, page),
                                u'page' : page })
        
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
              

    match = re.compile(u'<title>(?P<name>.+?)</title>').search(page)
    name = match.group('name')
    return indexes, name

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
    for (cat_view, cat_html) in re.compile(u'bloggagratis.se/(?P<url>.+?)">(?P<category>.+?) \\(\\d+\\)</a>').findall(categories_section):
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

def read_images(article):
    images = []
    for filename in re.compile(u'http://data.bloggplatsen.se/bild/(?P<filename>.+?)"').findall(article['text']):
        nicename = u'%s_%d.jpg' % (wp_export.nicename(article[u'title']), len(images)+1)
        images.append( {
                u'filename' : filename,
                u'nicename' : nicename,
                u'url' :  u'http://data.bloggplatsen.se/bild/%s?%s' % (filename, nicename), 
                u'date' : article[u'date'],
                u'categories' : [],
                u'name' : '%s - bild %d' % (article[u'title'], len(images) + 1),
                } )


    for image in images:
        article['text'] = article['text'].replace('http://data.bloggplatsen.se/bild/%s' % image[u'filename'], 
                                                  image[u'url'])

    return images

def minimize(article):
    article['text'] = article['text'].replace(' class="space"', '').replace('<!-- -->', '').replace(' class="editor_p"', '').replace('<p></p>', '')

def fix_links(articles, site_url):

    for article in articles:
        article['new_permalink'] = '%s/?p=%d' % (site_url, article['post_id'])

    for article in articles:
        for link in article[u'links']:
            for linkto in articles:
                if linkto['page'] == link['page']:
                    article[u'text'] = article[u'text'].replace(link['url'], linkto['new_permalink'])
                    print u'Fixing link %s to %s' % (link[u'page'], linkto['new_permalink'])
                    break
            else:
                print u'Missing link for %s to %s' % (article['page'], link['page'])


def main():
    global BLOG
    global TEMPDIR
    usage = 'usage: read_blog.py <blog> <new-url>\n\n<blog>Where blog is http://<blog>.bloggagratis.se \n and new-url is the full new url to where the site should be importet to.\n\nFor more help use --help.'
    parser = optparse.OptionParser(usage='read_blog.py <blog> <new-url>')
    parser.add_option('-c', '--no-comments', help='Dont include comments', default=False, action='store_true', dest='nocomments')
    parser.add_option('-t', '--temporary-directory', help='Default is <blog>', default=None, dest='tempdir')
    parser.add_option('-s', '--scratch', help='Wipe temporary directory and download everything from blog', default=False, action='store_true', dest='scratch')
    parser.add_option('-o', '--output', help='Export blog to wordprocess file', default='wordpress.xml', dest='output')
    parser.add_option('-n', '--limit', help='Split output into n articles per exported file', default=0, dest='limit')

    (options, args) = parser.parse_args()

    if len(args) != 2:
        print usage
        sys.exit(1)

    BLOG = args[0]
    site_url = args[1]
    if options.tempdir:
        TEMPDIR = options.tempdir
    else:
        TEMPDIR = BLOG

    print 'Imorting from http://%s.bloggagratis.se/' % BLOG
    print 'Temporary directory in %s' % TEMPDIR

    if not os.path.exists(TEMPDIR):
        os.mkdir(TEMPDIR)

    if options.scratch:
        print 'Reading site from scratch'
        for page in os.listdir(TEMPDIR):
            os.remove(os.path.join(TEMPDIR, page))
    else:
        pages = len([x for x in os.listdir(TEMPDIR)])
        if pages:
            print 'Using %d pages from cache' % pages

    post_id = 0
    categories, category_lookup = read_categories()
    
    indexes, name = read_index()
    articles = []
    for permalink in indexes:
        info = parse_blog_page(permalink)
        info[u'categories'] = category_lookup.get(permalink, [])
        print u'- Reading %s' % permalink
        info['post_id'] = post_id
        post_id = post_id + 1
        minimize(info)
        post_images = read_images(info)
        for img in post_images:
            img['post_parent'] = info['post_id']
            img['post_id'] = post_id
            post_id = post_id + 1
        info['images'] = post_images
        articles.append(info)
        
    fix_links(articles, unicode(site_url))

    bloginfo = {u'site_url':unicode(site_url), 
                u'static_url' : u'http://data.bloggplatsen.se/bild/',
                u'name' : name}

    if options.limit:
        for index, start in enumerate(range(0, len(articles), int(options.limit))):
            if u'.' in unicode(options.output):
                basename, ext = unicode(options.output).rsplit(u'.', 1)
                filename = u'%s_%d.%s' % (basename, index, ext)
            else:
                filename = u'%s_%d' % (unicode(options.output), index)
            print u'Exporting %d-%d to %s' % (start, start+int(options.limit), filename)
            wp_export.export(articles[start:start+int(options.limit)], categories, bloginfo, filename)
    else:
        wp_export.export(articles, categories, bloginfo, unicode(options.output))

if __name__ == '__main__':
    main()                 



