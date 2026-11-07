"""Group test export: one readable CSV and one formatted Excel file.

Both files are built from the same plain table (``build_table``), so they always
contain the same numbers.  The module does not touch the database itself; the
caller in ``group.py`` passes in already loaded objects.
"""

import csv
from datetime import datetime

# Slovak/Czech Excel uses ";" as the list separator.  With "," every row ended
# up in column A; with ";" each value gets its own column after a double click.
CSV_DELIMITER = ";"
NA = "n/a"

# Colours of the web app (static/style.css)
NAVY = "1D3364"
BLUE = "3660BA"
LIGHT_BLUE = "D1DEE8"
LIGHT_GREY = "F7F7F7"
BORDER = "BFC9D6"

# Background of a vote cell: 5 is the best grade on both scales (EXCELLENT /
# IMPERCEPTIBLE), 1 the worst.
VOTE_FILLS = {5: "C6EFCE", 4: "E2F0D9", 3: "FFF2CC", 2: "FCE4D6", 1: "F8CBAD"}


def _glasses(tester):
    if tester.glasses is None:
        return NA
    return "ano" if tester.glasses else "nie"


def _label(tester):
    return tester.name or f"Tester {tester.seat}"


def build_table(session, testers, videos, votes, scale_labels, exported=None):
    """Return everything both files need as plain Python values.

    ``videos`` is the list of Video rows in export order and ``votes`` maps
    ``(id_tester, id_video) -> value``.
    """
    exported = exported or datetime.now()
    return {
        "session": session.name,
        "method": (session.test_method or "").upper(),
        "display": session.display or "",
        "exported": exported.strftime("%d.%m.%Y %H:%M"),
        "seats": [f"Tester {tester.seat}" for tester in testers],
        "names": [_label(tester) for tester in testers],
        "ages": [tester.age if tester.age is not None else NA for tester in testers],
        "glasses": [_glasses(tester) for tester in testers],
        "rows": [
            (video.name, [votes.get((tester.id, video.id), NA) for tester in testers])
            for video in videos
        ],
        # 5 first: labels[0] belongs to grade 5 (see group_vote.html)
        "scale": [(5 - index, label) for index, label in enumerate(scale_labels)],
    }


def write_csv(table, path):
    """Readable CSV: info block, tester block, one row per video."""
    # utf-8-sig adds a BOM so Excel shows names with diacritics correctly
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=CSV_DELIMITER)
        writer.writerow(["Session", table["session"]])
        writer.writerow(["Method", table["method"]])
        writer.writerow(["Display", table["display"]])
        writer.writerow(["Exported", table["exported"]])
        writer.writerow([])
        writer.writerow(["Tester"] + table["seats"])
        writer.writerow(["Name"] + table["names"])
        writer.writerow(["Age"] + table["ages"])
        writer.writerow(["Glasses"] + table["glasses"])
        writer.writerow([])
        writer.writerow(["Video"] + table["names"])
        for video, values in table["rows"]:
            writer.writerow([video] + values)


def write_xlsx(table, path):
    """Formatted Excel file in the colours of the app."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    def fill(color):
        return PatternFill("solid", start_color=color, end_color=color)

    thin = Side(style="thin", color=BORDER)
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")

    count = len(table["names"])
    last_col = max(count + 1, 2)

    book = Workbook()
    sheet = book.active
    sheet.title = "Results"
    sheet.sheet_view.showGridLines = False

    # --- title ---
    sheet.cell(row=1, column=1, value=table["session"])
    sheet.cell(row=1, column=1).font = Font(bold=True, size=16, color="FFFFFF")
    sheet.cell(row=1, column=1).alignment = left
    for col in range(1, last_col + 1):
        sheet.cell(row=1, column=col).fill = fill(NAVY)
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    sheet.row_dimensions[1].height = 30

    # --- info block ---
    info = [("Method", table["method"]), ("Display", table["display"]),
            ("Exported", table["exported"]), ("Testers", count)]
    row = 3
    for label, value in info:
        key = sheet.cell(row=row, column=1, value=label)
        key.font = Font(bold=True, color=NAVY)
        key.fill = fill(LIGHT_BLUE)
        key.border = box
        cell = sheet.cell(row=row, column=2, value=value)
        cell.border = box
        cell.alignment = left
        row += 1

    # --- tester block ---
    row += 1
    tester_row = row
    header = sheet.cell(row=row, column=1, value="Video")
    for col, name in enumerate(table["names"], start=2):
        sheet.cell(row=row, column=col, value=name)
    for col in range(1, count + 2):
        cell = sheet.cell(row=row, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill(NAVY)
        cell.alignment = center if col > 1 else left
        cell.border = box
    header.alignment = left
    row += 1

    for label, values in (("Seat", table["seats"]), ("Age", table["ages"]),
                          ("Glasses", table["glasses"])):
        key = sheet.cell(row=row, column=1, value=label)
        key.font = Font(bold=True, color=NAVY)
        key.fill = fill(LIGHT_BLUE)
        key.border = box
        for col, value in enumerate(values, start=2):
            cell = sheet.cell(row=row, column=col, value=value)
            cell.fill = fill(LIGHT_BLUE)
            cell.alignment = center
            cell.border = box
            if value == NA:
                cell.font = Font(italic=True, color="808080")
        row += 1

    # --- votes ---
    first_vote_row = row
    for index, (video, values) in enumerate(table["rows"]):
        stripe = fill(LIGHT_GREY) if index % 2 else fill("FFFFFF")
        name = sheet.cell(row=row, column=1, value=video)
        name.fill = stripe
        name.border = box
        name.alignment = left
        for col, value in enumerate(values, start=2):
            cell = sheet.cell(row=row, column=col, value=value)
            cell.alignment = center
            cell.border = box
            if value == NA:
                cell.fill = stripe
                cell.font = Font(italic=True, color="A0A0A0")
            else:
                cell.fill = fill(VOTE_FILLS.get(value, "FFFFFF"))
                cell.font = Font(bold=True)
        row += 1
    if not table["rows"]:
        sheet.cell(row=row, column=1, value="No votes yet").font = Font(italic=True,
                                                                        color="808080")
        row += 1

    # --- legend ---
    row += 1
    title = sheet.cell(row=row, column=1, value="Scale")
    title.font = Font(bold=True, color="FFFFFF")
    title.fill = fill(BLUE)
    title.border = box
    row += 1
    for value, label in table["scale"]:
        number = sheet.cell(row=row, column=1, value=value)
        number.fill = fill(VOTE_FILLS[value])
        number.font = Font(bold=True)
        number.alignment = center
        number.border = box
        text = sheet.cell(row=row, column=2, value=label)
        text.border = box
        sheet.merge_cells(start_row=row, start_column=2, end_row=row,
                          end_column=max(last_col, 3))
        row += 1

    # --- sizes, freeze, print ---
    longest = max([len(str(video)) for video, _ in table["rows"]]
                  + [len("Exported"), 12])
    sheet.column_dimensions["A"].width = min(longest + 3, 60)
    for col, name in enumerate(table["names"], start=2):
        width = max(len(str(name)), len(table["display"]) if col == 2 else 0, 10)
        sheet.column_dimensions[get_column_letter(col)].width = min(width + 3, 40)
    if count == 0:
        sheet.column_dimensions["B"].width = max(len(table["display"]) + 3, 20)
    sheet.freeze_panes = sheet.cell(row=first_vote_row, column=2)
    sheet.print_title_rows = f"{tester_row}:{tester_row}"
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True

    book.save(path)
