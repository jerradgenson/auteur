"""
Tools for reading, writing, parsing, and otherwise working with files.

Author: Jerrad Michael Genson
Email: auteur@jerradgenson.33mail.com
License: BSD 3-Clause
Copyright 2016 Jerrad Michael Genson

"""

# Python built-in modules
import json
import re
from collections import namedtuple
from pathlib import Path
from datetime import datetime

# Third-party modules
import markdown

# First-party modules
from data import CONFIG_FILE_PATH, PROGRAM_NAME


# re pattern to match `Previous` link.
_PREVIOUS_PATTERN = '<a href=".*?">Previous</a>'

# String template for new `Previous` tag text.
_PREVIOUS_TAG_TEMPLATE = '<a href="{}">Previous</a>'

# re pattern to match `Next` link.
_NEXT_PATTERN = 'Home</a> <a href=".*?">Next</a>'

# String "key" used to find the location to insert the `Next` tag in blog posts.
_NEXT_TAG_KEY = 'Home</a>'

# String template for new `Next` tag text.
_NEXT_TAG_TEMPLATE = _NEXT_TAG_KEY + ' <a href="{}">Next</a>'

# Error message to display when there is a problem reading or opening a file.
_FILE_ERROR = "File at '{}' can not be accessed. Please check file permissions and ensure it is not missing or corrupt."

# List of fields in the config file along with their respective types.
_CONFIGURATION_FILE_FIELDS = {'rss_feed_path': Path,
                              'root_url': str,
                              'blog_title': str,
                              'blog_subtitle': str,
                              'owner': str,
                              'email_address': str,
                              'style_sheet': str,
                              'description': str}


Configuration = namedtuple('Configuration', ['program_name'] + list(_CONFIGURATION_FILE_FIELDS))


def insert_next_link(target_article, next_article):
    """
    Insert a `Next` link to `next_article` in `target_article`.
    """

    if not target_article.html:
        target_article.html = read_complete_file(target_article.html_path)

    next_tag_template = _NEXT_TAG_TEMPLATE.format(Path('../') / next_article.target)
    match = re.search(_NEXT_PATTERN, target_article.html)
    if match:
        target_article.html = target_article.html.replace(match.group(0), next_tag_template)

    else:
        target_article.html = target_article.html.replace(_NEXT_TAG_KEY, next_tag_template)


def insert_previous_link(target_article, previous_article):
    """
    Insert a `Previous` link to `previous_article` in `target_article`.
    """

    if not target_article.html:
        target_article.html = read_complete_file(target_article.html_path)

    previous_tag_template = _PREVIOUS_TAG_TEMPLATE.format(Path('../') / previous_article.target)
    match = re.search(_PREVIOUS_PATTERN, target_article.html)
    if match:
        target_article.html = target_article.html.replace(match.group(0), previous_tag_template)


def read_json_file(file_path):
    """
    Read JSON file into memory. Make sure file descriptor is closed properly and provide exception handling
    as appropriate.
    Args
      file_path: Path to the JSON file as a Path object.

    Returns
      Object loaded from JSON file.

    """

    try:
        with file_path.open() as listing_file:
            json_object = json.load(listing_file)

    except IOError:
        msg = _FILE_ERROR.format(file_path)
        raise IOError(msg)

    return json_object


def write_post(article):
    """
    Write blog post to filesystem, update previous post, and update listing file.

    Args
      article: An instance of Article.

    Return
      None

    """

    # Write new blog post to filesystem.
    write_complete_file(article.html, article.html_path)
    try:
        previous_article = article.previous()

    except AttributeError:
        article_database = get_article_database()
        article_database.insert(article)
        article_database.commit()
        previous_article = article.previous()

    if previous_article:
        # Insert `Next` link in previous article.
        insert_next_link(previous_article, article)
        write_complete_file(previous_article.html, previous_article.html_path)

    next_article = article.next()
    if next_article:
        insert_previous_link(next_article, article)
        write_complete_file(next_article.html, next_article.html_path)


