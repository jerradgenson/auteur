"""
Tools for parsing and generating blog article HTML.

Author: Jerrad Michael Genson
Email: auteur@jerradgenson.33mail.com
License: BSD 3-Clause
Copyright 2016 Jerrad Michael Genson

"""

# Python built-in modules
import datetime
import re
from collections import namedtuple
from pathlib import Path

# First-party modules
from file_tools import read_listing_file, read_complete_file, get_configuration
from data import LISTING_PATH, TEMPLATE_PATH, HOME_PAGE_LINK


# String index that article title starts on (excluding HTML tags).
_ARTICLE_TITLE_START = 7

# String index that article title ends on (excluding HTML tags).
_ARTICLE_TITLE_END = -8

# HTML template for the article title.
_ARTICLE_TITLE_TEMPLATE = '<h2 class="article_title"><a href="{article_path}">{article_title}</a><p class="article_subtitle">{article_subtitle}</p></h2>'

# HTML template for "Continue reading..." hyperlink.
_CONTINUE_READING_TEMPLATE = '<a href="{article_path}">Continue reading...</a>'

# HTML template for article preview.
_ARTICLE_PREVIEW_TEMPLATE = '<section class="article_preview">\n{article_title}\n{article_photo}\n{article_content}\n</section>\n'

# HTML template for article content.
_ARTICLE_CONTENT_TEMPLATE = '<section class="article_content">\n{article_content}\n</section>'

# HTML template for nav bar content.
_NAV_BAR_TEMPLATE = '<a href="{previous_article}">Previous</a> <a href="../">Home</a>'


ArticlePreview = namedtuple('ArticlePreview', ['title', 'publication_date', 'path', 'text', 'first_photo'])
ArticlePreview.__doc__ = \
"""
Represents an article preview for use on blog landing page.

Args
  title: The title of the blog article.
  publication_date: Date of article publication.
  path: Path object for the article file.
  text: Some introductory text from the article.
  first_photo: HTML for the article's first photograph, if any. If photo doesn't exist, this will be `None`.

"""


def extract_pub_date(html):
    """
    Extract publication date from HTML tag.

    Args
      html: HTML string to extract publication date from.

    Returns,
      A tuple of (publication date w/ tags, publication date w/o tags)

    """

    # Extract publication date.
    pub_date_match = re.search('<Published\s*=\s*.+?>', html)
    if pub_date_match:
        # Extract actual date from pub date tag.
        pub_date = re.sub('<Published\s*=\s*', '', pub_date_match.group(0))
        pub_date = pub_date[:-1]
        return pub_date_match.group(0), pub_date

     # Extract date from HTML subtitle tag.
    pub_date_match = re.search('<p class="article_subtitle">.+?</p>', html)
    if pub_date_match:
       pub_date = pub_date_match.group(0).replace('<p class="article_subtitle">', '').replace('</p>', '')
       return pub_date_match.group(0), pub_date

    else:
        # No pub date tag found.
        return None, ''


def extract_article_preview(article_path):
    """
    Extract title, first photograph, and first paragraph from the target article.

    Args
      article_path: Path object for the article file.

    Return
      An instance of `Article`.

      """

    article_text = read_complete_file(article_path)

    # Extract article title.
    match = re.search('<title>.+</title>', article_text)
    article_title = match.group(0)[_ARTICLE_TITLE_START:_ARTICLE_TITLE_END]

    # Extract publication date.
    pub_date = extract_pub_date(article_text)[1]

    # Extract introductory text..
    paragraphs = article_text.split('<p>')
    intro_text_list = ['']
    for paragraph in paragraphs:
        if len(intro_text_list) > 2:
            break

        if paragraph.strip()[0] != '<':
            intro_text_list.append(paragraph)

    intro_text = '<p>'.join(intro_text_list)

    # Remove HTML tags from intro text..
    reverse_text = intro_text[::-1]
    # Add 4 here to account for the length of the string '</p>' in reverse.
    tag_index = reverse_text.index('>p/<') + 4
    intro_text = intro_text[:-tag_index]

    # Extract first photograph.
    match = re.search('<figure>.+?</figure>', article_text, re.DOTALL)
    if match:
        first_photo = match.group(0)

    else:
        first_photo = None

    article_preview = ArticlePreview(article_title, pub_date, article_path, intro_text, first_photo)

    return article_preview


def generate_preview_html(article_preview):
    """
    Generate HTML for an `ArticlePreview` object.

    Args
      article_preview: An instance of `ArticlePreview`.

    Returns
      String containing HTML form of `article_preview`.

    """

    article_title_html = _ARTICLE_TITLE_TEMPLATE.format(article_title=article_preview.title,
                                                        article_subtitle=article_preview.publication_date,
                                                        article_path=article_preview.path.parent)

    if article_preview.first_photo:
        article_photo_html = article_preview.first_photo

    else:
        article_photo_html = ''

    continue_reading_link = _CONTINUE_READING_TEMPLATE.format(article_path=article_preview.path.parent)
    article_content = article_preview.text + ' ' + continue_reading_link + '</p>'
    preview_html = _ARTICLE_PREVIEW_TEMPLATE.format(article_title=article_title_html,
                                                    article_photo=article_photo_html,
                                                    article_content=article_content)

    return preview_html


