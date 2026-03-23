import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="DCF Valuation Modeling",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
    .main {
        background-color: #f7f8fa;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }

    h1, h2, h3 {
        color: #2f6bd8;
        font-weight: 700;
    }

    .author-text {
        color: #6b7280;
        font-size: 15px;
        margin-top: -10px;
        margin-bottom: 20px;
    }

    .metric-label {
        color: #4b5563;
        font-size: 15px;
        font-weight: 600;
    }

    .metric-value {
        color: #111827;
        font-size: 28px;
        font-weight: 700;
    }

    .section-header {
        background-color: #dbe7f7;
        color: #2f6bd8;
        font-size: 20px;
        font-weight: 700;
        padding: 10px 14px;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .note-text {
        color: #6b7280;
        font-size: 13px;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# FORMAT FUNCTIONS
# =========================================================
def fmt_number(x):
    if pd.isna(x):
        return ""
    return f"{float(x):,.0f}"

def fmt_pct(x):
    if pd.isna(x):
        return ""
    return f"{float(x):.1%}"

def fmt_share(x):
    if pd.isna(x):
        return ""
    return f"{float(x):,.2f}"

# =========================================================
# DCF ENGINE
# =========================================================
def compute_dcf(
    base_ebitda,
    growth_rates,
    terminal_growth,
    depreciation,
    tax_rate,
    capex,
    working_capital,
    wacc,
    net_debt,
    shares_outstanding,
    current_price,
    start_year
):
    years = [start_year + i for i in range(5)]
    year_cols = [str(y) for y in years]

    # Forecast EBITDA
    ebitda_values = []
    prev = base_ebitda
    for g in growth_rates:
        nxt = prev * (1 + g)
        ebitda_values.append(nxt)
        prev = nxt

    terminal_ebitda = ebitda_values[-1] * (1 + terminal_growth)

    # Operating profit and taxes
    operating_profit = [x - depreciation for x in ebitda_values]
    terminal_operating_profit = terminal_ebitda - depreciation

    taxes = [x * tax_rate for x in operating_profit]
    terminal_taxes = terminal_operating_profit * tax_rate

    # UFCF
    ufcf = [
        ebitda_values[i] - taxes[i] - capex - working_capital
        for i in range(5)
    ]
    terminal_ufcf = terminal_ebitda - terminal_taxes - capex - working_capital

    # UFCF Schedule
    ufcf_df = pd.DataFrame(
        {
            year_cols[0]: [growth_rates[0], ebitda_values[0], depreciation, operating_profit[0], tax_rate, taxes[0], capex, working_capital, ufcf[0]],
            year_cols[1]: [growth_rates[1], ebitda_values[1], depreciation, operating_profit[1], tax_rate, taxes[1], capex, working_capital, ufcf[1]],
            year_cols[2]: [growth_rates[2], ebitda_values[2], depreciation, operating_profit[2], tax_rate, taxes[2], capex, working_capital, ufcf[2]],
            year_cols[3]: [growth_rates[3], ebitda_values[3], depreciation, operating_profit[3], tax_rate, taxes[3], capex, working_capital, ufcf[3]],
            year_cols[4]: [growth_rates[4], ebitda_values[4], depreciation, operating_profit[4], tax_rate, taxes[4], capex, working_capital, ufcf[4]],
            "Terminal": [terminal_growth, terminal_ebitda, depreciation, terminal_operating_profit, tax_rate, terminal_taxes, capex, working_capital, terminal_ufcf]
        },
        index=[
            "EBITDA Growth",
            "EBITDA",
            "Tax Depreciation",
            "Operating Profit",
            "Tax Rate",
            "Current Tax",
            "Capital Expenditure",
            "Cash from Working Capital",
            "Unlevered Free Cash Flow"
        ]
    )

    # DCF
    if wacc <= terminal_growth:
        terminal_value = np.nan
        pv_terminal = np.nan
        enterprise_value = np.nan
        equity_value = np.nan
        equity_value_per_share = np.nan
        premium_discount = np.nan
        pv_discrete_list = [ufcf[i] / ((1 + wacc) ** (i + 1)) for i in range(5)]
        pv_discrete = sum(pv_discrete_list)
    else:
        terminal_value = terminal_ufcf / (wacc - terminal_growth)
        pv_discrete_list = [ufcf[i] / ((1 + wacc) ** (i + 1)) for i in range(5)]
        pv_discrete = sum(pv_discrete_list)
        pv_terminal = terminal_value / ((1 + wacc) ** 5)
        enterprise_value = pv_discrete + pv_terminal
        equity_value = enterprise_value - net_debt
        equity_value_per_share = equity_value / shares_outstanding
        premium_discount = (equity_value_per_share / current_price) - 1

    cash_flow_profiles = pd.DataFrame(
        {
            year_cols[0]: [ufcf[0], 0, ufcf[0]],
            year_cols[1]: [ufcf[1], 0, ufcf[1]],
            year_cols[2]: [ufcf[2], 0, ufcf[2]],
            year_cols[3]: [ufcf[3], 0, ufcf[3]],
            year_cols[4]: [ufcf[4], terminal_value if not pd.isna(terminal_value) else np.nan,
                           (ufcf[4] + terminal_value) if not pd.isna(terminal_value) else np.nan],
        },
        index=["Discrete Forecast", "Terminal Value", "Total Cash Flow"]
    )

    assumptions_dcf = pd.DataFrame(
        {"Value": [start_year, terminal_growth, wacc]},
        index=["First Year of Forecast", "Terminal Growth Rate", "WACC"]
    )

    ev_table = pd.DataFrame(
        {"Value": [pv_discrete, pv_terminal, enterprise_value]},
        index=["PV of Discrete", "PV of Terminal", "Enterprise Value"]
    )

    eq_table = pd.DataFrame(
        {"Value": [enterprise_value, -net_debt, equity_value]},
        index=["Enterprise Value", "Less: Net Debt", "Equity Value"]
    )

    per_share_table = pd.DataFrame(
        {"Value": [equity_value, shares_outstanding, equity_value_per_share]},
        index=["Equity Value", "Shares Outstanding", "Equity Value / Share"]
    )

    premium_table = pd.DataFrame(
        {"Value": [equity_value_per_share, current_price, premium_discount]},
        index=["Equity Value / Share", "Current Price", "Premium (Discount)"]
    )

    # Sensitivity ranges
    wacc_range = np.array([wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02])
    growth_range = np.array([
        max(0.0001, terminal_growth - 0.01),
        max(0.0001, terminal_growth - 0.005),
        terminal_growth,
        terminal_growth + 0.005,
        terminal_growth + 0.01
    ])

    ev_sens = pd.DataFrame(
        index=[f"{x:.1%}" for x in wacc_range],
        columns=[f"{g:.1%}" for g in growth_range],
        dtype=float
    )
    share_sens = pd.DataFrame(
        index=[f"{x:.1%}" for x in wacc_range],
        columns=[f"{g:.1%}" for g in growth_range],
        dtype=float
    )
    prem_sens = pd.DataFrame(
        index=[f"{x:.1%}" for x in wacc_range],
        columns=[f"{g:.1%}" for g in growth_range],
        dtype=float
    )
    eq_sens = pd.DataFrame(
        index=[f"{x:.1%}" for x in wacc_range],
        columns=[f"{g:.1%}" for g in growth_range],
        dtype=float
    )

    for w in wacc_range:
        for g in growth_range:
            row_label = f"{w:.1%}"
            col_label = f"{g:.1%}"

            if w <= g:
                ev = np.nan
                eq = np.nan
                share = np.nan
                prem = np.nan
            else:
                tv = terminal_ufcf / (w - g)
                pv_d = sum([ufcf[i] / ((1 + w) ** (i + 1)) for i in range(5)])
                pv_t = tv / ((1 + w) ** 5)
                ev = pv_d + pv_t
                eq = ev - net_debt
                share = eq / shares_outstanding
                prem = (share / current_price) - 1

            ev_sens.loc[row_label, col_label] = ev
            eq_sens.loc[row_label, col_label] = eq
            share_sens.loc[row_label, col_label] = share
            prem_sens.loc[row_label, col_label] = prem

    return {
        "years": years,
        "year_cols": year_cols,
        "ebitda_values": ebitda_values,
        "ufcf": ufcf,
        "ufcf_df": ufcf_df,
        "cash_flow_profiles": cash_flow_profiles,
        "assumptions_dcf": assumptions_dcf,
        "ev_table": ev_table,
        "eq_table": eq_table,
        "per_share_table": per_share_table,
        "premium_table": premium_table,
        "ev_sens": ev_sens,
        "eq_sens": eq_sens,
        "share_sens": share_sens,
        "prem_sens": prem_sens,
        "pv_discrete": pv_discrete,
        "pv_terminal": pv_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "equity_value_per_share": equity_value_per_share,
        "premium_discount": premium_discount,
        "terminal_value": terminal_value
    }

# =========================================================
# DISPLAY HELPERS
# =========================================================
def style_main_table(df):
    out = df.copy().astype(object)
    for idx in out.index:
        for col in out.columns:
            val = df.loc[idx, col]
            if idx in ["EBITDA Growth", "Tax Rate"]:
                out.loc[idx, col] = fmt_pct(val)
            else:
                out.loc[idx, col] = fmt_number(val)
    return out

def style_value_table(df, percent_rows=None, share_rows=None):
    percent_rows = percent_rows or []
    share_rows = share_rows or []
    out = df.copy().astype(object)

    for i in range(len(df)):
        idx = df.index[i]
        val = df.iloc[i, 0]

        if pd.isna(val):
            out.iloc[i, 0] = ""
        elif idx in percent_rows:
            out.iloc[i, 0] = fmt_pct(val)
        elif idx in share_rows:
            out.iloc[i, 0] = fmt_share(val)
        else:
            out.iloc[i, 0] = fmt_number(val)

    return out

def style_sens_num(df):
    out = df.copy().astype(object)
    for r in df.index:
        for c in df.columns:
            v = df.loc[r, c]
            out.loc[r, c] = "" if pd.isna(v) else fmt_number(v)
    return out

def style_sens_share(df):
    out = df.copy().astype(object)
    for r in df.index:
        for c in df.columns:
            v = df.loc[r, c]
            out.loc[r, c] = "" if pd.isna(v) else fmt_share(v)
    return out

def style_sens_pct(df):
    out = df.copy().astype(object)
    for r in df.index:
        for c in df.columns:
            v = df.loc[r, c]
            out.loc[r, c] = "" if pd.isna(v) else fmt_pct(v)
    return out

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("Assumptions")

base_ebitda = st.sidebar.number_input("Base EBITDA 2022", value=18379.0, step=100.0)

st.sidebar.subheader("Forecast Growth Rates")
g1 = st.sidebar.number_input("2023 Growth", value=0.075, step=0.005, format="%.3f")
g2 = st.sidebar.number_input("2024 Growth", value=0.070, step=0.005, format="%.3f")
g3 = st.sidebar.number_input("2025 Growth", value=0.060, step=0.005, format="%.3f")
g4 = st.sidebar.number_input("2026 Growth", value=0.050, step=0.005, format="%.3f")
g5 = st.sidebar.number_input("2027 Growth", value=0.040, step=0.005, format="%.3f")
terminal_growth = st.sidebar.number_input("Terminal Growth Rate", value=0.025, step=0.005, format="%.3f")

st.sidebar.subheader("Taxes / Depreciation")
depreciation = st.sidebar.number_input("Tax Depreciation", value=3700.0, step=50.0)
tax_rate = st.sidebar.number_input("Tax Rate", value=0.170, step=0.005, format="%.3f")

st.sidebar.subheader("Capital / Valuation")
capex = st.sidebar.number_input("Capital Expenditure", value=3700.0, step=50.0)
working_capital = st.sidebar.number_input("Cash from Working Capital", value=100.0, step=10.0)
wacc = st.sidebar.number_input("WACC", value=0.135, step=0.005, format="%.3f")
net_debt = st.sidebar.number_input("Net Debt", value=18642.0, step=100.0)
shares_outstanding = st.sidebar.number_input("Shares Outstanding", value=34200.0, step=100.0)
current_price = st.sidebar.number_input("Current Price", value=2.71, step=0.01)
start_year = st.sidebar.number_input("First Forecast Year", value=2023, step=1)

# =========================================================
# RUN MODEL
# =========================================================
results = compute_dcf(
    base_ebitda=base_ebitda,
    growth_rates=[g1, g2, g3, g4, g5],
    terminal_growth=terminal_growth,
    depreciation=depreciation,
    tax_rate=tax_rate,
    capex=capex,
    working_capital=working_capital,
    wacc=wacc,
    net_debt=net_debt,
    shares_outstanding=shares_outstanding,
    current_price=current_price,
    start_year=start_year
)

# =========================================================
# HEADER
# =========================================================
st.title("DCF Valuation Modeling")
st.markdown(
    '<div class="author-text">Interactive valuation platform | Author: Zakariya Boutayeb</div>',
    unsafe_allow_html=True
)

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown('<div class="metric-label">Enterprise Value</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{fmt_number(results["enterprise_value"])}</div>', unsafe_allow_html=True)

with m2:
    st.markdown('<div class="metric-label">Equity Value</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{fmt_number(results["equity_value"])}</div>', unsafe_allow_html=True)

with m3:
    st.markdown('<div class="metric-label">Equity Value / Share</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{fmt_share(results["equity_value_per_share"])}</div>', unsafe_allow_html=True)

with m4:
    st.markdown('<div class="metric-label">Premium (Discount)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{fmt_pct(results["premium_discount"])}</div>', unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "1. UFCF Schedule",
    "2. DCF Schedule",
    "3. Sensitivity Analysis",
    "4. Charts"
])

# =========================================================
# TAB 1 - UFCF
# =========================================================
with tab1:
    st.markdown('<div class="section-header">Unlevered Free Cash Flow Schedule</div>', unsafe_allow_html=True)
    st.caption("All figures in USD thousands unless stated")
    st.dataframe(style_main_table(results["ufcf_df"]), use_container_width=True)

# =========================================================
# TAB 2 - DCF
# =========================================================
with tab2:
    st.markdown('<div class="section-header">Discounted Cash Flow Schedule</div>', unsafe_allow_html=True)
    st.caption("All figures in USD thousands unless stated")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Assumptions")
        st.dataframe(
            style_value_table(
                results["assumptions_dcf"],
                percent_rows=["Terminal Growth Rate", "WACC"]
            ),
            use_container_width=True
        )

        st.subheader("Enterprise Value")
        st.dataframe(
            style_value_table(results["ev_table"]),
            use_container_width=True
        )

    with c2:
        st.subheader("Equity Value")
        st.dataframe(
            style_value_table(results["eq_table"]),
            use_container_width=True
        )

        st.subheader("Equity Value Per Share")
        st.dataframe(
            style_value_table(
                results["per_share_table"],
                share_rows=["Equity Value / Share"]
            ),
            use_container_width=True
        )

        st.subheader("Premium (Discount)")
        st.dataframe(
            style_value_table(
                results["premium_table"],
                percent_rows=["Premium (Discount)"],
                share_rows=["Equity Value / Share", "Current Price"]
            ),
            use_container_width=True
        )

    st.subheader("Cash Flow Profiles")
    cf_disp = results["cash_flow_profiles"].copy().astype(object)
    for idx in results["cash_flow_profiles"].index:
        for col in results["cash_flow_profiles"].columns:
            cf_disp.loc[idx, col] = fmt_number(results["cash_flow_profiles"].loc[idx, col])
    st.dataframe(cf_disp, use_container_width=True)

# =========================================================
# TAB 3 - SENSITIVITY
# =========================================================
with tab3:
    st.markdown('<div class="section-header">Sensitivity Analysis</div>', unsafe_allow_html=True)
    st.caption("Rows = WACC | Columns = Terminal Growth Rate")

    st.subheader("Enterprise Value Sensitivity")
    st.dataframe(style_sens_num(results["ev_sens"]), use_container_width=True)

    st.subheader("Equity Value Per Share Sensitivity")
    st.dataframe(style_sens_share(results["share_sens"]), use_container_width=True)

    st.subheader("Equity Value Sensitivity")
    st.dataframe(style_sens_num(results["eq_sens"]), use_container_width=True)

    st.subheader("Premium (Discount) Sensitivity")
    st.dataframe(style_sens_pct(results["prem_sens"]), use_container_width=True)

    h1, h2 = st.columns(2)

    with h1:
        ev_heat = px.imshow(
            results["ev_sens"].astype(float),
            text_auto=".0f",
            aspect="auto",
            title="Enterprise Value Heatmap",
            labels={"x": "Terminal Growth", "y": "WACC", "color": "EV"}
        )
        st.plotly_chart(ev_heat, use_container_width=True)

    with h2:
        share_heat = px.imshow(
            results["share_sens"].astype(float),
            text_auto=".2f",
            aspect="auto",
            title="Equity Value / Share Heatmap",
            labels={"x": "Terminal Growth", "y": "WACC", "color": "Value / Share"}
        )
        st.plotly_chart(share_heat, use_container_width=True)

# =========================================================
# TAB 4 - CHARTS
# =========================================================
with tab4:
    st.markdown('<div class="section-header">Interactive Charts</div>', unsafe_allow_html=True)

    chart_df = pd.DataFrame({
        "Year": [str(y) for y in results["years"]],
        "EBITDA": results["ebitda_values"],
        "UFCF": results["ufcf"]
    })

    c1, c2 = st.columns(2)

    with c1:
        fig1 = px.line(
            chart_df,
            x="Year",
            y="EBITDA",
            markers=True,
            title="EBITDA Forecast"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        fig2 = px.bar(
            chart_df,
            x="Year",
            y="UFCF",
            title="Unlevered Free Cash Flow Forecast"
        )
        st.plotly_chart(fig2, use_container_width=True)

    ev_breakdown = pd.DataFrame({
        "Component": ["PV of Discrete Forecast", "PV of Terminal Value"],
        "Value": [results["pv_discrete"], results["pv_terminal"]]
    })

    c3, c4 = st.columns(2)

    with c3:
        fig3 = px.pie(
            ev_breakdown,
            names="Component",
            values="Value",
            title="Enterprise Value Breakdown"
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        fig4 = go.Figure(go.Waterfall(
            name="Valuation Bridge",
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Enterprise Value", "Net Debt", "Equity Value"],
            y=[results["enterprise_value"], -net_debt, results["equity_value"]],
            text=[
                fmt_number(results["enterprise_value"]),
                fmt_number(-net_debt),
                fmt_number(results["equity_value"])
            ]
        ))
        fig4.update_layout(title="Enterprise Value to Equity Value Bridge")
        st.plotly_chart(fig4, use_container_width=True)