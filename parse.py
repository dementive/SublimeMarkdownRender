import re
import os
from sublime import packages_path
import urllib.request


def parse_header(line):
    # Identify and extract header text and level
    match = re.match(r"^(#+)\s(.+)", line)
    if match:
        level = len(match.group(1))
        text = match.group(2)
        if level < 6:
            return f"<h{level}>{text}</h{level}>"
    return line


def get_indentation_level(line):
    match = re.search(r"^(\s+)", line)
    if match:
        return len(match.group(1))
    return 0


def parse_lists(line):
    # Identify and convert markdown lists to HTML lists
    indentation = 0
    for i in range(get_indentation_level(line)):
        indentation += 7
    match = re.match(r"^(\t*|\s*)([*+-]|\d+\.)\s(.+)", line)
    if match:
        list_type = match.group(2)
        text = match.group(3)
        list_character = "•"
        if re.match(r"^\d+\.", list_type):
            list_character = list_type
        list_item = f'<p id="markdown-list-item" style="padding-left: {indentation}px; margin-top: 0; margin-bottom: 0;">{list_character} {text}</p>'
        return list_item
    return line


def parse_tags(line):
    line = line.replace("<sub>", "<small>").replace("</sub>", "</small>")
    line = line.replace("<sup>", "<big>").replace("</sup>", "</big>")
    return line


def parse_emphasis(line):
    line = re.sub(r"(\*\*\*)([^\*]+)(\*\*\*)", r"<strong><em>\2</em></strong>", line)
    line = re.sub(r"(\*\*)([^*]+)(\*\*)", r"<strong>\2</strong>", line)
    line = re.sub(r"(\*)([^*]+)(\*)", r"<em>\2</em>", line)
    line = re.sub(r"(__)([^_]+)(__)", r"<strong>\2</strong>", line)
    line = re.sub(r"(_)([^_]+)(_)", r"<em>\2</em>", line)
    line = re.sub(
        r"(\~\~)([^\~]+)(\~\~)", r"<div id=\"markdown-strikethrough\">\2</del>", line
    )
    return line


def parse_links(line):
    # Identify and convert links ([text](url) -> <a href="url">text</a>)
    line = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', line)
    return line


def parse_quoted_text(line):
    match = re.match(r"^>\s*(.+)", line)
    if match:
        text = match.group(1)
        return f'<div id="markdown-quote">{text}</div>'
    return line


def parse_code_blocks(text):
    # TODO - Code blocks should be highlighted properly in html output just like in sublime if possible.
    # Not really sure how to go about this since minihtml doesn't exactly support syntax highlighting like a normal sheet in sublime would
    # All of the potential code block syntax embeddings can be found in the sublime markdown syntax and are as follows
    # actionscript|as
    # applescript|osascript
    # clojure|clj
    # c|h
    # c\+\+|cc|cpp|cxx|h\+\+|hpp|hxx
    # csharp|c\#|cs
    # css
    # diff|patch
    # bat|cmd|dos
    # erlang|escript
    # graphviz
    # go(?:lang)?
    # haskell
    # html\+php
    # html
    # java
    # javascript|js
    # jsonc?
    # jspx?
    # jsx
    # lisp
    # lua
    # makefile
    # matlab
    # objc|obj-c|objectivec|objective-c
    # objc\+\+|obj-c\+\+|objectivec\+\+|objective-c\+\+
    # ocaml
    # perl
    # php|inc
    # python|py
    # regexp?
    # rscript|r|splus
    # ruby|rb|rbx
    # rust|rs
    # scala
    # console|shell
    # shell-script|sh|bash|zsh
    # sql
    # tsx
    # typescript|ts
    # atom|plist|svg|xjb|xml|xsd|xsl
    # yaml|yml
    subbed = re.sub(
        r"```([^`]+)```",
        r'<div id="markdown-code-block">\1</div>',
        text,
        flags=re.DOTALL,
    )
    return subbed


def parse_task_list(line):
    # Identify and convert markdown task lists to HTML with specific div IDs for completed and incomplete tasks
    match = re.match(r"^- \[(x|X)\] (.+)", line)
    if match:
        text = match.group(2)
        return f'<div id="markdown-task-completed">{text}</div>'
    match = re.match(r"^- \[ \] (.+)", line)
    if match:
        text = match.group(1)
        return f'<div id="markdown-task-incomplete">{text}</div>'
    return line


def parse_image(line):
    match = re.match(r"^!\[([^]]+)\]\(([^)]+)\)$", line)
    if match:
        alt_text = match.group(1)
        src = match.group(2)
        if (
            src.endswith(".png")
            or src.endswith(".jpeg")
            or src.endswith(".jpg")
            or src.endswith(".gif")
        ):
            file_name = src.replace("\\", "/").rstrip("/").rpartition("/")[2]
            file_path = os.path.join(packages_path(), "MarkdownRender", "ImageCache/")
            full_path = file_path + file_name
            urllib.request.urlretrieve(src, full_path)
            if os.path.exists(full_path):
                src = full_path
        return f'<img src="file://{src}" alt="{alt_text}">'
    return line


def parse_comments(text):
    # pattern to match Markdown comments
    pattern = r"<!--.*?-->"

    # replace Markdown comments with an empty string
    cleaned_text = re.sub(pattern, "", text, flags=re.DOTALL)

    return cleaned_text


def parse_markdown(markdown):
    markdown = parse_comments(markdown)
    markdown = parse_code_blocks(markdown)

    parsed_lines = []
    lines = markdown.split("\n")

    for line in lines:
        # Load order here is important
        line = parse_header(line)
        line = parse_task_list(line)
        line = parse_lists(line)
        line = parse_emphasis(line)
        line = parse_image(line)
        line = parse_links(line)
        line = parse_tags(line)
        line = parse_quoted_text(line)
        parsed_lines.append(line)

    lines = "\n".join(parsed_lines).replace("\n\n", "\n")
    return lines.replace("\n", "<br>")


# Usage example:
markdown = """
<!-- This content will not appear in the rendered Markdown -->
# Heading 1
## Heading 2
- List item 1
- List item 2
    + List item 3
        - List item 4
        - List item 5
* List item 6
1. First item
    1. Hello
    2. Hi
2. Second item 
3. Third item
- [x] #739
- [ ] fff
- [ ] fff
*Italic text*
**Bold text**
**This text is _extremely_ important**
*** Hello ***
<sub>This is subscript</sub>
<sup>This is superscript</sup>
> This is a quote - Unknown
```
This is a block of code!
def hello():
    return "hi"
```
![Image Name](https://www.artic.edu/iiif/2//18092196-50ae-3ff1-9205-1b3110e966c3/full/843,/0/default.jpg)
[Link](https://www.example.com)


This is a paragraph

it can be multiple lines
"""

minihtml_output = parse_markdown(markdown)
# print(minihtml_output)
