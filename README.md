# Auteur

Auteur is a highly customizable and configurable blog site creator, written for bloggers who desire to create their
own blog website and "get their hands dirty" with the HTML and CSS, but avoid the costly maintenance required to
write it by hand.

Please keep in mind that while Auteur is usable, it is still in the alpha stage of development, so
some features and niceties are missing, and it hasn't been tested on all platforms. Platforms it has been tested and
known to work on include recent versions of Fedora and Ubuntu.

## Requirements

Before downloading Auteur, make sure your system meets the following list of requirements:
* Operating system: Fedora 27 or Ubuntu 17.10 (other platforms may work but have not been tested)
* Python 3.6 is installed
* Markdown for Python 3.6 is installed

## Getting Started

What follows is a brief tutorial on how to create your first Auteur project.

1. Download the Auteur source from here: https://github.com/jerradgenson/auteur/archive/master.zip
2. Extract Auteur into the directory of your choosing. No install scripts exist for Auteur at this time
but you may make links in your bin directory manually or simply run Auteur from the extraction directory.
3. Create a new directory for your blog project. It can be anywhere on your machine. For simplicity's sake, we'll refer
to this as the blog directory.
4. Copy "resources" and ".auteur" from the auteur directory to your blog directory.
5. Open "resources/config.json" and fill in the missing configuration details for your site.
  * `root_url` is the URL for the homepage of your blog site. Example: "http://www.gensonsoftworks.com/auteur-demo/"
  * `blog_title` is the title of your blog site. Example: "Auteur Demo"
  * `blog_subtitle` is the subtitle for your blog site. This may be left blank if your blog has no subtitle.
  * `owner` is the copyright holder for the blog site. This is not necessarily the same as the author of your posts.
  * `email_address` is the address that users of your site can use to get in contact with you.
  * `description` is a brief description of your blog's content and target audience.
6. If you wish to display a background image on your site, you can add a file named "background.jpg" to the resources directory.
7. You are now ready to write your first blog post! Create a subdirectory in your blog directory for the post.
8. Blog posts are written in Markdown. Create a Markdown file (plain text file ending in ".md") in the subdirectory
for your blog post.
9. Autuer will use the first H1 heading it finds as the blog post title. Beyond that, you can use any Markdown
formatting you choose in your posts. See here for more information on Markdown: https://daringfireball.net/projects/markdown/syntax
10. Once you're done writing your post, use Auteur's `add` command: `auteur.py add <path-to-blog-post.md>`
11. When you're ready to create the blog site, use Auteur's `build` command from the root of the blog directory:
`<path-to-auteur.py> build`
12. Anytime you make a change to an existing blog posts, you can use the `build` command to update the site.
13. Finally, upload the blog directory to a web host of your choosing. The site should now be working and accesible
on the Internet.  
