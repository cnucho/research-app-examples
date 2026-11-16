"""Build the printable Korean exercise handbook from the four public manuscripts.

Requires reportlab, fontTools and pypdf. Noto Sans CJK is embedded, not assumed
to exist on the reader's computer. CFF collection fonts are subset to the
manuscript and converted to TrueType outlines in an external temporary cache.
No data, manuscript, statistical choice or interpretation is changed here.

Example:
    python teaching/build_handbook.py --output /path/to/policy-effect-exercises-ko.pdf
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from html import escape
import json
from pathlib import Path
import re

from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont as SourceFont
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, HRFlowable, KeepTogether, LongTable,
    PageBreak, PageTemplate, Paragraph, Spacer, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


SOURCES = ("README_KO.md", "PRACTICE_PROBLEMS_KO.md", "SUBMISSION_TEMPLATE_KO.md", "OPTIONAL_TOOLS_KO.md")
PART_LABELS = ("이용 안내", "사례별 연습과제", "제출 양식과 평가기준", "선택 도구 안내")
TITLE = "정책효과 분석 연습과제"
SUBTITLE = "정책문제 · 가상데이터 · 분석과제 · 제출기준"
REGULAR = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BOLD = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
INK = colors.HexColor("#172C3D")
ACCENT = colors.HexColor("#2E6078")
MUTED = colors.HexColor("#526372")
RULE = colors.HexColor("#D8E1E7")
PALE = colors.HexColor("#F2F6F8")
PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
FRAME_TOP = 22 * mm
FRAME_BOTTOM = 20 * mm
BODY_W = PAGE_W - 2 * MARGIN_X
BODY_H = PAGE_H - FRAME_TOP - FRAME_BOTTOM
INLINE = re.compile(r"(`[^`]+`|\[[^\]]+\]\([^\s)]+\)|\*\*[^*]+\*\*|\*[^*\n]+\*|<br\s*/?>)")
LIST_ITEM = re.compile(r"^(\s*)([-+*]|\d+[.)])\s+(.+)$")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
NORMALIZE = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " "})


def normalize(text):
    return text.translate(NORMALIZE).replace("\r\n", "\n").replace("\r", "\n")


def visible_source(text):
    """HTML comments are non-rendered Markdown, not student instructions."""
    return re.sub(r"<!--[\s\S]*?-->", "", normalize(text))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def plain_inline(text):
    """Keep literal code characters while removing presentation delimiters."""
    output, cursor = [], 0
    for match in INLINE.finditer(text):
        output.append(text[cursor:match.start()])
        token = match.group()
        if token.startswith("`"):
            output.append(token[1:-1])
        elif token.startswith("**"):
            output.append(plain_inline(token[2:-2]))
        elif token.startswith("*"):
            output.append(plain_inline(token[1:-1]))
        elif token.startswith("<br"):
            output.append(" ")
        else:
            output.append(plain_inline(re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", token)[1]))
        cursor = match.end()
    return "".join(output) + text[cursor:]


def embedded_font(path, chars, cache, label, collection_index):
    font = SourceFont(path, fontNumber=collection_index if path.suffix.lower() == ".ttc" else 0)
    cmap = font.getBestCmap()
    wanted = {ord(char) for char in chars if not char.isspace()}
    missing = sorted(wanted - set(cmap))
    if missing:
        raise ValueError("Font lacks manuscript glyphs: " + ", ".join(f"U+{cp:04X} {chr(cp)!r}" for cp in missing))
    key = sha256(path.read_bytes() + "".join(sorted(chars)).encode() + b"handbook-font-v1")[:24]
    target = cache / f"{label}-{key}.ttf"
    if not target.exists():
        options = subset.Options()
        options.layout_features = []
        options.hinting = False
        options.notdef_glyph = options.notdef_outline = True
        options.recommended_glyphs = True
        options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14]
        job = subset.Subsetter(options=options)
        job.populate(unicodes=wanted | {32})
        job.subset(font)
        if "glyf" in font:
            font.recalcTimestamp = False
            font.save(target)
        else:
            order = font.getGlyphOrder()
            glyph_set = font.getGlyphSet()
            glyphs = {}
            for name in order:
                pen = TTGlyphPen(glyph_set)
                glyph_set[name].draw(Cu2QuPen(pen, max_err=0.8, reverse_direction=True))
                glyphs[name] = pen.glyph()
            builder = FontBuilder(font["head"].unitsPerEm, isTTF=True)
            builder.setupGlyphOrder(order)
            builder.setupCharacterMap(font.getBestCmap())
            builder.setupGlyf(glyphs)
            builder.setupHorizontalMetrics(font["hmtx"].metrics)
            builder.setupHorizontalHeader(ascent=font["hhea"].ascent, descent=font["hhea"].descent,
                                          lineGap=font["hhea"].lineGap)
            builder.setupNameTable({"familyName": "Policy Handbook Noto Sans", "styleName": label,
                                    "uniqueFontIdentifier": "PolicyHandbook-" + label + "-" + key,
                                    "fullName": "Policy Handbook Noto Sans " + label,
                                    "psName": "PolicyHandbook-" + label})
            os2 = font["OS/2"]
            builder.setupOS2(sTypoAscender=os2.sTypoAscender, sTypoDescender=os2.sTypoDescender,
                             sTypoLineGap=os2.sTypoLineGap, usWinAscent=os2.usWinAscent,
                             usWinDescent=os2.usWinDescent, usWeightClass=os2.usWeightClass,
                             fsType=0)
            builder.setupPost()
            builder.setupMaxp()
            # Preserve the embedded source font's copyright and licence names.
            builder.font["name"].names.extend(deepcopy(record) for record in font["name"].names
                                              if record.nameID in (0, 7, 8, 9, 13, 14))
            builder.font["head"].created = builder.font["head"].modified = 2082844800
            builder.font.recalcTimestamp = False
            builder.save(target)
    font.close()
    return target


def register_fonts(texts, regular, bold, cache, collection_index):
    fixed = TITLE + SUBTITLE + "".join(PART_LABELS) + "읽는 순서 링크 목록 합성자료 기반 학습 자료 여섯 정책 사례 열두 자료 세트 이 과제집은 도구의 선택과 관계없이 문제 정의부터 자료 준비 분석 검토 제출까지 활용한다 모든 관측값은 합성자료다 결과를 실제 정책의 성과로 인용하지 않는다 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,;:!?/()[]<>_-+*=#%&'\"·•→"
    chars = set(fixed + "".join(texts))
    files = [embedded_font(path, chars, cache, label, collection_index)
             for path, label in ((regular, "Regular"), (bold, "Bold"))]
    pdfmetrics.registerFont(TTFont("Handbook", str(files[0])))
    pdfmetrics.registerFont(TTFont("Handbook-Bold", str(files[1])))
    pdfmetrics.registerFontFamily("Handbook", normal="Handbook", bold="Handbook-Bold",
                                  italic="Handbook", boldItalic="Handbook-Bold")
    return {"regular": str(regular), "bold": str(bold), "collection_index": collection_index,
            "embedded_subset_sha256": [sha256(path.read_bytes()) for path in files]}


def styles():
    base = dict(fontName="Handbook", textColor=INK, wordWrap="CJK", splitLongWords=True,
                allowWidows=0, allowOrphans=0, alignment=TA_LEFT)
    return {
        "body": ParagraphStyle("body", fontSize=10.1, leading=16.1, rightIndent=6, spaceAfter=7, **base),
        "list": ParagraphStyle("list", fontSize=10.0, leading=15.7, leftIndent=12, firstLineIndent=-12, rightIndent=6, spaceAfter=5, **base),
        "h1": ParagraphStyle("h1", fontSize=23, leading=32, spaceAfter=17, keepWithNext=True, **{**base, "fontName": "Handbook-Bold"}),
        "h2": ParagraphStyle("h2", fontSize=15, leading=22, spaceBefore=17, spaceAfter=9, keepWithNext=True, **{**base, "fontName": "Handbook-Bold"}),
        "h3": ParagraphStyle("h3", fontSize=11.7, leading=18, spaceBefore=12, spaceAfter=6, keepWithNext=True, **{**base, "fontName": "Handbook-Bold"}),
        "cell": ParagraphStyle("cell", fontSize=8.5, leading=12.7, **base),
        "headcell": ParagraphStyle("headcell", fontSize=8.6, leading=12.7, **{**base, "fontName": "Handbook-Bold", "textColor": colors.white}),
        "quote": ParagraphStyle("quote", fontSize=9.6, leading=15.3, leftIndent=12, rightIndent=9,
                                  borderColor=RULE, borderWidth=.5, borderPadding=9, backColor=PALE,
                                  spaceBefore=6, spaceAfter=11, **base),
        "code": ParagraphStyle("code", fontSize=8.7, leading=13.1, leftIndent=9, rightIndent=9,
                                 borderPadding=8, backColor=PALE, spaceBefore=5, spaceAfter=10, **base),
        "small": ParagraphStyle("small", fontSize=8, leading=12, spaceAfter=6, **{**base, "textColor": MUTED}),
        "eyebrow": ParagraphStyle("eyebrow", fontSize=10, leading=16, spaceAfter=8, **{**base, "fontName": "Handbook-Bold", "textColor": ACCENT}),
    }


class Markdown:
    def __init__(self, style):
        self.style = style
        self.urls = []
        self.counts = Counter()

    def inline(self, text):
        output, cursor = [], 0
        for match in INLINE.finditer(text):
            output.append(escape(text[cursor:match.start()]))
            token = match.group()
            if token.startswith("`"):
                output.append('<font color="#304D60">' + escape(token[1:-1]) + "</font>")
            elif token.startswith("**"):
                output.append("<b>" + self.inline(token[2:-2]) + "</b>")
            elif token.startswith("*"):
                output.append("<i>" + self.inline(token[1:-1]) + "</i>")
            elif token.startswith("<br"):
                output.append("<br/>")
            else:
                link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", token)
                label, target = link.groups()
                if target.startswith(("https://", "http://")):
                    if target not in self.urls:
                        self.urls.append(target)
                    number = self.urls.index(target) + 1
                    output.append('<link href="' + escape(target, quote=True) + '" color="#2E6078">' + self.inline(label) + f" [{number}]</link>")
                elif target.split("#", 1)[0] in SOURCES:
                    key = "part-" + str(SOURCES.index(target.split("#", 1)[0]) + 1)
                    output.append('<link href="#' + key + '" color="#2E6078">' + self.inline(label) + "</link>")
                else:
                    output.append(self.inline(label) + " (" + escape(target) + ")")
            cursor = match.end()
        output.append(escape(text[cursor:]))
        return "".join(output)

    @staticmethod
    def cells(line):
        line = line.strip().strip("|")
        cells, current, quoted, escaped = [], [], False, False
        for char in line:
            if escaped:
                current.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "`":
                quoted = not quoted
                current.append(char)
            elif char == "|" and not quoted:
                cells.append("".join(current).strip())
                current = []
            else:
                current.append(char)
        if escaped:
            current.append("\\")
        return cells + ["".join(current).strip()]

    def table(self, lines):
        rows = [self.cells(line) for line in lines]
        if len(rows) < 2 or not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in rows[1]):
            raise ValueError("Malformed Markdown table: " + lines[0])
        del rows[1]
        width = len(rows[0])
        if not all(len(row) == width for row in rows):
            raise ValueError("Table row width differs from its header: " + lines[0])
        headers = " ".join(rows[0])
        if width == 3 and "CSV" in headers and "SAV" in headers:
            shares = [.455, .455, .09]
        elif width == 3 and "파일" in headers and ("변수" in headers or "자료형" in headers):
            shares = [.25, .19, .56]
        elif width == 3 and "경로" in headers:
            shares = [.39, .27, .34]
        elif width == 4 and "사례" in headers:
            shares = [.07, .25, .34, .34]
        elif width == 2:
            shares = [.32, .68]
        else:
            lengths = [max(len(re.sub(r"[`*]", "", row[i])) for row in rows) for i in range(width)]
            weights = [max(5, value) ** .55 for value in lengths]
            total = sum(weights)
            shares = [value / total for value in weights]
        content = []
        for index, row in enumerate(rows):
            rendered = []
            for cell in row:
                markup = self.inline(cell)
                if index == 0:
                    markup = re.sub(r'\bcolor="[^"]+"', 'color="#FFFFFF"', markup)
                rendered.append(Paragraph(markup, self.style["headcell" if index == 0 else "cell"]))
            content.append(rendered)
        table = LongTable(content, colWidths=[BODY_W * part for part in shares], repeatRows=1,
                          splitByRow=1, splitInRow=1, hAlign="LEFT", spaceBefore=5, spaceAfter=12)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), .65, INK),
            ("LINEBELOW", (0, 1), (-1, -1), .3, RULE),
        ]))
        self.counts["tables"] += 1
        self.counts["table_body_rows"] += len(rows) - 1
        return table

    def blocks(self, text, filename, part):
        lines = visible_source(text).splitlines()
        story = [Paragraph(f"{part:02d}  {PART_LABELS[part - 1]}", self.style["eyebrow"])]
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if not line:
                index += 1
                continue
            heading = HEADING.match(line)
            if heading:
                level, title = len(heading[1]), heading[2]
                if level == 2 and ((filename == SOURCES[1] and title.startswith("사례")) or title.startswith("부록")):
                    story.append(PageBreak())
                paragraph = Paragraph(self.inline(title), self.style["h1" if level == 1 else "h2" if level == 2 else "h3"])
                if level <= 2:
                    paragraph.bookmark = f"part-{part}" if level == 1 else f"part-{part}-line-{index}"
                    paragraph.outline_title = re.sub(r"[`*]", "", title)
                    paragraph.outline_level = 0 if level == 1 else 1
                    paragraph.include_toc = level == 1 or (filename == SOURCES[1] and title.startswith("사례")) or title.startswith("부록")
                story.append(paragraph)
                self.counts["headings"] += 1
                index += 1
                continue
            if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].strip().startswith("|"):
                end = index + 1
                while end < len(lines) and lines[end].strip().startswith("|"):
                    end += 1
                table = self.table(lines[index:end])
                if len(lines[index:end]) <= 8:
                    if story and isinstance(story[-1], Paragraph):
                        story[-1].keepWithNext = True
                    leading = []
                    while story and isinstance(story[-1], Paragraph) and story[-1].getKeepWithNext():
                        leading.insert(0, story.pop())
                    story.append(KeepTogether(leading + [table]))
                else:
                    story.append(table)
                index = end
                continue
            if line.startswith("```"):
                end = index + 1
                while end < len(lines) and not lines[end].strip().startswith("```"):
                    end += 1
                if end == len(lines):
                    raise ValueError("Unclosed code block in " + filename)
                code = "<br/>".join(escape(value).replace("  ", "&#160;&#160;") for value in lines[index + 1:end])
                story.append(Paragraph(code or "&#160;", self.style["code"]))
                index = end + 1
                continue
            if line.startswith(">"):
                end = index
                quoted = []
                while end < len(lines) and lines[end].lstrip().startswith(">"):
                    quoted.append(re.sub(r"^\s*>\s?", "", lines[end]))
                    end += 1
                story.append(Paragraph(self.inline(" ".join(quoted)), self.style["quote"]))
                index = end
                continue
            item = LIST_ITEM.match(lines[index])
            if item:
                marker = "•" if item[2] in ("-", "+", "*") else item[2]
                story.append(Paragraph(escape(marker) + "  " + self.inline(item[3]), self.style["list"]))
                index += 1
                continue
            if re.fullmatch(r"[-*_]{3,}", line):
                story.extend([Spacer(1, 5), HRFlowable(width="100%", thickness=.4, color=RULE), Spacer(1, 8)])
                index += 1
                continue
            end = index + 1
            while end < len(lines) and lines[end].strip() and not (
                    HEADING.match(lines[end].strip()) or LIST_ITEM.match(lines[end]) or
                    lines[end].lstrip().startswith(("|", ">", "```"))):
                end += 1
            paragraph = " ".join(value.strip() for value in lines[index:end])
            story.append(Paragraph(self.inline(paragraph), self.style["body"]))
            self.counts["paragraphs"] += 1
            index = end
        return story


class Cover(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = BODY_W, BODY_H - 2

    def draw(self):
        canvas = self.canv
        canvas.setFillColor(INK)
        canvas.rect(0, self.height - 5, self.width, 5, fill=1, stroke=0)
        canvas.setFont("Handbook", 10)
        canvas.setFillColor(ACCENT)
        canvas.drawString(0, self.height - 49, "합성자료 기반 학습 자료")
        canvas.setFillColor(INK)
        canvas.setFont("Handbook-Bold", 34)
        canvas.drawString(0, self.height - 112, "정책효과 분석")
        canvas.drawString(0, self.height - 160, "연습과제")
        canvas.setFont("Handbook", 13)
        canvas.drawString(0, self.height - 200, SUBTITLE)
        canvas.setStrokeColor(RULE)
        canvas.line(0, self.height - 236, self.width, self.height - 236)
        canvas.setFont("Handbook-Bold", 13)
        canvas.drawString(0, self.height - 275, "여섯 정책 사례 · 열두 자료 세트")
        note = Paragraph("이 과제집은 도구의 선택과 관계없이 문제 정의부터 자료 준비, 분석, 검토, 제출까지 활용한다.",
                         ParagraphStyle("cover-note", fontName="Handbook", fontSize=11, leading=19,
                                        textColor=MUTED, wordWrap="CJK"))
        _, height = note.wrap(self.width - 40, 80)
        note.drawOn(canvas, 0, self.height - 300 - height)
        for index, label in enumerate(PART_LABELS):
            y = 178 - index * 27
            canvas.setFont("Handbook-Bold", 10)
            canvas.setFillColor(ACCENT)
            canvas.drawString(0, y, f"{index + 1:02d}")
            canvas.setFont("Handbook", 11)
            canvas.setFillColor(INK)
            canvas.drawString(31, y, label)
        canvas.setFillColor(MUTED)
        canvas.setFont("Handbook", 8.2)
        canvas.drawString(0, 29, "모든 관측값은 합성자료다. 결과를 실제 정책의 성과로 인용하지 않는다.")


class Handbook(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(str(filename), pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                         topMargin=FRAME_TOP, bottomMargin=FRAME_BOTTOM,
                         title=TITLE, author="", subject=SUBTITLE, creator="Policy exercise handbook builder",
                         pageCompression=1, invariant=1, allowSplitting=True)
        frame = Frame(MARGIN_X, FRAME_BOTTOM, BODY_W, BODY_H, leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="handbook", frames=[frame], onPage=self.decorate))

    def decorate(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setFont("Handbook", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN_X, PAGE_H - 12 * mm, TITLE)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(.4)
        canvas.line(MARGIN_X, PAGE_H - 15 * mm, PAGE_W - MARGIN_X, PAGE_H - 15 * mm)
        canvas.drawString(MARGIN_X, 11 * mm, "합성자료 기반 학습 자료")
        canvas.setFont("Handbook-Bold", 8)
        canvas.drawRightString(PAGE_W - MARGIN_X, 11 * mm, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and hasattr(flowable, "bookmark"):
            self.canv.bookmarkPage(flowable.bookmark)
            self.canv.addOutlineEntry(flowable.outline_title, flowable.bookmark, flowable.outline_level, closed=False)
            if flowable.include_toc:
                self.notify("TOCEntry", (flowable.outline_level, flowable.outline_title, self.page, flowable.bookmark))


def build(source_dir, output, regular, bold, collection_index, prepare_only=False):
    raw = [(source_dir / filename).read_bytes() for filename in SOURCES]
    texts = [visible_source(value.decode("utf-8-sig")) for value in raw]
    output.parent.mkdir(parents=True, exist_ok=True)
    cache = output.parent / "tmp" / "pdfs" / "font-cache"
    cache.mkdir(parents=True, exist_ok=True)
    fonts = register_fonts(texts, regular, bold, cache, collection_index)
    if prepare_only:
        return {"prepared_fonts": fonts}
    style = styles()
    markdown = Markdown(style)
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc0", fontName="Handbook-Bold", fontSize=11, leading=19,
                                      spaceBefore=10, leftIndent=0, rightIndent=20, textColor=INK),
                       ParagraphStyle("toc1", fontName="Handbook", fontSize=9.5, leading=16,
                                      spaceBefore=3, leftIndent=14, rightIndent=20, textColor=MUTED)]
    story = [Cover(), PageBreak(), Paragraph("읽는 순서", style["h1"]), toc]
    for part, (filename, text) in enumerate(zip(SOURCES, texts), 1):
        story.append(PageBreak())
        story.extend(markdown.blocks(text, filename, part))
    if markdown.urls:
        story.append(Paragraph("링크 목록", style["h2"]))
        for number, url in enumerate(markdown.urls, 1):
            story.append(Paragraph(f"<b>[{number}]</b> " + '<link href="' + escape(url, quote=True) + '">' + escape(url) + "</link>", style["small"]))
    Handbook(output).multiBuild(story)
    reader = PdfReader(output)
    page_text = [page.extract_text() or "" for page in reader.pages]
    all_text = "\n".join(page_text)
    if "\ufffd" in all_text or any(not value.strip() for value in page_text):
        raise ValueError("PDF contains a replacement glyph or an empty page")
    # Check every source line/table cell in the PDF reading stream. Remove only
    # running furniture and generated link numbers, retaining manuscript text.
    content = "\n".join(re.sub(r"^" + re.escape(TITLE) + r"\n합성자료 기반 학습 자료\n\d+\n", "", value)
                        for value in page_text)
    compact = re.sub(r"\s+", "", re.sub(r"\[\d+\]", "", content))
    checked, missing = 0, []
    for filename, text in zip(SOURCES, texts):
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip() or re.fullmatch(r"\s*[|:\- ]+\s*", line) or line.strip().startswith("```"):
                continue
            cells = Markdown.cells(line) if line.strip().startswith("|") else [line]
            for cell in cells:
                plain = re.sub(r"^\s*(?:#{1,6}\s+|>\s*|[-+*]\s+|\d+[.)]\s+)", "", cell)
                plain = plain_inline(plain)
                needle = re.sub(r"\s+", "", plain)
                if needle:
                    checked += 1
                    if needle not in compact:
                        missing.append({"file": filename, "line": number, "text": plain[:120]})
    if missing:
        raise ValueError("Source text not located in PDF: " + json.dumps(missing, ensure_ascii=False))
    if any((source_dir / filename).read_bytes() != value for filename, value in zip(SOURCES, raw)):
        raise RuntimeError("A manuscript changed during PDF generation; rebuild the final snapshot")
    report = {"output": output.name, "sha256": sha256(output.read_bytes()), "bytes": output.stat().st_size,
              "pages": len(reader.pages), "source_order": list(SOURCES),
              "sources": [{"file": name, "sha256": sha256(value), "bytes": len(value)} for name, value in zip(SOURCES, raw)],
              "fonts": fonts, "parsed_blocks": dict(markdown.counts),
              "external_links": len(markdown.urls), "page_text_characters": [len(value) for value in page_text],
              "source_text_checks": {"checked": checked, "missing": len(missing)},
              "replacement_characters": all_text.count("\ufffd"), "visual_qa_required": True,
              "content_policy": "All manuscript paragraphs, list items, code blocks and table cells are retained; Markdown comments are non-rendered. Unicode dashes are normalized to ASCII hyphens."}
    output.with_suffix(".qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--font-regular", type=Path, default=REGULAR)
    parser.add_argument("--font-bold", type=Path, default=BOLD)
    parser.add_argument("--font-index", type=int, default=1, help="Noto CJK collection index 1 is Korean")
    parser.add_argument("--prepare-fonts-only", action="store_true")
    args = parser.parse_args()
    report = build(args.source_dir, args.output, args.font_regular, args.font_bold, args.font_index, args.prepare_fonts_only)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