def generate_landing_page(template_path=TEMPLATE_PATH):
    """
    Create new landing page — the "home page" for Recursive Descent.


    Args
      template_path: Path to the article template file.

    Return
      An HTML string for the blog site landing page.

    """

    articles = create_article_previews()

    # Load blog article template from file.
    article_template = read_complete_file(template_path)

    # Combine article previews into one long aggregate post.
    preview_htmls = (generate_preview_html(article) for article in articles)
    aggregate_html = ''
    for preview_html in preview_htmls:
        aggregate_html += preview_html + '\n\n'

    last_updated = 'Last updated: ' + datetime.date.today().strftime('%B %d, %Y')
    current_year = datetime.date.today().strftime('%Y')
    configuration = get_configuration()

    # Apply blog article template to aggregate content.
    landing_page_html = article_template.format(article_title=configuration.blog_title,
                                                nav_bar='',
                                                article_content=aggregate_html,
                                                last_updated=last_updated,
                                                current_year=current_year,
                                                blog_title=configuration.blog_title,
                                                blog_subtitle=configuration.blog_subtitle,
                                                owner=configuration.owner,
                                                email_address=configuration.email_address,
                                                rss_feed_path=configuration.rss_feed_path,
                                                style_sheet=configuration.style_sheet,
                                                root_url=configuration.root_url,
                                                home_page_link='')

    return landing_page_html


def generate_post(html, output_path, template_path=TEMPLATE_PATH, listing_path=LISTING_PATH):
    """
    Apply blog post template to Markdown-to-HTML translation.

    Args
      html: HTML content to turn into blog post.
      output_path: Output path for final HTML blog post file.
      template_path: Path to blog post template file. (Optional)
      listing_path: Path to blog post listing file. (Optional)

    Return
      Final blog post HTML string.

    """

    # Find top-level heading tag in HTML and turn it into article title.
    article_title_match = re.search('<h1>.+?</h1>', html)
    if not article_title_match:
        article_title_match = re.search('<h2 class="article_title">.+?</a>', html)

    if not article_title_match:
        raise ValueError('Argument `html` must have an `h1` or `h2` tag.')

    # Extract article title from heading.
    article_title = article_title_match.group(0).replace('<h1>', '').replace('</h1>', '')
    article_title = article_title.replace('<h2 class="article_title">', '')
    article_title = re.sub('<a href=".+?">', '', article_title)
    article_title = article_title.replace('</a>', '')

    # Extract publication date if it exists.
    pub_date_full, pub_date = extract_pub_date(html)

    # Apply HTML template to article title.
    article_title_html = _ARTICLE_TITLE_TEMPLATE.format(article_title=article_title,
                                                        article_subtitle=pub_date,
                                                        article_path='')

    # Remove heading from article content, then reinsert it as the article's title.
    html = re.sub('<h2.+?</h2>', '', html)
    html = html.replace(article_title_match.group(0), '')
    html = html.strip()

    # Remove publication date tags from article content.
    if pub_date_full:
        html = html.replace(pub_date_full, '')

    article_content = article_title_html + '\n' + html

    # If line formerly containing heading is empty, we need to remove it from the article content.
    lines = article_content.split('\n')
    chars_on_line = re.match('\S', lines[0])
    if not chars_on_line:
        lines = lines[1:]
        article_content = '\n'.join(lines)

    # Apply HTML template to article content.
    article_content_html = _ARTICLE_CONTENT_TEMPLATE.format(article_content=article_content)

    # Create link to previous blog entry.
    listing = read_listing_file(listing_path)
    if output_path not in listing:
        # If the output path for the current article isn't in the blog post listing then we know this is the most
        # recent post, and the last post in the listing is what we should link to.
        previous_article = listing[-1]

    else:
        # This isn't the most recent post, so we need to figure out which post it is so we can link it to the previous
        # article.
        previous_article_index = listing.index(output_path) - 1
        if previous_article_index >= 0:
            previous_article = Path('../') / listing[previous_article_index].parent

        else:
            # This is the first blog post; there is no previous article!
            previous_article = ''

    # Now apply blog post template to article content.
    template = read_complete_file(template_path)

    # Insert link to previous article in nav bar template.
    nav_bar = _NAV_BAR_TEMPLATE.format(previous_article=previous_article)
    if not previous_article:
        # No previous articles exist, so remove the `Previous` link from navigation bar.
        nav_bar = nav_bar.replace('<a href="">Previous</a>', '')

    # Create text for describing when this article was last updated.
    last_updated = 'Last updated: ' + datetime.date.today().strftime('%B %d, %Y')
    current_year = datetime.date.today().strftime('%Y')
    configuration = get_configuration()
    blog_post = template.format(nav_bar=nav_bar,
                                article_title=article_title,
                                article_content=article_content_html,
                                last_updated=last_updated,
                                current_year=current_year,
                                blog_title=configuration.blog_title,
                                blog_subtitle=configuration.blog_subtitle,
                                owner=configuration.owner,
                                email_address=configuration.email_address,
                                rss_feed_path=configuration.rss_feed_path,
                                style_sheet=configuration.style_sheet,
                                root_url=configuration.root_url,
                                home_page_link='../')

    return blog_post


def create_article_previews(listing_path=LISTING_PATH):
    """
    Create ArticlePreview objects for all blog artiles in the listing file.

    Args
      listing_path: Location of the listing file.

    Return
      A generator that yeilds ArticlePreview objects.

    """

    listing = read_listing_file(listing_path)

    # Extract the first photograph and paragraph from all articles.
    listing.reverse()
    return (extract_article_preview(article_path) for article_path in listing)
