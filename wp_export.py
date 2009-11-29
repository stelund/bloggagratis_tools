
import time
import pytz
import datetime

UTC_TIMEZONE = pytz.timezone('UTC')

def format_pubdate(date):
    # Mon, 02 Nov 2009 08:39:06 +0000
    return date.astimezone(UTC_TIMEZONE).strftime(u'%a, %d %b %Y %H:%M:%S %z')

def format_isodate(date):
    # 2009-11-02 09:39:06
    return date.strftime(u'%Y-%m-%d %H:%M:%S')

def format_gmtdate(date):
    # 2009-11-02 09:39:06
    return date.astimezone(UTC_TIMEZONE).strftime(u'%Y-%m-%d %H:%M:%S')

def format_comments(comments):
    format = u"""      <wp:comment>
        <wp:comment_id>%(comment_id)s</wp:comment_id>
        <wp:comment_author><![CDATA[%(author)s]]></wp:comment_author>
        <wp:comment_author_email>%(author_email)s</wp:comment_author_email>
        <wp:comment_author_url>%(url)s</wp:comment_author_url>
        <wp:comment_author_IP></wp:comment_author_IP>
        <wp:comment_date>%(date)s</wp:comment_date>
        <wp:comment_date_gmt>%(gmt_date)s</wp:comment_date_gmt>
        <wp:comment_content><![CDATA[%(text)s]]></wp:comment_content>
        <wp:comment_approved>1</wp:comment_approved>
        <wp:comment_type></wp:comment_type>
        <wp:comment_parent>0</wp:comment_parent>
        <wp:comment_user_id>%(user_id)d</wp:comment_user_id>
      </wp:comment>
"""
    
    for c in comments:
        c['gmt_date'] = format_gmtdate(c['date'])
        c['date'] = format_isodate(c['date'])
        c['user_id'] = 0
        c['author_email'] = ''
        c['comment_id'] = ''
    return u'\n'.join([format % comment for comment in comments])

def format_item_categories(categories):
    # <category><![CDATA[Bilder]]></category>
    # <category domain="category" nicename="bilder"><![CDATA[Bilder]]></category>
    return ''

def format_images(images, static_url):
    format = u"""    <item>
      <title>%(name)s</title>
      <link>%(static_url)s%(filename)s</link>
      <pubDate>%(pubdate)s</pubDate>
      <dc:creator><![CDATA[admin]]></dc:creator>
%(categories)s
      <guid isPermaLink="false">%(static_url)s%(filename)s</guid>
      <description>%(description)s</description>
      <content:encoded><![CDATA[]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>%(post_id)d</wp:post_id>
      <wp:post_date>%(post_date)s</wp:post_date>
      <wp:post_date_gmt>%(post_gmt_date)s</wp:post_date_gmt>
      <wp:comment_status>open</wp:comment_status>
      <wp:ping_status>open</wp:ping_status>
      <wp:post_name>%(name)s</wp:post_name>
      <wp:status>inherit</wp:status>
      <wp:post_parent>%(post_parent)d</wp:post_parent>
      <wp:menu_order>0</wp:menu_order>
      <wp:post_type>attachment</wp:post_type>
      <wp:post_password></wp:post_password>
      <wp:attachment_url>%(static_url)s%(filename)s</wp:attachment_url>
      <wp:postmeta>
        <wp:meta_key>_wp_attached_file</wp:meta_key>
        <wp:meta_value>%(filename)s</wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
      <wp:meta_key>_wp_attachment_metadata</wp:meta_key>
      <wp:meta_value>a:6:{s:5:"width";s:3:"%(width)d";s:6:"height";s:3:"%(height)d";s:14:"hwstring_small";s:22:"height='96' width='76'";s:4:"file";s:7:"6jg.jpg";s:5:"sizes";a:2:{s:9:"thumbnail";a:3:{s:4:"file";s:15:"6jg-150x150.jpg";s:5:"width";s:3:"150";s:6:"height";s:3:"150";}s:6:"medium";a:3:{s:4:"file";s:15:"6jg-240x300.jpg";s:5:"width";s:3:"240";s:6:"height";s:3:"300";}}s:10:"image_meta";a:10:{s:8:"aperture";s:1:"0";s:6:"credit";s:0:"";s:6:"camera";s:0:"";s:7:"caption";s:0:"";s:17:"created_timestamp";s:1:"0";s:9:"copyright";s:0:"";s:12:"focal_length";s:1:"0";s:3:"iso";s:1:"0";s:13:"shutter_speed";s:1:"0";s:5:"title";s:0:"";}}</wp:meta_value>
      </wp:postmeta>
    </item>"""
    
    for img in images:
        img['pubdate'] = format_pubdate(img['date'])
        img['post_date'] = format_isodate(img['date'])
        img['post_gmt_date'] = format_gmtdate(img['date'])
        img['categories'] = format_categories(img['categories'])
        img['static_url'] = static_url
        img['description'] = ''
    
    return u'\n'.join([format % img for img in images])