def parse_markdown_file(input_path):
    """
    Translate Markdown input into HTML.

    Args
      input_path: Path to the Markdown input file.

    Returns
      HTML string translated from Markdown file.

    """

    markdown_string = read_complete_file(input_path)
    html = markdown.markdown(markdown_string)

    return html


def _handle_file(file_path, file_text=''):
    """
    Internal file handler to abstract generic reading and writing functionality.

    Args
      file_path: Path to the file as a Path object.
      file_text: Optional. A string to write to the file. Will be written in 'w' mode, not 'a' mode.

    Returns
      All text from the target file as a string.

    """

    file_flag = 'w' if file_text else 'r'
    try:
        with file_path.open(file_flag) as file_descriptor:
            if file_text:
                file_descriptor.write(file_text)

            else:
                file_text = file_descriptor.read()

    except IOError:
        msg = _FILE_ERROR.format(file_path)
        raise IOError(msg)

    return file_text


def read_complete_file(file_path):
    """
    Read a standard ASCII or UTF-8 file from filesystem. Make sure file descriptor is closed properly and provide
    exception handling as appropriate

    Args
      file_path: Path to the file as a Path object.

    Returns
      Complete file text as a string.

    """

    return _handle_file(file_path)


def write_complete_file(file_text, file_path):
    """
    Write a standard UTF-8 file to the filesystem. Make sure file descriptor is closed properly and provide exception
    handling as appropriate.

    Args
      file_text: A string to write to the file. Will be written in 'w' mode, not 'a' mode.
      file_path: Path to the file as a Path object.

    Returns
      None

    """

    _handle_file(file_path, file_text)


def _create_get_configuration():
    """
    Create a function for getting the program's global configuration.

    Returns
      A 'get_configuration' function that takes no arguments and returns the program's configuration.

    """

    configuration = None

    def get_configuration():
        """
        Get the program's global configuration as a Configuration object.
        """

        nonlocal configuration
        if not configuration:
            try:
                config_dict = read_json_file(CONFIG_FILE_PATH)

            except IOError:
                msg = 'An {} project could not be found in the current directory.'.format(PROGRAM_NAME)
                raise IOError(msg)

            # Check to make sure each of the config fields is present and valid.
            config_values = {}
            for field_name, type_func in _CONFIGURATION_FILE_FIELDS.items():
                try:
                    config_values[field_name] = type_func(config_dict[field_name])

                except KeyError:
                    msg = "'{}' field is missing from configuration file.".format(field_name)
                    raise KeyError(msg)

                except ValueError:
                    msg = "Value for '{}' in configuration file has invalid type.".format(field_name)
                    raise ValueError(msg)

            # Ensure constructed URL is joined with correct number of slashes.
            if config_values['root_url'][-1] != '/':
                config_values['root_url'] += '/'

            if config_values['style_sheet'][0] == '/':
                config_values['style_sheet'] = config_values['style_sheet'][1:]

            config_values['style_sheet'] = config_values['root_url'] + config_values['style_sheet']
            configuration = Configuration(program_name=PROGRAM_NAME, **config_values)

        return configuration

    return get_configuration


def _create_get_article_database():
    articles = []
    def get_article_database():
        """
        Return an instance of `_ArticleDatabase`.
        WARNING: This class utilizes a global variable that is not thread or concurrency-safe.
        """

        return _ArticleDatabase(articles)

    return get_article_database


