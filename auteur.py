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
from html_tools import generate_landing_page, generate_post, create_article_previews


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

    # Create HTML output path from Markdown input path.
    output_path = args.input_path.parent / Path('index.html')

    # Translate Markdown input into HTML.
    html = file_tools.parse_markdown_file(args.input_path)

    # Apply blog post template to Markdown-to-HTML translation.
    blog_post = generate_post(html, output_path)

    # Write blog post to filesystem, update previous post, and update listing file.
    file_tools.write_post(blog_post, output_path)


def build_website(args):
    """
    Recreate all articles in website.

    Returns
      None

    """

    # First, load the listing file.
    listing = file_tools.read_listing_file(data.LISTING_PATH)

    # Now iterate over each item in the listing file and regenerate the corresponding web page.
    for article_html_path in listing:
        # First, try to determine if a corresponding markdown file exists.
        # Path to use if the markdown file is in the same directory as the html file.
        article_directory = article_html_path.parent
        article_md_path1 = article_directory / Path(article_directory.stem).with_suffix('.md')

        # Path to use if the markdown file is in the parent directory.
        article_parent_directory = article_directory.parent
        article_md_path2 = article_parent_directory / Path(article_directory.stem).with_suffix('.md')
        if article_md_path1.exists():
            # A corresponding markdown file does exist, so get article content from this.
            article_content = file_tools.parse_markdown_file(article_md_path1)

        elif article_md_path2.exists():
            article_content = file_tools.parse_markdown_file(article_md_path2)

        else:
            # A corresponding markdown file doesn't exist, so get content from HTML file instead.
            full_html = file_tools.read_complete_file(article_html_path)
            article_content_match = re.search('<article>.+?</section>', full_html, re.DOTALL)
            article_content = article_content_match.group(0)
            # Remove HTML tags at beginning and end of article content.
            article_content = article_content.replace('<article>', '').replace('</section>', '')
            article_content = article_content.replace('<section class="main_content">', '')
            article_content = article_content.replace('<section class="article_content">', '')

        # Apply blog post template to article content.
        blog_post = generate_post(article_content, article_html_path)

        # Write blog post to filesystem, update previous post, and update listing file.
        file_tools.write_post(blog_post, article_html_path)


def create_rss_feed():
    """
    Create XML for an RSS feed for the blog site.

    Return
      XML string for RSS feed.

    """

    # Get iterable of ArticlePreview objects.
    articles = create_article_previews()

    # Load main RSS template.
    rss_template = file_tools.read_complete_file(RSS_TEMPLATE)

    # Load RSS item template.
    item_template = file_tools.read_complete_file(RSS_ITEM_TEMPLATE)

    configuration = file_tools.get_configuration()

    items = ""
    for article in articles:
        url = build_article_url(configuration.root_url, article.path)
        dt_instance = datetime.datetime.strptime(article.publication_date, "%B %d, %Y")
        creation_date = dt_instance.strftime('%a, %d %b %Y %H:%M:%S GMT')
        text = article.text + '</p>\n'
        if article.first_photo:
            photo = re.sub('<figcaption>.+?</figcaption>', '', article.first_photo)
            text = photo + '\n' + text

        items += item_template.format(article_title=article.title,
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
    add_parser.set_defaults(func=add_new_article)

    build_subparser = subparsers.add_parser('build', help='Build or rebuild the entire blog website.')
    build_subparser.set_defaults(func=build_website)

    return parser.parse_args()


if __name__ == '__main__':
    auteur()
