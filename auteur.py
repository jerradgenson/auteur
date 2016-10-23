"""
Auteur main module.

usage: auteur.py [-h] [-d] {add,build} ...

Create an entire blog website from simple Markdown files.

positional arguments:
  {add,build}
    add        Add an article to the blog.
    build      Build or rebuild the entire blog website.

optional arguments:
  -h, --help   show this help message and exit
  -d, --debug  Launch program in debug mode.

Author: Jerrad Michael Genson
Email: auteur@jerradgenson.33mail.com
License: BSD 3-Clause
Copyright 2016 Jerrad Michael Genson

"""

# Python built-in modules
import argparse
import datetime
import re
from pathlib import Path

# First-party modules
import data
import file_tools
from data import RSS_TEMPLATE, RSS_ITEM_TEMPLATE
from html_tools import generate_landing_page, generate_post, create_article_previews, preprocess_raw_html


def auteur():
    """ Program's "main" function. Execution normally starts here. """


    try:
        cl_args = parse_command_line()
        cl_args.func(cl_args)
        configuration = file_tools.get_configuration()
        landing_page = generate_landing_page()
        file_tools.write_complete_file(landing_page, Path('index.html'))
        rss_feed = create_rss_feed()
        file_tools.write_complete_file(rss_feed, configuration.rss_feed_path)

    except Exception as exception:
        if cl_args.debug:
            raise

        else:
            print(exception)


def add_new_article(args):
    """
    Add new article to the website.

    Args
      args: A Namespace object with arguments from the command line.

    Returns
      None

    """

    article = file_tools.Article()
    article.source = args.input_path
    article.target = article.source.parent
    if args.pub_date:
        article.pub_date = datetime.datetime.strptime(args.pub_date, '%B %d, %Y')

    else:
        article.pub_date_today()

    if article.source.suffix == '.html':
        # Treat the source file as an html file.
        article.html = file_tools.read_complete_file(args.input_path)

    else:
        # Translate Markdown input into HTML.
        article.html = file_tools.parse_markdown_file(article.source)

        # Apply blog post template to Markdown-to-HTML translation.
        article.html = generate_post(article)

    # Write blog post to filesystem, update previous post, and update listing file.
    file_tools.write_post(article)


def build_website(args):
    """
    Recreate all articles in website.

    Returns
      None

    """

    # First, load the listing file.
    listing = file_tools.read_listing_file(data.LISTING_PATH)

    # Now iterate over each item in the listing file and regenerate the corresponding web page.
    for article in listing:
        if article.source.suffix != '.html':
            # Try to load article contents from markdown file.
            article.html = file_tools.parse_markdown_file(article.source)

            # Apply blog post template to article content.
            article.html = generate_post(article)

        else:
            # A corresponding markdown file doesn't exist, so get content from HTML file instead.
            raw_html = file_tools.read_complete_file(article.html_path)

        # Write blog post to filesystem, update previous post, and update listing file.
        file_tools.write_post(article)


def create_rss_feed():
    """
    Create XML for an RSS feed for the blog site.

    Return
      XML string for RSS feed.

    """

    # Get iterable of ArticlePreview objects.
    article_previews = create_article_previews()

    # Load main RSS template.
    rss_template = file_tools.read_complete_file(RSS_TEMPLATE)

    # Load RSS item template.
    item_template = file_tools.read_complete_file(RSS_ITEM_TEMPLATE)

    configuration = file_tools.get_configuration()

    items = ""
    for article_preview in article_previews:
        url = build_article_url(configuration.root_url, article_preview.html_path)
        creation_date = article_preview.pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
        text = article_preview.intro_text + '</p>\n'
        if article_preview.first_photo:
            photo = re.sub('<figcaption>.+?</figcaption>', '', article_preview.first_photo)
            text = photo + '\n' + text

        items += item_template.format(article_title=article_preview.title,
                                      article_url=url,
                                      article_date=creation_date,
                                      article_description=text)

    return rss_template.format(items=items)


def build_article_url(root_url, article_path):
    """
    Build URL for blog article. Using this function will ensure the URL is constructed correctly, regardless of what
    platform the article path is for.

    Args
      root_url: URL string to website root directory.
      article_path: Path to the article on the server relative to the website root as either a string or Path object.

    Return
      A URL string for the blog article.

    """

    article_path_string = str(article_path)

    # Convert backlashes to forward slashes in case this is a Windows path.
    article_path_string = article_path_string.replace('\\', '/')

    # Remove existing slashes between parts of the URL to make sure they're joined correctly.
    if root_url[-1] == '/':
        root_url = root_url[:-1]

    if article_path_string[0] == '/':
        article_path_string = article_path_string[1:]

    article_url = '/'.join((root_url, article_path_string))

    return article_url


def parse_command_line():
    """
    Parse command line arguments.

    Return
      The `namespace` instance returned by `argparse`.

     """

    msg = 'Create an entire blog website from simple Markdown files.'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('-d', '--debug', action='store_true', help='Launch program in debug mode.')
    subparsers = parser.add_subparsers()

    add_parser = subparsers.add_parser('add', help='Add an article to the blog.')
    add_parser.add_argument('input_path', help='Input Markdown file to turn into blog post.', type=Path)
    add_parser.add_argument('--pub-date', help='Specify a publication date for this article.')
    add_parser.set_defaults(func=add_new_article)

    build_subparser = subparsers.add_parser('build', help='Build or rebuild the entire blog website.')
    build_subparser.set_defaults(func=build_website)

    return parser.parse_args()


if __name__ == '__main__':
    auteur()
