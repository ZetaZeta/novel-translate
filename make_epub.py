# -*- coding: utf-8 -*-
# Python 3.10

from six.moves.html_parser import HTMLParser
from bs4 import BeautifulSoup
import threading
from ebooklib import epub
original_get_template = epub.EpubBook.get_template
from multiprocessing.pool import ThreadPool
import html
import unicodedata
import os
import re

title = ""
start_chapter = 1

outputFilename = title
author = None
exclude_this = None
find_images = None
reverse_chapter_list = False
title_in_fulltext = False
default_chapter_titles = False

done = set()
done_filenames = set()

# set up epub
book = epub.EpubBook()
book.set_title(title)
book.set_language('en')
book.set_identifier(title.replace(' ',''))

if author:
    book.add_author(author)

chapterlist = []

chapter_num = start_chapter

bad_count = 0
good_count = 0

def tag(a, b):
    return "%s=\"%s\"" % (a, b)

def chapter_source_filename(chapter):
    return "chapter_" + str(chapter) + "_EN.txt"

def ch_untranslated_filename(chapter):
    return "chapter_" + str(chapter) + "_CH.txt"

while os.path.exists(chapter_source_filename(chapter_num)):
    with open(chapter_source_filename(chapter_num), "r", encoding="utf-8") as infile:
        raw_text = infile.read()

    raw_text = raw_text.strip()
    raw_text.replace
    raw_chapter_title = raw_text.split('\n')[0].strip()
    chapter_title = re.sub('Chapter +.? *\d+(?:\ ?[<【[]+\d+[]】>]+)? *[:-]? *', 'Chapter '+str(chapter_num) + ': ', raw_chapter_title)

    filename = "chapter_" + str(chapter_num)

    entry_text = raw_text
    
    if not "Chapter" in chapter_title and not "chapter" in chapter_title:
        chapter_title = "Chapter " + str(chapter_num)
        entry_text = chapter_title + "<hr>" + entry_text
    else: 
        entry_text = entry_text.replace(raw_chapter_title, chapter_title + "<hr>", 1)
    entry_text = entry_text.replace('\n', '</p><p>')
    entry_text = '<p>' + entry_text + '</p>'
    
    chapter = epub.EpubHtml(title=chapter_title, file_name=filename + '.xhtml', lang='hr')

    chapter.content=entry_text
    
    # add chapter
    book.add_item(chapter)
    chapterlist.append(chapter)

    chapter_num += 1

print("All chapters parsed, writing file...")

# define Table Of Contents
if len(chapterlist) > 1:
    book.toc = chapterlist;
else:
    print("Only one chapter: " + chapter_title)

# add default NCX and Nav file
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# define CSS style
style = 'BODY {color: white;}'
nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

# add CSS file
book.add_item(nav_css)

# basic spine
book.spine = ['nav']
book.spine += chapterlist

print("Parsing complete. Producing epub...")

# write to the file
epub.write_epub(outputFilename + '.epub', book, {})
