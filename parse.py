import re
import os
import sublime
import urllib.request
from .css.css import CSS

INDENTATION_AMOUNT = 7


def parse_header(line, inside_code_block):
    # Identify and extract header text and level
    if inside_code_block:
        return line
    match = re.match(r"^(#+)\s(.+)", line)
    if match:
        level = min(len(match.group(1)), 6)
        text = match.group(2)
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
        indentation += INDENTATION_AMOUNT
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
    line = re.sub(r"(\~\~)([^\~]+)(\~\~)", r"<small><i>\2</i></small>", line)
    return line


def parse_links(line):
    # Identify and convert links ([text](url) -> <a href="url">text</a>)
    line = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2" title="\2">\1</a>', line)
    return line


def parse_quoted_text(line):
    match = re.match(r"^>\s*(.+)", line)
    if match:
        text = match.group(1)
        return f'<div id="markdown-quote"><tt id="blockquote">{text}</tt></div>'
    return line


def parse_task_list(line):
    # Identify and convert markdown task lists to HTML with specific div IDs for completed and incomplete tasks
    match = re.match(r"^- \[(x|X)\] (.+)", line)
    checked_image = os.path.join(
        sublime.packages_path().replace("\\", "/"), "MarkdownRender", "css", "styles/checkbox.png"
    )
    unchecked_image = os.path.join(
        sublime.packages_path().replace("\\", "/"),
        "MarkdownRender",
        "css",
        "styles/checkbox_incomplete.png",
    )
    if match:
        text = match.group(2)
        return f'<div id="markdown-task-completed"><img src="file://{checked_image}" alt="[Completed Task]" width="22" height="22"> {text}</div>'
    match = re.match(r"^- \[ \] (.+)", line)
    if match:
        text = match.group(1)
        return f'<div id="markdown-task-incomplete"><img src="file://{unchecked_image}" alt="[Completed Task]" width="22" height="22"> {text}</div>'
    return line


def get_last_dir(string):
    return string.replace("\\", "/").rstrip("/").rpartition("/")[0]


def parse_image(line, view):
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
            file_path = os.path.join(
                sublime.packages_path().replace("\\", "/"), "MarkdownRender", "ImageCache/"
            )
            full_path = file_path + file_name
            if src.startswith("http://") or src.startswith("https://"):
                urllib.request.urlretrieve(src, full_path)
            if os.path.exists(full_path):
                src = full_path
            if src.startswith("...."):
                view_directory = get_last_dir(
                    get_last_dir(get_last_dir(get_last_dir(view.file_name())))
                )
                src = view_directory + src.partition("....")[2]
            elif src.startswith("..."):
                view_directory = get_last_dir(
                    get_last_dir(get_last_dir(view.file_name()))
                )
                print(view_directory)
                src = view_directory + src.partition("...")[2]
            elif src.startswith(".."):
                view_directory = get_last_dir(get_last_dir(view.file_name()))
                src = view_directory + src.partition("..")[2]
            elif src.startswith("."):
                view_directory = (
                    view.file_name().replace("\\", "/").rstrip("/").rpartition("/")[0]
                )
                src = view_directory + src.partition(".")[2]
        return f'<img src="file://{src}" alt="{alt_text}">'
    return line


def parse_code_block(line, inside_code_block):
    if not line:
        return "", False
    indentation = 0
    for i in range(get_indentation_level(line)):
        indentation += INDENTATION_AMOUNT
    match = re.match(r"^```(\w+)?$", line)
    if match:
        if inside_code_block:
            return "</code></div></div><br>", False
        return '<div class="box-for-codebox"><div class="codebox"><code>', True
    # Code line
    if inside_code_block:
        return (
            f'<code style="padding-left: {indentation}">{line}</code>',
            inside_code_block,
        )
    return line, inside_code_block


def parse_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def parse_markdown(markdown, view):
    markdown = markdown.replace("\t", "    ")
    markdown = parse_comments(markdown)
    parsed_lines = []
    inside_code_block = False
    lines = markdown.split("\n")
    css = CSS()

    for line in lines:
        # Load order here is important
        line, inside_code_block = parse_code_block(line, inside_code_block)
        line = parse_header(line, inside_code_block)
        line = parse_task_list(line)
        line = parse_lists(line)
        line = parse_emphasis(line)
        line = parse_image(line, view)
        line = parse_links(line)
        line = parse_tags(line)
        line = parse_quoted_text(line)
        parsed_lines.append(line)

    lines = "\n".join(parsed_lines).replace("\n\n", "\n").replace("\n", "<br>")
    html = f"""
    <body id=markdown-render-body>
        <style>
            {css.default}
        </style>
        {lines}
    </body>
    """
    return html


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
# This is a block of code!
def hello():
    return "hi"
```
![Image Name](https://www.artic.edu/iiif/2//18092196-50ae-3ff1-9205-1b3110e966c3/full/843,/0/default.jpg)
[Link](https://www.example.com)


This is a paragraph

it can be multiple lines
"""
