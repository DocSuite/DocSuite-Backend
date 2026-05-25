import re
from io import BytesIO

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

_PRIMARY = RGBColor(0x1F, 0x49, 0x7D)
_GRAY = RGBColor(0x70, 0x70, 0x70)
_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_HEADER_BG = "1F497D"
_ALT_ROW_BG = "EBF0FA"

_SEP_ROW_RE = re.compile(r"^\|[\s\-:|]+\|$")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")
_INLINE_RE = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*|([^*]+)")


def _parse_row(row: str) -> list[str]:
    parts = row.split("|")
    return [c.strip() for c in parts[1:-1]]


def _set_cell_bg(cell, hex_color: str) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tc_pr.append(shd)


def _add_run_formatted(para, text: str) -> None:
    for m in _INLINE_RE.finditer(text):
        if m.group(1):
            run = para.add_run(m.group(1))
            run.bold = True
        elif m.group(2):
            run = para.add_run(m.group(2))
            run.italic = True
        elif m.group(3):
            para.add_run(m.group(3))


def _add_hr(doc: Document) -> None:
    para = doc.add_paragraph()
    p_pr = para._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1F497D")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def _render_table(doc: Document, raw_lines: list[str]) -> None:
    header: list[str] | None = None
    data_rows: list[list[str]] = []

    for line in raw_lines:
        if _SEP_ROW_RE.match(line):
            continue
        cells = _parse_row(line)
        if header is None:
            header = cells
        else:
            data_rows.append(cells)

    if not header:
        return

    col_count = len(header)
    table = doc.add_table(rows=1, cols=col_count)
    table.style = "Table Grid"

    hdr_cells = table.rows[0].cells
    for j, text in enumerate(header):
        cell = hdr_cells[j]
        cell.paragraphs[0].clear()
        run = cell.paragraphs[0].add_run(text)
        run.bold = True
        run.font.color.rgb = _WHITE
        run.font.size = Pt(9)
        _set_cell_bg(cell, _HEADER_BG)

    for row_idx, row_data in enumerate(data_rows):
        row = table.add_row()
        for j in range(col_count):
            cell = row.cells[j]
            text = row_data[j] if j < len(row_data) else ""
            cell.paragraphs[0].clear()
            _add_run_formatted(cell.paragraphs[0], text)
            cell.paragraphs[0].runs[0].font.size = Pt(9) if cell.paragraphs[0].runs else None
            if row_idx % 2 == 1:
                _set_cell_bg(cell, _ALT_ROW_BG)

    doc.add_paragraph()


def markdown_to_docx(content: str, filename: str = "acta") -> BytesIO:
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.5)

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if not s:
            i += 1
            continue

        if s.startswith("### "):
            h = doc.add_heading(s[4:].strip(), level=3)
            for run in h.runs:
                run.font.color.rgb = _PRIMARY
            i += 1

        elif s.startswith("## "):
            h = doc.add_heading(s[3:].strip(), level=2)
            for run in h.runs:
                run.font.color.rgb = _PRIMARY
            i += 1

        elif s.startswith("# "):
            h = doc.add_heading(s[2:].strip(), level=1)
            for run in h.runs:
                run.font.color.rgb = _PRIMARY
            i += 1

        elif s == "---":
            _add_hr(doc)
            i += 1

        elif s.startswith("|"):
            block: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            _render_table(doc, block)

        elif s.startswith("- [ ]") or s.startswith("- [x]") or s.startswith("- [X]"):
            checked = s[3].lower() == "x"
            text = s[6:].strip()
            symbol = "☑" if checked else "☐"
            para = doc.add_paragraph(style="List Bullet")
            run = para.add_run(f"{symbol}  {text}")
            run.font.size = Pt(10)
            i += 1

        elif s.startswith("- "):
            para = doc.add_paragraph(style="List Bullet")
            _add_run_formatted(para, s[2:].strip())
            i += 1

        elif _NUMBERED_RE.match(s):
            text = _NUMBERED_RE.sub("", s)
            para = doc.add_paragraph(style="List Number")
            _add_run_formatted(para, text)
            i += 1

        elif s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            para = doc.add_paragraph()
            run = para.add_run(s[1:-1])
            run.italic = True
            run.font.color.rgb = _GRAY
            run.font.size = Pt(9)
            i += 1

        else:
            para = doc.add_paragraph()
            _add_run_formatted(para, s)
            i += 1

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
