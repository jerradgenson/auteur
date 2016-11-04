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
                              'description': str,
                              'generate_amp': bool,
                              'generate_vanilla_html': bool}


Configuration = namedtuple('Configuration', ['program_name'] + list(_CONFIGURATION_FILE_FIELDS))


def insert_next_link(target_article, next_article, amp=False):
    """
    Insert a `Next` link to `next_article` in `target_article`.
    """

    target_html = target_article.amp if amp else target_article.html
    next_link = _NEXT_TAG_TEMPLATE.format(Path('../') / next_article.target)

    # Check if next link is already present.
    match = re.search(_NEXT_PATTERN, target_html)
    if match:
        # Yes, replace current next link.
        target_html = target_html.replace(match.group(0), next_link)

    else:
        # No, add next link for the first time.
        target_html = target_html.replace(_NEXT_TAG_KEY, next_link)

    if amp:
        target_article.amp = target_html

    else:
        target_article.html = target_html


def insert_previous_link(target_article, previous_article, amp=False):
    """
    Insert a `Previous` link to `previous_article` in `target_article`.
    """

    target_html = target_article.amp if amp else target_article.html
    previous_link = _PREVIOUS_TAG_TEMPLATE.format(Path('../') / previous_article.target)
    match = re.search(_PREVIOUS_PATTERN, target_html)
    if match:
        target_html = target_html.replace(match.group(0), previous_link)
        if amp:
            target_article.amp = target_html

        else:
            target_article.html = target_html


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


def validate_configuration():
    """
    Check that the configuration file is readable and contains valid values.
    """

    configuration = get_configuration()
    if not (configuration.generate_amp or configuration.generate_vanilla_html):
        raise ConfigFileError('generate_amp and generate_vanilla_html can not both be false.')


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


