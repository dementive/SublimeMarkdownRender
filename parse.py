import re


def parse_header(line):
    # Identify and extract header text and level
    match = re.match(r"^(#+)\s(.+)", line)
    if match:
        level = len(match.group(1))
        text = match.group(2)
        if level < 6:
            return f"<h{level}>{text}</h{level}>"
    return line


def parse_paragraph(line):
    if line:
        match = re.match(r"^(\t*|\s*)", line)
        if match is None:
            return
        leading_spaces = match.group(1)
        content = line.strip()
        return f"<p>{leading_spaces}{content}</p>"
    else:
        return line


def parse_lists(line):
    # Identify and convert markdown lists to HTML lists
    match = re.match(r"^(\s*)([*+-])\s(.+)", line)
    if match:
        indent = match.group(1)
        text = match.group(3)
        return f"{indent}<li>{text}</li>"
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
    subbed = re.sub(
        r"```([^`]+)```",
        r'<div id="markdown-code-block">\1</div>',
        text,
        flags=re.DOTALL,
    )
    return subbed


def parse_ordered_list(text):
    # TODO - This does not currently work with nested ordered lists

    # Split the markdown into separate lines
    lines = text.split("\n")

    # Extract the list items from the markdown
    list_items = []
    remaining_lines = []

    ordered_list_start = None  # Line number position of ordered list start

    for i, line in enumerate(lines):
        # Check if the line starts with a number followed by a period and a space
        if re.match(r"^\d+\.\s", line):
            if ordered_list_start is None:
                ordered_list_start = i  # Save the line number position
            list_items.append(line)
        else:
            remaining_lines.append(line)

    # Generate the HTML tags for each list item
    html = ""
    for item in list_items:
        html += "<li>" + re.sub(r"^\d+\.\s", "", item) + "</li>\n"

    # Wrap the list items with the ordered list tag
    if html != "":
        html = "<ol>\n" + html + "</ol>"

    # Insert the ordered list at the correct position within the remaining Markdown content
    if ordered_list_start is not None:
        remaining_lines.insert(ordered_list_start, html)

    # Combine the remaining lines HTML
    remaining_html = "\n".join(remaining_lines)

    # Return the generated HTML
    return remaining_html


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
        if "http" in src:
            prefix = "data:"
        else:
            prefix = "file://"
        return f'<img src="{prefix}{src}" alt="{alt_text}">'
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
    markdown = parse_ordered_list(markdown)

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
        if (
            not line.startswith("#")
            and not line.startswith("*")
            and not line.startswith("-")
            and not line.startswith("[")
            and not line.startswith("!")
            and not line.startswith("<")
        ):
            line = parse_paragraph(line)
            pass
        parsed_lines.append(line)

    return "\n".join(parsed_lines).replace("\n\n", "\n")


# Usage example:
markdown = """
This is a paragraph
it can be multiple lines
<!-- This content will not appear in the rendered Markdown -->
# Heading 1
## Heading 2
- List item 1
- List item 2
+ List item 3
* List item 4
1. First item
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
![Image Name](https://myoctocat.com/assets/images/base-octocat.svg)
[Link](https://www.example.com)
"""

minihtml_output = parse_markdown(markdown)
print(minihtml_output)
