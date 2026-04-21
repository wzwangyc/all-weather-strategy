"""Report generation helpers.

CSV and PDF output is kept inside the repository so the demo can be reproduced
without external services.
"""

import io
from decimal import Decimal
from typing import Dict, Union

import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .paths import FONT_PATH


def _register_font():
    """Register the bundled Chinese font and return a FontProperties handle."""
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Font file not found: {FONT_PATH}")
    font_manager.fontManager.addfont(str(FONT_PATH))
    pdfmetrics.registerFont(TTFont("SimHei", str(FONT_PATH)))
    return font_manager.FontProperties(fname=str(FONT_PATH))


class ReportGenerator:
    """Create tabular and chart-based output artifacts."""

    def __init__(self, total_amount: Union[Decimal, float]):
        self.total_amount = Decimal(str(total_amount))
        self.font_prop = _register_font()
        self.font_name = self.font_prop.get_name()
        self.styles = getSampleStyleSheet()

    @staticmethod
    def wrap_text(text: str, max_len: int = 10) -> str:
        """Wrap long labels for chart readability."""
        if len(text) <= max_len:
            return text
        return "\n".join(text[i : i + max_len] for i in range(0, len(text), max_len))

    def generate_csv(self, df: pd.DataFrame, path: str) -> None:
        """Write the result table to CSV."""
        df.to_csv(path, index=False, encoding="utf-8-sig")

    def create_pie_chart(self, weights, labels):
        """Build the allocation pie chart used in the UI and PDF."""
        fig = plt.figure(figsize=(10, 7))
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [self.font_name, "Microsoft YaHei", "DejaVu Sans", "sans-serif"]
        plt.rcParams["axes.unicode_minus"] = False
        explode = [0.05] * len(labels)
        plt.pie(
            weights,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            explode=explode,
            textprops={"fontsize": 10, "fontproperties": self.font_prop},
            wedgeprops={"edgecolor": "white", "linewidth": 1},
        )
        plt.title(
            f"ETF权重分布（总金额：{self.total_amount:.2f}元）",
            fontsize=14,
            pad=25,
            fontproperties=self.font_prop,
        )
        plt.axis("equal")
        plt.tight_layout()
        return fig

    def generate_pdf(self, result_df: pd.DataFrame, weights, etf_names: Dict[str, str], output_path: str = None, buffer: io.BytesIO = None) -> None:
        """Write a PDF report with the result table and allocation chart."""
        if buffer is None and output_path is None:
            raise ValueError("Either output_path or buffer must be provided.")

        doc = SimpleDocTemplate(
            output_path if output_path else buffer,
            pagesize=A4,
            rightMargin=inch / 2,
            leftMargin=inch / 2,
            topMargin=inch / 2,
            bottomMargin=inch / 2,
        )

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Title"],
            fontName=self.font_name,
            fontSize=18,
            alignment=1,
        )
        section_style = ParagraphStyle(
            "CustomHeading2",
            parent=self.styles["Heading2"],
            fontName=self.font_name,
            fontSize=12,
            spaceAfter=10,
        )

        story = []
        story.append(Paragraph(f"ETF全天候配置报告（总金额：{self.total_amount:.2f}元）", title_style))
        story.append(Spacer(1, 12))

        table_data = [result_df.columns.tolist()] + result_df.values.tolist()
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(Paragraph("配置方案详情", section_style))
        story.append(table)
        story.append(Spacer(1, 20))

        sorted_pairs = sorted(
            zip(weights, [self.wrap_text(f"{etf_names[code]}({code})") for code in result_df["ETF代码"]]),
            key=lambda item: item[0],
            reverse=True,
        )
        sorted_weights = [pair[0] for pair in sorted_pairs]
        sorted_labels = [pair[1] for pair in sorted_pairs]

        fig = self.create_pie_chart(sorted_weights, sorted_labels)
        image_buffer = io.BytesIO()
        fig.savefig(image_buffer, format="PNG", dpi=150, bbox_inches="tight")
        image_buffer.seek(0)
        plt.close(fig)
        story.append(Paragraph("权重分布可视化", section_style))
        story.append(Image(image_buffer, width=6 * inch, height=4 * inch))

        doc.build(story)