class Article:
    """
    Information needed to construct a blog article.

    Args
      article_dict: An article dictionary read from the listing file.

    """

    DATE_FORMAT = '%Y%m%d%H%M'
    HTML_FILENAME = 'index.html'
    NO_AMP_FILENAME = 'index-noamp.html'

    def __init__(self, source, target, pub_date, html=None, amp=None, markdown=None, title=None,
                 html_filename=None, amp_filename=None):
        self.source = Path(source) if source else None
        self.target = Path(target) if target else None
        self.pub_date = pub_date if pub_date else datetime.today()
        self.__html = html
        self.__amp = amp
        self.title = title
        self.__article_database = None
        self.__url = None
        self.__markdown = markdown
        self.__html_read_path = target / html_filename if html_filename else None
        self.__amp_read_path = target / amp_filename if amp_filename else None
        configuration = get_configuration()
        if configuration.generate_amp:
            self.__html_write_path = target / self.NO_AMP_FILENAME

        else:
            self.__html_write_path = target / self.HTML_FILENAME

        if amp_filename:
            self.__amp_write_path = self.__amp_read_path

        elif configuration.generate_amp:
            self.__amp_write_path = target / self.HTML_FILENAME

        else:
            self.__amp_write_path = None

    def write(self, amp=False):
        """
        Write AMP and HTML articles (as applicable) to filesystem.

        Return
          None

        """

        configuration = get_configuration()
        if amp:
            if not self.amp:
                return

            html = self.amp
            path = self.__amp_write_path

        else:
            if not (self.html and configuration.generate_vanilla_html):
                # Recurse to write AMP file.
                return self.write(True)

            html = self.html
            path = self.__html_write_path

        # Write new blog post to filesystem.
        write_complete_file(html, path)
        if amp:
            self.__amp_read_path = self.__amp_write_path

        else:
            self.__html_read_path = self.__html_write_path

        if not amp:
            # Recurse to write AMP file.
            self.write(True)

    def update_links(self, amp=False):
        """
        Update links to next and previous articles.
        """

        if self.previous:
            # Insert link to previous article
            insert_previous_link(self, self.previous, amp=amp)

        if self.next:
            # Insert link to next article.
            insert_next_link(self, self.next, amp=amp)

        if self.amp and not amp:
            self.update_links(True)

    def pub_date_today(self):
        """
        Set `pub_date` attribute for today's date.
        """

        self.pub_date = datetime.today()

    def pub_date_from_str(self, date_string):
        """
        Set `pub_date` attribute from a datestring of the format `%Y%m%d%H%M`.
        """

        self.pub_date = self.date_string_to_datetime(date_string)

    def str_from_pub_date(self):
        """
        Return `pub_date` attribute as a string of the format `%Y%m%d%H%M`.
        """

        return self.pub_date.strftime(self.DATE_FORMAT)

    def register(self, article_database):
        """
        Register this article with an article database.
        """

        self.__article_database = article_database

    @property
    def previous(self):
        """
        Return previous article in article database.
        """

        if not self.__article_database:
            raise DatabaseError('Article is not registered with a database.')

        previous_article = None
        for article in self.__article_database:
            if article.title == self.title:
                return previous_article

            previous_article = article

    @property
    def next(self):
        """
        Return next article in article database.
        """

        if not self.__article_database:
            raise DatabaseError('Article is not registered with a database.')

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
        html_filename = self.html_path.name if self.html_path else '__None__'
        amp_filename = self.amp_path.name if self.amp else '__None__'
        return {'source': source, 'target': target, 'pub_date': pub_date_str, 'title': title,
                'html_filename': html_filename, 'amp_filename': amp_filename}

    @property
    def html_path(self):
        """
        Path to the article's HTML file.
        """

        return self.__html_read_path

    @property
    def amp_path(self):
        """
        Path to the article's AMP file.
        """

        return self.__amp_read_path

    @property
    def human_readable_pub_date(self):
        return self.pub_date.strftime('%B %d, %Y')

    @property
    def url(self):
        if self.__url:
            return self.__url

        else:
            configuration = get_configuration()
            self.__url = build_article_url(configuration.root_url, self.target)
            return self.__url

    @property
    def markdown(self):
        if self.__markdown:
            return self.__markdown

        else:
            self.__markdown = read_complete_file(self.source)
            return self.__markdown

    @staticmethod
    def date_string_to_datetime(date_string):
        """
        Convert a `date_string` of the format `%Y%m%d%H%M` to a `datetime` object.
        """

        return datetime.strptime(date_string, Article.DATE_FORMAT)

    def gethtml(self):
        if not self.__html:
            if self.html_path:
                try:
                    self.__html = read_complete_file(self.html_path)

                except OSError:
                    return None

            else:
                return None

        return self.__html

    def sethtml(self, new_html):
        self.__html = new_html

    html = property(gethtml, sethtml)

    def getamp(self):
        if not self.__amp:
            if self.amp_path:
                try:
                    self.__amp = read_complete_file(self.amp_path)

                except OSError:
                    return None

                else:
                    self.__html_write_path = self.target / self.NO_AMP_FILENAME

            else:
                return None

        return self.__amp

    def setamp(self, new_amp):
        self.__amp = new_amp
        self.__html_write_path = self.target / self.NO_AMP_FILENAME

    amp = property(getamp, setamp)


class _ArticleDatabase:
    """
    Interface for article database.
    """

    DATABASE_PATH = Path('.auteur/database.json')

    def __init__(self, articles):
        if not articles:
            try:
                self.articles = []
                for article_json in read_json_file(self.DATABASE_PATH):
                    source = Path(self.string_or_none(article_json['source']))
                    target = Path(self.string_or_none(article_json['target']))
                    html_filename = self.string_or_none(article_json['html_filename'])
                    amp_filename = self.string_or_none(article_json['amp_filename'])
                    pub_date = Article.date_string_to_datetime(article_json['pub_date'])
                    title = article_json['title']
                    article = Article(source, target, pub_date,
                                      title=title,
                                      html_filename=html_filename,
                                      amp_filename=amp_filename)

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

    @staticmethod
    def string_or_none(string):
        """
        If `string` is equal to `__None__`, return `None`; otherwise, return `String`.
        """

        return None if string == '__None__' else string


class DatabaseError(Exception):
    """
    Indicates an exception related to the `ArticleDatabase`.
    """


class ConfigFileError(Exception):
    """
    Indicates an exception related to the configuration file.
    """


# Create 'get_configuration' and `get_article_database` functions.
get_configuration = _create_get_configuration()
get_article_database = _create_get_article_database()