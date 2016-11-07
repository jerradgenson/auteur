"""
Global constants and data types.

Author: Jerrad Michael Genson
Email: auteur@jerradgenson.33mail.com
License: BSD 3-Clause
Copyright 2016 Jerrad Michael Genson

"""

# Python built-in modules
from pathlib import Path


# Path to the configuration file.
CONFIG_FILE_PATH = Path('.auteur/config.json')

# Name of this program.
PROGRAM_NAME = 'Auteur'

# Main RSS template.
RSS_TEMPLATE = Path('.auteur/rss_template.xml')

# RSS item template.
RSS_ITEM_TEMPLATE = Path('.auteur/rss_item_template.xml')

# Location of the default blog post HTML template.
HTML_TEMPLATE_PATH = Path('.auteur/html_template.html')

# Location of the default blog post AMP template.
AMP_TEMPLATE_PATH = Path('.auteur/amp_template.html')

# Relative path to the home page.
HOMEPAGE_LINK = '../index.html'

# Default homepage name for vanilla HTML websites.
HOMEPAGE_NAME = Path('index.html')

# Alternate homepage name for the HTML version in AMP websites.
NO_AMP_HOMEPAGE_NAME = Path('index-noamp.html')
