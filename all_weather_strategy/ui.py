"""Streamlit user interface layer."""

from datetime import datetime
import io

import streamlit as st

from .config import AppConfig
from .engine import AllWeatherEngine
from .reports import ReportGenerator


def render_app() -> None:
    """Render the Streamlit application."""
    st.set_page_config(page_title="全天候投资配置系统", layout="wide")

    st.sidebar.header("配置参数")
    default_etf_str = "\n".join(AppConfig.DEFAULT_ETF_LIST)
    etf_input = st.sidebar.text_area("ETF 标的池 (每行一个代码)", value=default_etf_str, height=200)
    etf_list = [s.strip() for s in etf_input.split("\n") if s.strip()]

    total_amount = st.sidebar.number_input(
        "拟配置总金额 (元)",
        min_value=AppConfig.MIN_CAPITAL,
        value=AppConfig.DEFAULT_CAPITAL,
        step=1000.0,
    )
    lookback_days = st.sidebar.slider(
        "回看时长 (天)",
        min_value=AppConfig.MIN_LOOKBACK_DAYS,
        max_value=AppConfig.MAX_LOOKBACK_DAYS,
        value=AppConfig.DEFAULT_LOOKBACK_DAYS,
    )

    st.title("全天候 ETF 资产配置系统")
    st.markdown("依据 **风险平价 (Risk Parity)** 原理，自动计算各大类资产 ETF 的配置权重。")

    if st.sidebar.button("开始计算"):
        if not etf_list:
            st.error("请输入至少一个 ETF 代码")
            return

        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_progress(progress, text):
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
            if "Rate limited" in str(exc) or "Too Many Requests" in str(exc):
                st.error("Yahoo Finance 触发了限流，请稍后再试，或减少频繁刷新。")
            else:
                st.error(f"计算失败：{exc}")
            return

        st.success("配置方案计算完成")

        m1, m2 = st.columns(2)
        ret = results["metrics"]["annualized_return"] * 100
        risk = results["metrics"]["annualized_risk"] * 100
        m1.metric("预估年化配置收益", f"{ret:.2f}%")
        m2.metric("配置组合年化风险 (波动率)", f"{risk:.2f}%")

        st.subheader("配置方案详情")
        st.table(results["result_df"])

        st.subheader("权重分布可视化")
        generator = ReportGenerator(total_amount)
        labels = [f"{results['etf_names'][code]}({code})" for code in results["result_df"]["ETF代码"]]
        wrapped_labels = [generator.wrap_text(label) for label in labels]
        fig = generator.create_pie_chart(results["weights"], wrapped_labels)
        st.pyplot(fig)

        st.subheader("报告导出")
        col1, col2 = st.columns(2)

        timestamp = datetime.now().strftime("%Y%m%d")
        csv_data = results["result_df"].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        col1.download_button(
            label="下载 CSV 方案",
            data=csv_data,
            file_name=f"AllWeather_Plan_{timestamp}.csv",
            mime="text/csv",
        )

        pdf_buffer = io.BytesIO()
        generator.generate_pdf(results["result_df"], results["weights"], results["etf_names"], buffer=pdf_buffer)
        col2.download_button(
            label="下载 PDF 报告",
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
