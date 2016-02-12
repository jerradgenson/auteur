"""
Global constants and data types.

Author: Jerrad Michael Genson
Email: auteur@jerradgenson.33mail.com
License: BSD 3-Clause
Copyright 2016 Jerrad Michael Genson

"""

# Python built-in modules
from pathlib import Path


# Location of blog post listing file. This file contains a list of all blog post HTML files in the order that they
# appear in Recursive Descent.
LISTING_PATH = Path('.auteur/listing.json')

# Path to the configuration file.
CONFIG_FILE_PATH = Path('.auteur/config.json')

# Name of this program.
PROGRAM_NAME = 'Auteur'

# Main RSS template.
RSS_TEMPLATE = Path('.auteur/rss_template.xml')

# RSS item template.
RSS_ITEM_TEMPLATE = Path('.auteur/rss_item_template.xml')

# Location of the default blog post HTML template.
TEMPLATE_PATH = Path('.auteur/template.html')

# Relative path to the home page.
HOME_PAGE_LINK = '../index.html'