class Article:
    """
    Information needed to construct a blog article.

    Args
      article_dict: An article dictionary read from the listing file.

    """

    DATE_FORMAT = '%Y%m%d%H%M'
    HTML_FILENAME = 'index.html'

    def __init__(self, source=None, target=None, pub_date=None, html=None, markdown=None , title=None):
        self.source = Path(source) if source else None
        self.target = Path(target) if target else None
        self.pub_date = pub_date
        self.html = html
        self.markdown = markdown
        self.title = title
        self.__article_database = None

    def pub_date_today(self):
        """
        Set `pub_date` attribute for today's date.
        """

        self.pub_date = datetime.today()

    def pub_date_from_str(self, date_string):
        """
        Set `pub_date` attribute from a datestring of the format `%Y%m%d%H%M`.
        """

        self.pub_date = self.pub_date_str_to_datetime(date_string)

    def str_from_pub_date(self):
        """
        Return `pub_date` attribute as a string of the format `%Y%m%d%H%M`.
        """

        return self.pub_date.strftime(self.DATE_FORMAT)

    def register(self, article_datase):
        """
        Register this article with an article database.
        """

        self.__article_database = article_datase

    def previous(self):
        """
        Return previous article in article database.
        """

        if not self.__article_database:
            raise AttributeError('Article not registered with database.')

        previous_article = None
        for article in self.__article_database:
            if article.title == self.title:
                return previous_article

            previous_article = article

    def next(self):
        """
        Return next article in article database.
        """

        if not self.__article_database:
            raise AttributeError('Article not registered with database.')

        found = False
        for article in self.__article_database:
            if article.title == self.title:
                found = True

            elif found:
                return article

    @property
    def article_dict(self):
        """
        A dictionary representation of the Article.
        """

        pub_date_str = self.str_from_pub_date()
        source = str(self.source) if self.source else '__None__'
        target = str(self.target) if self.target else '__None__'
        title = self.title if self.title else '__None__'
        return {'source': source, 'target': target, 'pub_date': pub_date_str, 'title': title}

    @property
    def html_path(self):
        """
        Path to the article's HTML file.
        """

        return self.target / self.HTML_FILENAME

    @property
    def human_readable_pub_date(self):
        return self.pub_date.strftime('%B %d, %Y')

    @staticmethod
    def date_string_to_datetime(date_string):
        """
        Convert a `date_string` of the format `%Y%m%d%H%M` to a `datetime` object.
        """

        return datetime.strptime(date_string, Article.DATE_FORMAT)


class _ArticleDatabase:
    """
    Interface for article database.
    """

    DATABASE_PATH = Path('.auteur/listing.json')

    def __init__(self, articles):
        if not articles:
            try:
                self.articles = []
                for article_json in read_json_file(self.DATABASE_PATH):
                    source = article_json['source']
                    source = None if source == '__None__' else source
                    target = article_json['target']
                    target = None if target == '__None__' else target
                    pub_date = Article.date_string_to_datetime(article_json['pub_date'])
                    title = article_json['title']
                    article = Article(source, target, pub_date, title=title)
                    article.register(self)
                    self.articles.append(article)

            except IOError:
                # Article database does not exist. That's fine; we can create it.
                pass

        else:
            self.articles = articles

    def __iter__(self):
        return iter(self.articles)

    def commit(self):
        """
        Commit any unsaved changes to the database.
        """

        articles_json = [article.article_dict for article in self.articles]
        try:
            with self.DATABASE_PATH.open('w') as listing_file:
                json.dump(articles_json, listing_file)

        except IOError:
            msg = _FILE_ERROR.format(self.DATABASE_PATH)
            raise IOError(msg)

    def insert(self, article):
        """
        Insert `article` into the database.
        """

        article.register(self)
        for index, other_article in enumerate(self.articles):
            if article.pub_date < other_article.pub_date:
                self.articles.insert(index, article)
                return

        self.articles.append(article)

    def remove(self, article):
        """
        Remove `article` from the database.

        Raises
          `ValueError` if article not in database.
        """

        try:
            article_index = self.find_article_index(article, True)

        except ValueError:
            raise ValueError('Article not found. Can not remove.')

        self.articles.pop(article_index)

    def find_article_index(self, article, title=False):
        """
        Find the index of the previous article in the article database.

        Args
          article: An instance of `Article`.
          title: Optional. Set to `True` to search by `title` instead of `target`.

        Return
          `None` if no previous article exists.

        Raise
          `ValueError` if article isn't in listing.

        """

        for index, current_article in enumerate(self.articles):
            if title and article.title == current_article.title:
                return index

            if not title and article.target == current_article.target:
                return index

        raise ValueError('article not in listing')


# Create 'get_configuration' and `get_article_database` functions.
get_configuration = _create_get_configuration()
get_article_database = _create_get_article_database()