from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "MERGED DATASETS"

st.set_page_config(
    page_title="Cashflow Intelligence",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink: #14213d; --muted: #687386; --accent: #f26b38; --teal: #157a78; --cream: #f7f4ed; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: var(--ink); }
    .stApp { background: var(--cream); }
    [data-testid="stSidebar"] { background: #14213d; }
    [data-testid="stSidebar"] * { color: #f7f4ed; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Space Grotesk', sans-serif; }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    .hero { padding: 1.2rem 0 1.8rem; border-bottom: 1px solid #dedbd3; margin-bottom: 1.2rem; }
    .eyebrow { color: var(--accent); text-transform: uppercase; letter-spacing: .14em; font-size: .72rem; font-weight: 700; }
    .hero h1 { font-size: clamp(2rem, 4vw, 3.5rem); margin: .2rem 0 .35rem; }
    .hero p { color: var(--muted); max-width: 760px; font-size: 1.02rem; }
    .section-note { color: var(--muted); margin-top: -0.6rem; margin-bottom: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


DATASETS = {
    "trends": "cyber_national_trends.csv",
    "banks": "merged_bank_financials.csv",
    "transactions": "bank_transactions_clean.csv",
    "crime": "merged_crime_data.csv",
}


@st.cache_data(show_spinner=False)
def load_dataset(name: str) -> pd.DataFrame:
    path = DATA_DIR / DATASETS[name]
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path, low_memory=False)
    for column in frame.columns:
        if column in {"Year", "TransactionDate", "CustomerDOB"}:
            continue
        if frame[column].dtype == "object":
            numeric = pd.to_numeric(frame[column], errors="coerce")
            if numeric.notna().mean() > 0.8:
                frame[column] = numeric
    return frame


def format_number(value, decimals=0):
    if pd.isna(value):
        return "—"
    if decimals:
        return f"{value:,.{decimals}f}"
    return f"{value:,.0f}"


def metric_delta(current, previous, suffix=""):
    if previous in (None, 0) or pd.isna(previous) or pd.isna(current):
        return None
    return f"{((current - previous) / abs(previous)) * 100:+.1f}%{suffix}"


def chart_layout(fig):
    fig.update_layout(
        template="simple_white",
        margin=dict(l=12, r=12, t=48, b=12),
        font=dict(family="DM Sans", color="#14213d"),
        title_font=dict(family="Space Grotesk", size=18),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    return fig


def show_missing_data():
    st.error("Merged datasets are not available yet.")
    st.code("python data_merge.py", language="powershell")
    st.caption("Run the pipeline from the project root, then refresh this page.")


trends = load_dataset("trends")
banks = load_dataset("banks")
transactions = load_dataset("transactions")
crime = load_dataset("crime")

if trends.empty and banks.empty and transactions.empty and crime.empty:
    show_missing_data()
    st.stop()

st.sidebar.markdown("## Cashflow Intelligence")
st.sidebar.caption("Banking, transactions and cybercrime in one view")
st.sidebar.divider()
page = st.sidebar.radio("Explore", ["Overview", "Cyber trends", "Banking", "Transactions", "Crime & states"])
st.sidebar.divider()
st.sidebar.caption(f"Data directory\n`{DATA_DIR}`")

st.markdown(
    '<div class="hero"><div class="eyebrow">India · financial risk analytics</div>'
    '<h1>Cashflow Intelligence</h1>'
    '<p>A practical command centre for reading banking health, transaction behaviour and cybercrime signals across the available datasets.</p></div>',
    unsafe_allow_html=True,
)

if page == "Overview":
    st.markdown("## Signal board")
    st.markdown('<p class="section-note">A high-level view of the project outputs and the latest measurable signals.</p>', unsafe_allow_html=True)
    latest_year = int(banks["Year"].max()) if not banks.empty and "Year" in banks else None
    trend_year = int(trends["Year"].max()) if not trends.empty and "Year" in trends else None
    total_assets = banks.loc[banks["Year"] == latest_year, "Total_Assets_Cr"].sum() if latest_year else None
    total_txn = len(transactions) if not transactions.empty else None
    cyber_total = trends.loc[trends["Year"] == trend_year, "Cybersecurity_Incidents_Total"].iloc[0] if trend_year and "Cybersecurity_Incidents_Total" in trends and trends.loc[trends["Year"] == trend_year, "Cybersecurity_Incidents_Total"].notna().any() else None
    average_crime_rate = crime["Crime_Rate_Per_100K"].mean() if not crime.empty and "Crime_Rate_Per_100K" in crime else None

    cards = st.columns(4)
    cards[0].metric("Bank assets", f"₹{format_number(total_assets)} Cr", f"FY {latest_year}" if latest_year else None)
    cards[1].metric("Clean transactions", format_number(total_txn), "records" if total_txn is not None else None)
    cards[2].metric("Cyber incidents", format_number(cyber_total), f"reported in {trend_year}" if trend_year else None)
    cards[3].metric("Average crime rate", format_number(average_crime_rate, 1), "per 100K" if average_crime_rate is not None else None)

    left, right = st.columns([1.35, 1])
    with left:
        if not trends.empty:
            trend_plot = trends.melt("Year", value_vars=["Cybersecurity_Incidents_Total", "Cyber_Fraud_Incidents"], var_name="Metric", value_name="Value")
            fig = px.line(trend_plot, x="Year", y="Value", color="Metric", markers=True, title="National cyber signals over time")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
    with right:
        if not banks.empty:
            latest_banks = banks[banks["Year"] == latest_year].nlargest(8, "Total_Assets_Cr")
            fig = px.bar(latest_banks, x="Total_Assets_Cr", y="Bank_Name", color="Bank_Type", orientation="h", title=f"Largest banks by assets · {latest_year}")
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(chart_layout(fig), use_container_width=True)

    st.markdown("### Data coverage")
    coverage = pd.DataFrame({"Dataset": ["Cyber trends", "Bank financials", "Transactions", "Crime & states"], "Rows": [len(trends), len(banks), len(transactions), len(crime)]})
    st.dataframe(coverage, hide_index=True, use_container_width=True)

elif page == "Cyber trends":
    st.markdown("## Cyber trends")
    st.markdown('<p class="section-note">National incident and financial-fraud measures reported across the source years.</p>', unsafe_allow_html=True)
    if trends.empty:
        show_missing_data()
    else:
        trends = trends.sort_values("Year")
        available = [column for column in trends.columns if column != "Year" and trends[column].notna().any()]
        selected = st.multiselect("Metrics", available, default=available[:2])
        if selected:
            plot_data = trends.melt("Year", value_vars=selected, var_name="Metric", value_name="Value").dropna()
            fig = px.line(plot_data, x="Year", y="Value", color="Metric", markers=True, title="Selected national metrics")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        st.dataframe(trends, hide_index=True, use_container_width=True)

elif page == "Banking":
    st.markdown("## Banking health")
    st.markdown('<p class="section-note">Compare balance-sheet scale, profitability, asset quality and access infrastructure.</p>', unsafe_allow_html=True)
    if banks.empty:
        show_missing_data()
    else:
        years = sorted(banks["Year"].dropna().unique())
        year = st.select_slider("Reporting year", options=years, value=years[-1])
        bank_types = st.multiselect("Bank types", sorted(banks["Bank_Type"].dropna().unique()), default=sorted(banks["Bank_Type"].dropna().unique()))
        view = banks[(banks["Year"] == year) & banks["Bank_Type"].isin(bank_types)]
        cards = st.columns(3)
        cards[0].metric("Assets", f"₹{format_number(view["Total_Assets_Cr"].sum())} Cr")
        cards[1].metric("Deposits", f"₹{format_number(view["Deposits_Cr"].sum())} Cr")
        cards[2].metric("Average ROA", f"{view["Return_on_Assets_Pct"].mean():.2f}%")
        left, right = st.columns(2)
        with left:
            fig = px.scatter(view, x="Net_NPA_Pct", y="Return_on_Assets_Pct", size="Total_Assets_Cr", color="Bank_Type", hover_name="Bank_Name", title="Asset quality vs return on assets")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        with right:
            top = view.nlargest(12, "ATMs_Total")
            fig = px.bar(top, x="ATMs_Total", y="Bank_Name", color="Bank_Type", orientation="h", title="Banks with the most ATMs")
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        st.dataframe(view.sort_values("Total_Assets_Cr", ascending=False), hide_index=True, use_container_width=True)

elif page == "Transactions":
    st.markdown("## Transaction behaviour")
    st.markdown('<p class="section-note">Explore cleaned transaction volume, value distribution and location concentration.</p>', unsafe_allow_html=True)
    if transactions.empty:
        show_missing_data()
    else:
        transactions["TransactionDate"] = pd.to_datetime(transactions["TransactionDate"], errors="coerce")
        transactions["TransactionAmount_INR"] = pd.to_numeric(transactions["TransactionAmount_INR"], errors="coerce")
        min_date, max_date = transactions["TransactionDate"].min(), transactions["TransactionDate"].max()
        date_range = st.date_input("Date range", value=(min_date.date(), max_date.date()))
        filtered = transactions
        if isinstance(date_range, tuple) and len(date_range) == 2:
            filtered = transactions[transactions["TransactionDate"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))]
        cards = st.columns(3)
        cards[0].metric("Transactions", format_number(len(filtered)))
        cards[1].metric("Total value", f"₹{format_number(filtered["TransactionAmount_INR"].sum())}")
        cards[2].metric("Average amount", f"₹{format_number(filtered["TransactionAmount_INR"].mean(), 2)}")
        left, right = st.columns(2)
        with left:
            daily = filtered.set_index("TransactionDate").resample("ME")["TransactionAmount_INR"].agg(["count", "sum"]).reset_index()
            fig = px.line(daily, x="TransactionDate", y="sum", markers=True, title="Monthly transaction value")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        with right:
            locations = filtered.groupby("CustLocation").agg(Transactions=("TransactionID", "count"), Value=("TransactionAmount_INR", "sum")).nlargest(12, "Transactions").reset_index()
            fig = px.bar(locations, x="Transactions", y="CustLocation", orientation="h", title="Busiest customer locations")
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        st.dataframe(filtered.head(1000), hide_index=True, use_container_width=True)
        st.caption("Showing the first 1,000 filtered records for a responsive browser experience.")

else:
    st.markdown("## Crime & states")
    st.markdown('<p class="section-note">Compare socioeconomic indicators with reported crime and cyber-fraud measures.</p>', unsafe_allow_html=True)
    if crime.empty:
        show_missing_data()
    else:
        states = sorted(crime["State_UT"].dropna().unique())
        selected_states = st.multiselect("States / UTs", states, default=states[:8])
        view = crime[crime["State_UT"].isin(selected_states)] if selected_states else crime
        state_summary = view.groupby("State_UT", as_index=False).agg(
            Crime_Rate_Per_100K=("Crime_Rate_Per_100K", "mean"),
            Cyber_Crimes=("Cyber_Crimes", "sum"),
            Cyber_Fraud_Amount_Reported_Lakh=("Cyber_Fraud_Amount_Reported_Lakh", "sum"),
        ).sort_values("Crime_Rate_Per_100K", ascending=False)
        left, right = st.columns(2)
        with left:
            fig = px.bar(state_summary.head(15), x="Crime_Rate_Per_100K", y="State_UT", orientation="h", title="Highest average crime rate")
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        with right:
            fig = px.scatter(state_summary, x="Cyber_Crimes", y="Cyber_Fraud_Amount_Reported_Lakh", size="Crime_Rate_Per_100K", hover_name="State_UT", title="Cybercrime volume vs fraud amount")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        st.dataframe(state_summary, hide_index=True, use_container_width=True)

st.divider()
st.caption("Cashflow Intelligence · Local analytical dashboard · Source data remains in the project datasets")
