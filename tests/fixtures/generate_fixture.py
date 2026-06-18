"""Regenerate the synthetic MWRA-style PDF used by parser tests."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT = Path(__file__).with_name("mwra-report.pdf")


def build() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=landscape(letter),
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28,
    )
    styles = getSampleStyleSheet()
    rows = [
        [
            "Component",
            "Brutsch Water Treatment Facility (Raw)",
            "Ludlow Monitoring Station (Treated)",
            "Carroll Water Treatment Plant Inlet (Raw)",
            "Carroll Water TP Fin. Water Tap (Treated)",
            "Units",
        ],
        ["Alkalinity (3)", "4.0", "5.0", "6.9", "40.3", "MG/L"],
        ["Calcium", "2150", "2190", "4340", "4370", "UG/L"],
        ["Chloride", "7.6", "8.9", "24.4", "27.3", "MG/L"],
        ["Magnesium", "512", "501", "853", "845", "UG/L"],
        ["pH (3)", "6.8", "7.1", "7.3", "9.7", "S.U."],
        ["Sodium", "5.91", "7", "16.7", "34", "MG/L"],
        ["Sulfate (SO4)", "3.5", "3.6", "5.1", "5.6", "MG/L"],
        ["Hardness (2)", "7.5", "7.5", "14.3", "14.4", "MG/L"],
        ["Fluoride", "U", "U", "U", "0.72", "MG/L"],
        ["Potassium", "562", "605", "942", "935", "UG/L"],
    ]
    table = Table(rows, colWidths=[120, 125, 125, 125, 145, 50], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEEF2")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#68858D")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story = [
        Paragraph("MWRA Monthly Water Quality Analysis", styles["Title"]),
        Paragraph("April 2026", styles["Heading2"]),
        Spacer(1, 12),
        table,
    ]
    doc.build(story)


if __name__ == "__main__":
    build()