def format_items(items, site_url):
    format = u"""    <item>
      <title>%(title)s</title>
      <link>%(site_url)s/%(year)d/%(month)d/%(day)d/%(post_name)s/</link>
      <pubDate>%(pubdate)s</pubDate>
      <dc:creator><![CDATA[%(author)s]]></dc:creator>
%(categories)s
      <guid isPermaLink="false">%(site_url)s/?p=%(post_id)d</guid>
      <description>%(description)s</description>
      <content:encoded><![CDATA[%(text)s]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>%(post_id)d</wp:post_id>
      <wp:post_date>%(post_date)s</wp:post_date>
      <wp:post_date_gmt>%(post_gmt_date)s</wp:post_date_gmt>
      <wp:comment_status>open</wp:comment_status>
      <wp:ping_status>open</wp:ping_status>
      <wp:post_name>%(post_name)s</wp:post_name>
      <wp:status>publish</wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>0</wp:menu_order>
      <wp:post_type>post</wp:post_type>
      <wp:post_password></wp:post_password>
      <wp:postmeta>
        <wp:meta_key>_edit_lock</wp:meta_key>
        <wp:meta_value>1257151148</wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key>_edit_last</wp:meta_key>
        <wp:meta_value>1</wp:meta_value>
      </wp:postmeta>
%(comments)s
    </item>
"""
    for item in items:
        item['pubdate'] = format_pubdate(item['date'])
        item['post_date'] = format_isodate(item['date'])
        item['post_gmt_date'] = format_gmtdate(item['date'])
        item['post_name'] = item['title'].lower().replace(' ', '_')
        item['comments'] = format_comments(item['comments'])
        item['categories'] = format_categories(item['categories'])
        item['site_url'] = site_url
        item['year'] = item['date'].year
        item['month'] = item['date'].month
        item['day'] = item['date'].day
        item['description'] = ''

    return u'\n'.join([format % item for item in items])

def format_categories(categories):
    format = u'    <wp:category><wp:category_nicename>%(nicename)s</wp:category_nicename><wp:category_parent>%(parent)s</wp:category_parent><wp:cat_name><![CDATA[%(fullname)s]]></wp:cat_name></wp:category>'
    return u'\n'.join([format % cat for cat in categories])
        

def export(articles, images, categories, bloginfo, outfile):
   fp = file(u'wp_template.xml', 'r')
   template = unicode(fp.read())
   fp.close()

   bloginfo['pubdate'] = format_pubdate(UTC_TIMEZONE.localize(datetime.datetime.utcnow()))
   bloginfo['creation_date'] = time.strftime('%Y-%m-%d %H:%M')
   bloginfo['categories'] = format_categories(categories)
   bloginfo['items'] = format_items(articles, bloginfo['site_url'])
   bloginfo['images'] = format_images(images, bloginfo['static_url'])
   out = template % bloginfo

   if outfile:
       fp = file(outfile, 'w')
       fp.write(out.encode('ISO-8859-1'))
       fp.close()
