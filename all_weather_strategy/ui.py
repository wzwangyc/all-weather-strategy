"""Streamlit user interface layer."""

from datetime import datetime
import io

import streamlit as st

from .config import AppConfig
from .engine import AllWeatherEngine
from .reports import ReportGenerator


PAGE_TITLE = "All Weather Strategy"
APP_TITLE = "All Weather Strategy ETF Allocation"
APP_SUBTITLE = (
    "Allocate capital across a multi-asset ETF basket using a deterministic risk-parity model. "
    "Live historical prices are fetched from Yahoo Finance at runtime."
)

SIDEBAR_TITLE = "Parameters"
DEFAULT_ETF_LABEL = "ETF tickers (one per line)"
CAPITAL_LABEL = "Total capital (CNY)"
LOOKBACK_LABEL = "Lookback window (days)"
START_LABEL = "Run allocation"

METRIC_RETURN = "Estimated annualized return"
METRIC_RISK = "Estimated annualized risk"
SECTION_DETAILS = "Allocation Details"
SECTION_CHART = "Weight Distribution"
SECTION_EXPORT = "Export Reports"
CSV_BUTTON = "Download CSV"
PDF_BUTTON = "Download PDF"


def render_app() -> None:
    """Render the Streamlit application."""
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")

    st.sidebar.header(SIDEBAR_TITLE)
    default_etf_str = "\n".join(AppConfig.DEFAULT_ETF_LIST)
    etf_input = st.sidebar.text_area(DEFAULT_ETF_LABEL, value=default_etf_str, height=200)
    etf_list = [s.strip() for s in etf_input.split("\n") if s.strip()]

    total_amount = st.sidebar.number_input(
        CAPITAL_LABEL,
        min_value=AppConfig.MIN_CAPITAL,
        value=AppConfig.DEFAULT_CAPITAL,
        step=1000.0,
    )
    lookback_days = st.sidebar.slider(
        LOOKBACK_LABEL,
        min_value=AppConfig.MIN_LOOKBACK_DAYS,
        max_value=AppConfig.MAX_LOOKBACK_DAYS,
        value=AppConfig.DEFAULT_LOOKBACK_DAYS,
    )

    st.title(APP_TITLE)
    st.markdown(APP_SUBTITLE)

    if st.sidebar.button(START_LABEL):
        if not etf_list:
            st.error("Please enter at least one ETF ticker.")
            return

        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_progress(progress: float, text: str) -> None:
            progress_bar.progress(float(progress))
            status_text.text(text)

        engine = AllWeatherEngine(etf_list)
        try:
            results = engine.run(
                total_amount=total_amount,
                lookback_days=lookback_days,
                progress_callback=update_progress,
            )
        except Exception as exc:
            progress_bar.empty()
            status_text.empty()
            message = str(exc)
            if "Rate limited" in message or "Too Many Requests" in message:
                st.error("Yahoo Finance rate limit reached. Please try again later.")
            else:
                st.error(f"Calculation failed: {exc}")
            return

        st.success("Allocation completed")

        m1, m2 = st.columns(2)
        ret = results["metrics"]["annualized_return"] * 100
        risk = results["metrics"]["annualized_risk"] * 100
        m1.metric(METRIC_RETURN, f"{ret:.2f}%")
        m2.metric(METRIC_RISK, f"{risk:.2f}%")

        st.subheader(SECTION_DETAILS)
        st.dataframe(results["result_df"], use_container_width=True)

        st.subheader(SECTION_CHART)
        generator = ReportGenerator(total_amount)
        labels = [f"{results['etf_names'][code]} ({code})" for code in results["result_df"]["ETF_CODE"]]
        wrapped_labels = [generator.wrap_text(label) for label in labels]
        fig = generator.create_pie_chart(results["weights"], wrapped_labels)
        st.pyplot(fig)

        st.subheader(SECTION_EXPORT)
        col1, col2 = st.columns(2)

        timestamp = datetime.now().strftime("%Y%m%d")
        csv_data = results["result_df"].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        col1.download_button(
            label=CSV_BUTTON,
            data=csv_data,
            file_name=f"AllWeather_Plan_{timestamp}.csv",
            mime="text/csv",
        )

        pdf_buffer = io.BytesIO()
        generator.generate_pdf(results["result_df"], results["weights"], results["etf_names"], buffer=pdf_buffer)
        col2.download_button(
            label=PDF_BUTTON,
            data=pdf_buffer.getvalue(),
            file_name=f"AllWeather_Report_{timestamp}.pdf",
            mime="application/pdf",
        )

    st.markdown(
        """
        <style>
            .stMetric {
                background-color: #f0f2f6;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
