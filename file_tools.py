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

# Third-party modules
import markdown

# First-party modules
from data import LISTING_PATH, CONFIG_FILE_PATH, PROGRAM_NAME


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
                              'style_sheet': str}


Configuration = namedtuple('Configuration', ['program_name'] + list(_CONFIGURATION_FILE_FIELDS))


def read_listing_file(listing_path):
    """
    Read listing file contents into memory. This function should be called instead of reading the listing file directly
    so the file contents can be converted to a higher-order object.

    Args
      listing_path: Path to the listing file as a Path object.

    Returns
      A list of Path objects for blog articles in chronological order.

    """

    listing = read_json_file(listing_path)
    return [Path(article_path) / Path('index.html') for article_path in listing]


def write_listing_file(listing, listing_path):
    """
    Write article listing to filesystem. This function should be called instead of writing the listing file directly
    so the listing object can be properly serialized.

    Args
      listing: A list of Path objects for blog articles in chronological order.
      listing_path: Path to the listing file as a Path object.

    Returns
      None

    """

    listing = [str(article_path.parent) for article_path in listing]
    try:
        with listing_path.open('w') as listing_file:
            json.dump(listing, listing_file)

    except IOError:
        msg = _FILE_ERROR.format(listing_path)
        raise IOError(msg)


def read_json_file(file_path):
    """
    Write JSON file into memory. Make sure file descriptor is closed properly and provide exception handling
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


def write_post(blog_post, output_path, listing_path=LISTING_PATH):
    """
    Write blog post to filesystem, update previous post, and update listing file.

    Args
      blog_post: Final blog post HTML string.
      output_path: Path to write blog post to as Path object.
      listing_path: Path to blog post listing file as Path object.

    Return
      None

    """

    # Write new blog post to filesystem.
    write_complete_file(blog_post, output_path)
    listing = read_listing_file(listing_path)

    # Determine index of previous article, if one exists.
    try:
        previous_article_index = listing.index(output_path) - 1

    except (AttributeError, ValueError):
        # Current article not yet in listing.
        previous_article_index = len(listing) - 1
        if previous_article_index < 0:
            # No previous article; this one is the first.
            previous_article_index = None

        # Update blog post listing to include current post.
        listing.append(output_path)
        write_listing_file(listing, listing_path)

    if previous_article_index is not None:
        # Insert `Next` link in previous article.
        previous_article = read_complete_file(listing[previous_article_index])

        # Check to see if `Next` link already exists before inserting one.
        if not re.search('<a href=".+?">Next</a>', previous_article):
            # Create link to current post from previous post.
            next_tag_template = _NEXT_TAG_TEMPLATE.format(Path('../') / output_path.parent)
            previous_article = previous_article.replace(_NEXT_TAG_KEY, next_tag_template)
            write_complete_file(previous_article, listing[previous_article_index])


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

            # Build fully-qualified path to style sheet.
            root_url = config_values['root_url']
            style_sheet = config_values['style_sheet']

            # Ensure constructed URL is joined with correct number of slashes.
            if config_values['root_url'][-1] != '/':
                config_values['root_url'] += '/'

            if config_values['style_sheet'][0] == '/':
                config_values['style_sheet'] = config_values['style_sheet'][1:]

            config_values['style_sheet'] = config_values['root_url'] + config_values['style_sheet']
            configuration = Configuration(program_name=PROGRAM_NAME, **config_values)

        return configuration

    return get_configuration


# Create 'get_configuration' function.
get_configuration = _create_get_configuration()
