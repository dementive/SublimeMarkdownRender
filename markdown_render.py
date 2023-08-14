import sublime
import sublime_plugin
from .parse import parse_markdown


class MarkdownRenderCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Your code to generate the HTML content
        view = self.window.active_view()

        if view is None:
            return
        filename = view.file_name()
        if filename is None:
            return
        if not filename.endswith(".md"):
            return
        markdown_content = view.substr(sublime.Region(0, view.size()))
        html_content = parse_markdown(markdown_content)

        # Create a new HTML sheet
        name = (
            filename.replace(".md", "")
            .replace("\\", "/")
            .rstrip("/")
            .rpartition("/")[2]
        )
        self.window.new_html_sheet(name, html_content)
