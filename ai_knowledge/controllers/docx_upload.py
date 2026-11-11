# -*- coding: utf-8 -*-
"""
HTTP controller for uploading a .docx or .xlsx file and creating a Knowledge article.

POST /knowledge/upload_docx
  multipart/form-data fields:
    file          – the .docx or .xlsx binary
    parent_id     – id of the Workspace article to nest under
                    (empty string = root of Workspace)

Returns JSON:
  { "success": true,  "article_id": <int>, "title": "<str>" }
  { "success": false, "error": "<str>" }

Conversion:
  .docx  → mammoth  (pip install mammoth)
  .xlsx  → openpyxl (pip install openpyxl)  — each sheet becomes a section
"""

import base64
import html
import io
import json
import logging
import re

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# ── optional dependency guards ────────────────────────────────────────────────

try:
    import mammoth as _mammoth
    _MAMMOTH_OK = True
except ImportError:
    _mammoth = None
    _MAMMOTH_OK = False

try:
    import openpyxl as _openpyxl
    _OPENPYXL_OK = True
except ImportError:
    _openpyxl = None
    _OPENPYXL_OK = False


# ── converters ────────────────────────────────────────────────────────────────

def _docx_to_html(file_bytes: bytes, title: str) -> str:
    """Convert a .docx binary to HTML using mammoth.

    Images are embedded as base64 data-URIs.
    """
    if not _MAMMOTH_OK:
        raise RuntimeError(
            "'mammoth' is not installed on the server. "
            "Run: pip install mammoth"
        )

    def inline_image(image):
        with image.open() as f:
            data = base64.b64encode(f.read()).decode()
        mime = image.content_type or "image/png"
        return {"src": f"data:{mime};base64,{data}"}

    result = _mammoth.convert_to_html(
        io.BytesIO(file_bytes),
        convert_image=_mammoth.images.img_element(inline_image),
    )
    inner_html = result.value or ""
    return (
        f'<div class="odoo-editor-editable">'
        f'<h1>{html.escape(title)}</h1>'
        f'{inner_html}'
        f'</div>'
    )


def _xlsx_to_html(file_bytes: bytes, title: str) -> str:
    """Convert a .xlsx binary to HTML using openpyxl.

    Each worksheet becomes an <h2> section with an HTML table.
    Merged cells are preserved by repeating the value across the span.
    """
    if not _OPENPYXL_OK:
        raise RuntimeError(
            "'openpyxl' is not installed on the server. "
            "Run: pip install openpyxl"
        )

    wb = _openpyxl.load_workbook(
        io.BytesIO(file_bytes),
        read_only=False,
        data_only=True,
    )

    sections = []
    for ws in wb.worksheets:
        # Build a grid resolving merged cells
        grid = {}
        for merge in ws.merged_cells.ranges:
            top_left_val = ws.cell(merge.min_row, merge.min_col).value
            for row in range(merge.min_row, merge.max_row + 1):
                for col in range(merge.min_col, merge.max_col + 1):
                    grid[(row, col)] = top_left_val

        rows_html = []
        for row in ws.iter_rows():
            cells_html = []
            for cell in row:
                val = grid.get((cell.row, cell.column), cell.value)
                if val is None:
                    val = ""
                safe = html.escape(str(val))
                cells_html.append(f"<td>{safe}</td>")
            rows_html.append(f"<tr>{''.join(cells_html)}</tr>")

        if not rows_html:
            continue

        sheet_name = html.escape(ws.title)
        table = (
            f'<table class="table table-bordered table-sm" style="border-collapse:collapse">'
            f'<tbody>{"".join(rows_html)}</tbody>'
            f'</table>'
        )
        sections.append(f'<h2>{sheet_name}</h2>{table}')

    body = (
        f'<div class="odoo-editor-editable">'
        f'<h1>{html.escape(title)}</h1>'
        f'{"".join(sections) or "<p>(empty spreadsheet)</p>"}'
        f'</div>'
    )
    return body


# ── controller ────────────────────────────────────────────────────────────────

_ALLOWED_EXTS = {'.docx', '.xlsx'}


class KnowledgeDocxUploadController(http.Controller):

    @http.route(
        '/knowledge/upload_docx',
        type='http',
        auth='user',  # pragma: allowlist secret
        methods=['POST'],
        csrf=False,
    )
    def upload_docx(self, file=None, parent_id='', **kwargs):
        """Receive a .docx or .xlsx upload and create a Knowledge article."""
        env = request.env

        # ── validate input ────────────────────────────────────────────────
        if file is None or not getattr(file, 'filename', None):
            return _json_error("No file received.")

        filename = file.filename or ''
        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in _ALLOWED_EXTS:
            return _json_error(
                f"Unsupported file type '{ext}'. "
                "Please upload a .docx or .xlsx file."
            )

        file_bytes = file.read()
        if not file_bytes:
            return _json_error("The uploaded file is empty.")

        # Article title = filename without extension
        title = re.sub(r'\.[^.]+$', '', filename).strip() or filename

        # ── convert → HTML ───────────────────────────────────────────────
        try:
            if ext == '.docx':
                body_html = _docx_to_html(file_bytes, title)
            else:
                body_html = _xlsx_to_html(file_bytes, title)
        except Exception as exc:
            _logger.exception("File conversion failed for %s", filename)
            return _json_error(f"Conversion error: {exc}")

        # ── resolve parent article ────────────────────────────────────────
        parent_rec = env['knowledge.article']
        parent_id = str(parent_id or '').strip()
        if parent_id:
            if not parent_id.isdigit():
                return _json_error("Invalid parent article.")
            # Checked with the user's own rights: the creation below runs as sudo.
            parent_rec = env['knowledge.article'].browse(int(parent_id)).exists()
            if (
                not parent_rec
                or parent_rec.is_template
                or not parent_rec.has_access('write')
            ):
                return _json_error("Parent article not found. Please select another one.")
        parent_id = parent_rec.id

        # ── create article ────────────────────────────────────────────────
        try:
            vals = {'name': title, 'body': body_html, 'full_width': True}
            if parent_id:
                vals['parent_id'] = parent_id
            else:
                # Root Workspace article: same values as Knowledge's own
                # `article_create`. Without them the article is visible to its
                # members only (and the creator is not even a member).
                vals.update({
                    'internal_permission': 'write',
                    'is_article_visible_by_everyone': True,
                    'article_member_ids': [(0, 0, {
                        'partner_id': env.user.partner_id.id,
                        'permission': 'write',
                    })],
                })

            article = env['knowledge.article'].sudo().create(vals)
            _logger.info(
                "Knowledge article '%s' (id=%s) created from %s upload by uid=%s",
                title, article.id, ext, env.uid,
            )
        except Exception as exc:
            _logger.exception("Failed to create Knowledge article from upload")
            return _json_error(f"Could not create article: {exc}")

        return _json_ok({"article_id": article.id, "title": title})


# ── helpers ───────────────────────────────────────────────────────────────────

def _json_ok(data: dict) -> Response:
    payload = {"success": True, **data}
    return Response(json.dumps(payload), content_type='application/json', status=200)


def _json_error(message: str) -> Response:
    payload = {"success": False, "error": message}
    return Response(json.dumps(payload), content_type='application/json', status=200)
