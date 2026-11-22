"""Render untrusted Markdown using only local GTK widgets and escaped text."""

from html import escape

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Comment, Keyword, Literal, Name, Number, Operator
from pygments.util import ClassNotFound

from .ui import Gdk, Gtk, Pango

MARKDOWN = MarkdownIt("commonmark", {"html": False, "maxNesting": 16}).enable("table")
INLINE_STYLES = {"strong": "b", "em": "i"}
TOKEN_COLORS = (
    (Comment, "#81949c", "#57686d"),
    (Keyword, "#d0afff", "#66399a"),
    (Name.Function, "#a1cdff", "#17618e"),
    (Number, "#f3c592", "#8b4820"),
    (Literal.String, "#a7d6a6", "#276347"),
    (Operator, "#9dd7dc", "#276569"),
)


def label(content="", style=None):
    widget = Gtk.Label(label=content, xalign=0)
    widget.set_line_wrap(True)
    widget.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    widget.set_max_width_chars(1)
    if style:
        widget.get_style_context().add_class(style)
    return widget


def inline_markup(nodes):
    fragments = []
    for node in nodes:
        if node.type == "text":
            fragments.append(escape(node.content, quote=False))
        elif node.type in ("softbreak", "hardbreak"):
            fragments.append("\n" if node.type == "hardbreak" else " ")
        elif node.type == "code_inline":
            fragments.append("<tt>" + escape(node.content, quote=False) + "</tt>")
        elif node.type in INLINE_STYLES:
            tag = INLINE_STYLES[node.type]
            fragments.append(f"<{tag}>" + inline_markup(node.children) + f"</{tag}>")
        elif node.children:
            # Links and images expose only their visible label or alt text.
            fragments.append(inline_markup(node.children))
    return "".join(fragments)


def prose(content="", *, markup=None, style=None):
    widget = label(content, style)
    widget.set_selectable(True)
    if markup is not None:
        widget.set_markup(markup)
    return widget


def code_markup(code, language, dark):
    if not language or len(code) > 12000:
        return escape(code, quote=False)
    try:
        lexer = get_lexer_by_name(language, stripnl=False, ensurenl=False)
    except ClassNotFound:
        return escape(code, quote=False)
    fragments = []
    for kind, value in lex(code, lexer):
        text = escape(value, quote=False)
        color = next((colors[1 if dark else 2] for colors in TOKEN_COLORS if kind in colors[0]), None)
        fragments.append(f'<span foreground="{color}">{text}</span>' if color else text)
    return "".join(fragments)


def code_block(node, dark):
    block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    block.get_style_context().add_class("code-block")
    toolbar = Gtk.Box(spacing=8)
    toolbar.get_style_context().add_class("code-toolbar")
    language = node.info.split(maxsplit=1)[0][:32] if node.info.strip() else ""
    toolbar.pack_start(label(language or "Código"), True, True, 0)
    copy = Gtk.Button(label="Copiar código")

    def copy_code(*_args):
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(node.content, -1)
        copy.set_label("Copiado")

    copy.connect("clicked", copy_code)
    toolbar.pack_end(copy, False, False, 0)
    block.pack_start(toolbar, False, False, 0)
    snippet = prose(markup="<tt>" + code_markup(node.content.rstrip("\n"), language, dark) + "</tt>",
                    style="code-text")
    block.pack_start(snippet, False, False, 0)
    return block


def table(node):
    grid = Gtk.Grid(column_homogeneous=True)
    grid.get_style_context().add_class("message-table")
    for row_index, row in enumerate(row for section in node.children for row in section.children):
        for column, cell in enumerate(row.children):
            widget = prose(markup=inline_markup(cell.children),
                           style="table-heading" if cell.type == "th" else "table-cell")
            grid.attach(widget, column, row_index, 1, 1)
    return grid


def blocks(container, nodes, dark):
    for node in nodes:
        if node.type == "paragraph":
            child = prose(markup=inline_markup(node.children))
        elif node.type == "heading":
            child = prose(markup="<b>" + inline_markup(node.children) + "</b>", style="message-heading")
        elif node.type in ("fence", "code_block"):
            child = code_block(node, dark)
        elif node.type == "table":
            child = table(node)
        elif node.type in ("bullet_list", "ordered_list"):
            child = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            start = int(node.attrGet("start") or 1)
            for index, item in enumerate(node.children, start):
                row = Gtk.Box(spacing=10)
                bullet = Gtk.Label(label=f"{index}." if node.type == "ordered_list" else "•")
                bullet.set_valign(Gtk.Align.START)
                row.pack_start(bullet, False, False, 0)
                body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                blocks(body, item.children, dark)
                row.pack_start(body, True, True, 0)
                child.pack_start(row, False, False, 0)
        elif node.type == "blockquote":
            child = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            child.get_style_context().add_class("message-quote")
            blocks(child, node.children, dark)
        elif node.type == "hr":
            child = Gtk.Separator()
        else:
            continue
        container.pack_start(child, False, False, 0)


def render(container, content, role, dark):
    for child in container.get_children():
        child.destroy()
    tokens = MARKDOWN.parse(content) if role == "assistant" and len(content) <= 64000 else ()
    if tokens and len(tokens) <= 500:
        nodes = SyntaxTreeNode(tokens).children
        blocks(container, nodes, dark)
    else:
        for offset in range(0, max(1, len(content)), 8000):
            container.pack_start(prose(content[offset:offset + 8000]), False, False, 0)
    container.show_all()
