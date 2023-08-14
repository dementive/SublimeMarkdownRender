import sublime
import sublime_plugin
from .parse import parse_markdown

opened_sheets = []
settings = None


def plugin_loaded():
    global settings
    settings = sublime.load_settings("MarkdownRender.sublime-settings")


class MarkdownRenderCommand(sublime_plugin.WindowCommand):
    def run(self):
        global opened_sheets
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

        content_set = False
        for i in opened_sheets:
            if i.name == name:
                i.set_contents(html_content)
                content_set = True

        if content_set is False:
            sheet = self.window.new_html_sheet(name, html_content)
            setattr(sheet, "name", name)
            opened_sheets.append(sheet)


class MarkDownRenderListener(sublime_plugin.EventListener):
    def on_close(self, view):
        global opened_sheets
        # Clear empty sheets out of opened sheet list
        for i in opened_sheets:
            if not i:
                opened_sheets.remove(i)

    def on_post_save_async(self, view):
        if settings.get("render_markdown_on_save") is True:
            sublime.active_window().run_command("markdown_render")
