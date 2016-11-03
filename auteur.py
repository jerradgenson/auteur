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

import file_tools
from data import RSS_TEMPLATE, RSS_ITEM_TEMPLATE
from file_tools import build_article_url
from html_tools import generate_landing_page, generate_vanilla_html, create_article_previews


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

    configuration = file_tools.get_configuration()
    source = args.input_path
    target = source.parent
    if args.pub_date:
        pub_date = datetime.datetime.strptime(args.pub_date, '%B %d, %Y')

    else:
        pub_date = None

    article = file_tools.Article(source, target, pub_date)
    if source.suffix != '.html':
        # Translate Markdown input into HTML.
        article.html = file_tools.parse_markdown_file(source)

        # Apply blog post template to Markdown-to-HTML translation.
        article.html = generate_vanilla_html(article)

        if configuration.generate_amp:
            article.amp = generate_amp(article)
            file_tools.write_post(article, amp=True)

    # Write blog post to filesystem, update previous post.
    file_tools.write_post(article)
    file_tools.get_article_database().commit()


def remove_article(args):
    """
    Remove article from website.

    Args
      args A Namespace object with arguments from the command line.

    Returns
      None

    """

    article_database = file_tools.get_article_database()
    article_database.remove(args)
    article_database.commit()
    build_website(args)


def build_website(args):
    """
    Recreate all articles in website.

    Returns
      None

    """

    configuration = file_tools.get_configuration()
    article_database = file_tools.get_article_database()

    # Now iterate over each article in the database and regenerate the corresponding web page.
    for article in article_database:
        if article.source.suffix != '.html':
            # Try to load article contents from markdown file.
            article.html = file_tools.parse_markdown_file(article.source)

            # Apply blog post template to article content.
            article.html = generate_vanilla_html(article)

            if configuration.generate_amp:
                article.amp = generate_amp(article)
                file_tools.write_post(article, amp=True)

        else:
            # A corresponding markdown file doesn't exist, so get content from HTML file instead.
            article.html = file_tools.read_complete_file(article.html_path)

        # Write blog post to filesystem and update previous post.
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

    remove_parser = subparsers.add_parser('remove', help='Remove an article from the blog.')
    remove_parser.add_argument('title', help='Title of the article to remove.')
    remove_parser.set_defaults(func=remove_article)

    build_subparser = subparsers.add_parser('build', help='Build or rebuild the entire blog website.')
    build_subparser.set_defaults(func=build_website)

    return parser.parse_args()


if __name__ == '__main__':
    auteur()
