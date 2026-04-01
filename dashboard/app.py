"""
Credit Risk Dashboard — Streamlit Multi-Page Application.

Six pages with full methodology explainers, interactive inputs, and
interpretive callouts designed for a credit risk professional audience.
"""
import glob
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from models.pd_model import PDModel
from models.lgd_model import LGDModel
from models.ead_model import EADModel
from portfolio.expected_loss import compute_expected_loss, aggregate_el
from portfolio.credit_var import run_monte_carlo
from portfolio.concentration import concentration_analysis
from portfolio.rwa import compute_rwa
from migration.transition_matrix import run_migration_analysis
from stress.stress_engine import run_all_scenarios

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Credit Risk Engine",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1A1A2E; }
    [data-testid="stSidebar"] * { color: #E0E0E0 !important; }
    .info-box {
        background: #F0F4FF; border-left: 4px solid #0F3460;
        padding: 12px 16px; border-radius: 4px; margin: 8px 0 16px 0;
        font-size: 0.92rem; line-height: 1.5; color: #1a1a2e !important;
    }
    .method-box {
        background: #FFF8F0; border-left: 4px solid #E67E22;
        padding: 12px 16px; border-radius: 4px; margin: 8px 0 16px 0;
        font-size: 0.88rem; line-height: 1.5; color: #333 !important;
    }
    .insight-box {
        background: #F0FFF4; border-left: 4px solid #2E7D32;
        padding: 12px 16px; border-radius: 4px; margin: 8px 0 16px 0;
        font-size: 0.90rem; line-height: 1.5; color: #1b5e20 !important;
    }
    .warning-box {
        background: #FFF0F0; border-left: 4px solid #E4002B;
        padding: 12px 16px; border-radius: 4px; margin: 8px 0 16px 0;
        font-size: 0.90rem; line-height: 1.5; color: #7f0000 !important;
    }
    .kpi-label { font-size: 0.75rem; color: #666 !important; margin-top: 2px; }
    .info-box b, .method-box b, .insight-box b, .warning-box b { color: inherit !important; }
    .traffic-light { font-size: 0.95rem; color: #222 !important; line-height: 1.6; }
    .traffic-light b { color: #222 !important; }
    /* Prevent metric value truncation */
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; white-space: nowrap !important; overflow: visible !important; text-overflow: unset !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; white-space: normal !important; }
</style>
""", unsafe_allow_html=True)

RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
PALETTE = config.CHART_PALETTE


def info_box(text: str) -> None:
    st.markdown(f'<div class="info-box">{text}</div>', unsafe_allow_html=True)


def method_box(text: str) -> None:
    st.markdown(f'<div class="method-box">{text}</div>', unsafe_allow_html=True)


def insight_box(text: str) -> None:
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)


def warning_box(text: str) -> None:
    st.markdown(f'<div class="warning-box">{text}</div>', unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## **Credit Risk Engine**")
    st.markdown("**Credit Risk Engine** v1.0")
    st.markdown("---")

    page = st.radio(
        "Navigate to",
        [
            "Executive Summary",
            "Portfolio Overview",
            "Risk Models",
            "Portfolio Risk",
            "Migration & Stress Testing",
            "SQL Explorer",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("##### Input Data")
    st.caption("250 obligors | ~408 facilities")
    st.caption("Segments: Large Corp, LevFin, ProjFin, Structured")
    st.caption("Geography: 7 European jurisdictions")
    st.caption("Ratings: AAA through CCC")
    st.caption("Reference date: 27 Mar 2026")

    st.markdown("---")
    st.caption("Synthetic data for demonstration.")
    st.caption("Synthetic data for demonstration purposes only.")


# ── Data loading (cached) ─────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Running risk models...")
def load_data():
    pd_model = PDModel()
    pd_results = pd_model.train()
    lgd_results = LGDModel().estimate()
    ead_results = EADModel().estimate()
    el_df = compute_expected_loss(pd_results, lgd_results, ead_results)
    el_agg = aggregate_el(el_df)
    var_results = run_monte_carlo(el_df, n_simulations=config.MONTE_CARLO_SIMULATIONS)
    conc = concentration_analysis(el_df)
    rwa_df = compute_rwa(el_df)
    migration = run_migration_analysis()
    stress = run_all_scenarios(el_df, n_simulations=5000)
    return {
        "pd_model": pd_model, "pd_results": pd_results,
        "lgd_results": lgd_results, "ead_results": ead_results,
        "el_df": el_df, "el_agg": el_agg, "var_results": var_results,
        "conc": conc, "rwa_df": rwa_df, "migration": migration, "stress": stress,
    }


data = load_data()


# ══════════════════════════════════════════════════════════════════════════
# PAGE 0: EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════
if page == "Executive Summary":
    st.title("Executive Summary")

    info_box(
        "<b>What is this?</b> This dashboard models the credit risk of a synthetic EUR 655B "
        "European Corporate & Investment Banking portfolio, simulating an internal risk engine "
        "for a European bank. It estimates the probability and severity of credit losses using "
        "industry-standard regulatory models (Basel III Internal Ratings-Based framework), runs Monte Carlo "
        "simulations for tail risk, and stress-tests the portfolio under European Banking Authority macroeconomic scenarios."
    )

    el_df = data["el_df"]
    var_results = data["var_results"]
    rwa_df = data["rwa_df"]
    stress = data["stress"]
    conc = data["conc"]

    total_ead = el_df["ead"].sum()
    total_el = el_df["el"].sum()
    el_bps = total_el / total_ead * 10_000

    # ── INPUT DATA SECTION ─────────────────────────────────────────────
    st.markdown("### Input Data — What Goes Into the Models")
    info_box(
        "Before any risk calculation, we need a <b>portfolio</b>: a set of borrowers (obligors) "
        "and their credit facilities (loans, bonds, guarantees). Each obligor has financial statements "
        "(assets, debt, EBITDA, interest expense) and an internal credit rating. Each facility has a "
        "committed amount, drawn amount, seniority, collateral, and maturity date. "
        "This synthetic portfolio mimics a European Corporate & Investment Banking lending book."
    )

    # Summary stats
    conn = sqlite3.connect(str(config.DB_PATH))
    ob_stats = pd.read_sql("SELECT COUNT(*) as n, COUNT(DISTINCT sector) as sectors, COUNT(DISTINCT country) as countries FROM obligors", conn)
    fac_stats = pd.read_sql("SELECT COUNT(*) as n, COUNT(DISTINCT facility_type) as types, ROUND(SUM(commitment_amount),0) as total_commit, ROUND(SUM(drawn_amount),0) as total_drawn FROM facilities", conn)
    seg_dist = pd.read_sql("SELECT segment, COUNT(*) as count FROM obligors GROUP BY segment ORDER BY count DESC", conn)
    rating_dist = pd.read_sql("""
        SELECT internal_rating as Rating, COUNT(*) as Obligors,
        ROUND(AVG(leverage_ratio),3) as "Avg Leverage", ROUND(AVG(interest_coverage),1) as "Avg Interest Coverage",
        ROUND(AVG(debt_to_ebitda),1) as "Avg Debt/EBITDA"
        FROM obligors GROUP BY internal_rating
        ORDER BY CASE internal_rating
            WHEN 'AAA' THEN 1 WHEN 'AA' THEN 2 WHEN 'A' THEN 3 WHEN 'BBB' THEN 4
            WHEN 'BB' THEN 5 WHEN 'B' THEN 6 WHEN 'CCC' THEN 7 WHEN 'D' THEN 8 END
    """, conn)
    conn.close()

    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Obligors (Borrowers)", f"{ob_stats['n'].iloc[0]}")
    i2.metric("Facilities (Loans/Bonds)", f"{fac_stats['n'].iloc[0]}")
    i3.metric("Total Commitments", f"EUR {fac_stats['total_commit'].iloc[0]/1000:,.0f}B")
    i4.metric("Total Drawn", f"EUR {fac_stats['total_drawn'].iloc[0]/1000:,.0f}B")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Portfolio Segments**")
        seg_dist.columns = ["Segment", "Count"]
        seg_dist["Segment"] = seg_dist["Segment"].str.replace("_", " ").str.title()
        st.dataframe(seg_dist, use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("**Rating Distribution with Key Ratios (Model Inputs)**")
        st.dataframe(rating_dist, use_container_width=True, hide_index=True)

    method_box(
        "<b>How inputs flow to outputs:</b> Financial ratios (leverage, interest coverage, debt/EBITDA) + rating "
        "feed into the <b>Probability of Default model</b>. Seniority + collateral type feed into the <b>Loss Given Default model</b>. "
        "Drawn + undrawn amounts feed into the <b>Exposure at Default model</b>. Together: "
        "<b>Expected Loss = Probability of Default x Loss Given Default x Exposure at Default</b>, computed per facility and aggregated."
    )

    st.markdown("---")

    # ── OUTPUT SECTION ─────────────────────────────────────────────────
    st.markdown("### Key Risk Indicators — Model Outputs")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Exposure at Default", f"EUR {total_ead/1000:,.0f}B")
        st.markdown('<div class="kpi-label">Sum of drawn + contingent exposure across 408 facilities</div>', unsafe_allow_html=True)
    with c2:
        st.metric("Expected Loss", f"EUR {total_el:,.0f}M ({el_bps:.0f} basis points)")
        st.markdown('<div class="kpi-label">Average annual loss = Prob. of Default x Loss Given Default x Exposure at Default, summed across portfolio</div>', unsafe_allow_html=True)
    with c3:
        st.metric("Credit Value at Risk (99.9%)", f"EUR {var_results['var_999']:,.0f}M")
        st.markdown('<div class="kpi-label">Worst-case loss exceeded only 0.1% of the time (1-in-1,000 year event)</div>', unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("Risk-Weighted Assets", f"EUR {rwa_df['rwa'].sum()/1000:,.0f}B")
        st.markdown('<div class="kpi-label">Basel III Internal Ratings-Based capital requirement base. Drives minimum CET1 capital.</div>', unsafe_allow_html=True)
    with c5:
        wavg_pd = (el_df["pd_score"] * el_df["ead"]).sum() / total_ead
        st.metric("Weighted Avg Prob. of Default", f"{wavg_pd:.2%}")
        st.markdown('<div class="kpi-label">Exposure-weighted probability of default across all obligors</div>', unsafe_allow_html=True)
    with c6:
        severe_el = stress["severely_adverse"]["total_el_stressed"]
        st.metric("Stressed Expected Loss (Severe)", f"EUR {severe_el:,.0f}M (+{stress['severely_adverse']['el_increase_pct']:.0f}%)")
        st.markdown('<div class="kpi-label">Expected loss under GDP -3.5%, unemployment 12%, rates +400 basis points</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Traffic-light risk assessment
    st.markdown("### Risk Assessment")
    t1, t2, t3 = st.columns(3)
    with t1:
        ig_share = el_df[el_df["internal_rating"].isin(["AAA","AA","A","BBB"])]["ead"].sum() / total_ead
        color = "#2E7D32" if ig_share > 0.6 else ("#E67E22" if ig_share > 0.4 else "#E4002B")
        label = "GOOD" if ig_share > 0.6 else ("WATCH" if ig_share > 0.4 else "ALERT")
        st.markdown(
            f'<div class="traffic-light"><span style="color:{color};font-weight:bold;">[{label}]</span> '
            f'<b>Portfolio Quality</b><br>Investment-grade share: <b>{ig_share:.0%}</b> of Exposure at Default<br>'
            f'<span style="font-size:0.8rem;color:#888;">Investment-grade = AAA through BBB. Above 60% is healthy for a Corporate & Investment Banking book.</span></div>',
            unsafe_allow_html=True)

    with t2:
        hhi = conc["hhi_sector"]
        color = "#2E7D32" if hhi < 0.10 else ("#E67E22" if hhi < 0.18 else "#E4002B")
        label = "GOOD" if hhi < 0.10 else ("WATCH" if hhi < 0.18 else "ALERT")
        st.markdown(
            f'<div class="traffic-light"><span style="color:{color};font-weight:bold;">[{label}]</span> '
            f'<b>Concentration Risk</b><br>Sector Herfindahl-Hirschman Index: <b>{hhi:.4f}</b> ({conc["hhi_sector_classification"]})<br>'
            f'<span style="font-size:0.8rem;color:#888;">Index &lt; 0.10 = diversified, 0.10-0.18 = moderate, &gt; 0.18 = concentrated.</span></div>',
            unsafe_allow_html=True)

    with t3:
        stress_ratio = severe_el / total_el
        color = "#2E7D32" if stress_ratio < 3 else ("#E67E22" if stress_ratio < 5 else "#E4002B")
        label = "GOOD" if stress_ratio < 3 else ("WATCH" if stress_ratio < 5 else "ALERT")
        st.markdown(
            f'<div class="traffic-light"><span style="color:{color};font-weight:bold;">[{label}]</span> '
            f'<b>Stress Resilience</b><br>Severe stress multiplier: <b>{stress_ratio:.1f}x</b> baseline Expected Loss<br>'
            f'<span style="font-size:0.8rem;color:#888;">Below 3x indicates robust. Above 5x signals vulnerability.</span></div>',
            unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### How to Read This Dashboard")
    st.markdown("""
    - **Portfolio Overview** — What's in the lending book: sectors, ratings, countries, largest names
    - **Risk Models** — How we quantify risk: Probability of Default (will they default?), Loss Given Default (how much do we lose?), Exposure at Default (how much is exposed?)
    - **Portfolio Risk** — What could we lose: expected loss, tail risk (Value at Risk), concentration, regulatory capital (Risk-Weighted Assets)
    - **Migration & Stress Testing** — How risk evolves: rating transitions over time, impact of economic downturns
    - **SQL Explorer** — Direct queries against the underlying portfolio database
    """)


# ══════════════════════════════════════════════════════════════════════════
# PAGE 1: PORTFOLIO OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
elif page == "Portfolio Overview":
    st.title("Portfolio Overview")

    info_box(
        "<b>What are we looking at?</b> The composition of the lending book — "
        "who we lend to (sectors, countries), how much (commitment, drawn), "
        "and the credit quality distribution (ratings). This is the starting point "
        "for understanding where risk is concentrated before running any models."
    )

    el_df = data["el_df"]

    # Input data summary
    with st.expander("Input Data Summary", expanded=True):
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("Obligors", f"{el_df['obligor_id'].nunique()}")
        d2.metric("Facilities", f"{len(el_df):,}")
        total_ead_b = el_df['ead'].sum() / 1000
        d3.metric("Total Commitment", f"EUR {total_ead_b:,.1f}B")
        conn = sqlite3.connect(str(config.DB_PATH))
        min_mat = pd.read_sql("SELECT MIN(maturity_date) as mn, MAX(maturity_date) as mx FROM facilities", conn)
        conn.close()
        # Format dates as short "Mon YYYY" to avoid truncation
        from datetime import datetime
        early_dt = datetime.strptime(min_mat["mn"].iloc[0][:10], "%Y-%m-%d")
        late_dt = datetime.strptime(min_mat["mx"].iloc[0][:10], "%Y-%m-%d")
        d4.metric("Earliest Maturity", early_dt.strftime("%b %Y"))
        d5.metric("Latest Maturity", late_dt.strftime("%b %Y"))

    # Filters
    st.markdown("##### Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_sectors = st.multiselect("Sector", config.SECTORS, default=config.SECTORS)
    with f2:
        sel_ratings = st.multiselect("Rating", RATING_ORDER, default=RATING_ORDER)
    with f3:
        all_countries = sorted(el_df["sector"].unique())  # get from data
        conn = sqlite3.connect(str(config.DB_PATH))
        countries_list = [r[0] for r in conn.execute("SELECT DISTINCT country FROM obligors ORDER BY country").fetchall()]
        conn.close()
        sel_countries = st.multiselect("Country", countries_list, default=countries_list)

    # Apply filters via DB query for country
    conn = sqlite3.connect(str(config.DB_PATH))
    obligor_countries = pd.read_sql("SELECT obligor_id, country FROM obligors", conn)
    conn.close()
    filt = el_df.merge(obligor_countries, on="obligor_id", how="left")
    filt = filt[
        filt["sector"].isin(sel_sectors)
        & filt["internal_rating"].isin(sel_ratings)
        & filt["country"].isin(sel_countries)
    ]

    if len(filt) == 0:
        st.warning("No data matches the selected filters.")
    else:
        total_ead = filt["ead"].sum()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Filtered Exposure at Default", f"EUR {total_ead/1000:,.0f}B")
        c2.metric("Obligors", f"{filt['obligor_id'].nunique()}")
        wavg_pd = (filt["pd_score"] * filt["ead"]).sum() / total_ead if total_ead > 0 else 0
        c3.metric("Wtd Avg Prob. of Default", f"{wavg_pd:.2%}")
        c4.metric("Total Expected Loss", f"EUR {filt['el'].sum():,.0f}M")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            sector_ead = filt.groupby("sector")["ead"].sum().reset_index()
            fig = px.pie(sector_ead, values="ead", names="sector", hole=0.45,
                         title="Exposure by Sector", color_discrete_sequence=PALETTE)
            fig.update_layout(height=400, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
            insight_box("Sector diversification reduces idiosyncratic risk. Watch for any single sector exceeding 20% — it may warrant sub-limits.")

        with col2:
            rating_ead = filt.groupby("internal_rating")["ead"].sum().reindex(RATING_ORDER).fillna(0).reset_index()
            fig = px.bar(rating_ead, x="internal_rating", y="ead",
                         title="Exposure by Rating Grade",
                         labels={"ead": "Exposure at Default (EUR M)", "internal_rating": "Rating"},
                         color_discrete_sequence=[config.BRAND_RED])
            fig.update_layout(height=400, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
            ig = filt[filt["internal_rating"].isin(["AAA","AA","A","BBB"])]["ead"].sum()
            insight_box(f"Investment-grade (AAA through BBB) represents <b>{ig/total_ead:.0%}</b> of filtered exposure. Sub-investment-grade carries disproportionate expected loss.")

        col3, col4 = st.columns(2)
        with col3:
            geo = filt.groupby("country")["ead"].sum().sort_values(ascending=False).reset_index()
            fig = px.bar(geo, x="country", y="ead", title="Exposure by Country",
                         labels={"ead": "Exposure at Default (EUR M)", "country": "Country"},
                         color_discrete_sequence=[config.BRAND_DARK_GREY])
            fig.update_layout(height=400, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col4:
            st.markdown("##### Top 10 Obligors by Exposure at Default")
            top10 = data["conc"]["top_10_obligors"][["obligor_id", "sector", "total_ead", "pct_of_portfolio"]].copy()
            top10.columns = ["Obligor", "Sector", "Exposure at Default (EUR M)", "% of Portfolio"]
            top10["Exposure at Default (EUR M)"] = top10["Exposure at Default (EUR M)"].apply(lambda x: f"{x:,.0f}")
            top10["% of Portfolio"] = top10["% of Portfolio"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(top10, use_container_width=True, hide_index=True)
            insight_box(f"Top-10 obligors represent <b>{data['conc']['top_10_concentration_ratio']:.0%}</b> of portfolio Exposure at Default. Single-name limit is 5%.")

        with st.expander("Data Quality Checks"):
            conn = sqlite3.connect(str(config.DB_PATH))
            checks = {
                "Drawn <= Commitment": conn.execute("SELECT COUNT(*) FROM facilities WHERE drawn_amount > commitment_amount * 1.01").fetchone()[0] == 0,
                "All ratings valid": conn.execute("SELECT COUNT(*) FROM obligors WHERE internal_rating NOT IN ('AAA','AA','A','BBB','BB','B','CCC','D')").fetchone()[0] == 0,
                "No orphan facilities": conn.execute("SELECT COUNT(*) FROM facilities f LEFT JOIN obligors o ON f.obligor_id=o.obligor_id WHERE o.obligor_id IS NULL").fetchone()[0] == 0,
                "Positive assets": conn.execute("SELECT COUNT(*) FROM obligors WHERE total_assets <= 0").fetchone()[0] == 0,
            }
            conn.close()
            for check, passed in checks.items():
                st.markdown(f"{'✅' if passed else '❌'} {check}")


# ══════════════════════════════════════════════════════════════════════════
# PAGE 2: RISK MODELS
# ══════════════════════════════════════════════════════════════════════════
elif page == "Risk Models":
    st.title("Risk Models")

    info_box(
        "<b>What are we looking at?</b> The three building blocks of credit risk measurement: "
        "<b>Probability of Default</b> (will the borrower fail to pay?), "
        "<b>Loss Given Default</b> (if they default, how much do we lose?), and "
        "<b>Exposure at Default</b> (how much are we owed when they default?). "
        "Together these produce: <b>Expected Loss = Probability of Default &times; Loss Given Default &times; Exposure at Default</b>."
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Probability of Default Model", "Loss Given Default Model", "Exposure at Default Model", "Single Obligor Calculator"])

    # ── PD TAB ─────────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Probability of Default")
        method_box(
            "<b>Methodology:</b> Logistic regression trained on 6 financial features. "
            "The model estimates the probability that an obligor defaults within 1 year. "
            "Features are standardised and the model uses balanced class weights to handle "
            "the low default rate (~3%). Final probabilities are blended 60/40 with rating-implied "
            "benchmarks to ensure calibration to long-run default rates."
            "<br><br>"
            "<b>Features:</b> Leverage Ratio, Interest Coverage, Current Ratio, "
            "Debt/EBITDA, Sector Risk Score, Rating Notch"
            "<br><br>"
            "<b>Formula:</b> Prob. of Default = &sigma;(&beta;<sub>0</sub> + &beta;<sub>1</sub>&middot;Leverage + "
            "&beta;<sub>2</sub>&middot;Interest Coverage + ... + &beta;<sub>6</sub>&middot;RatingNotch) where &sigma; is the logistic function."
        )

        pd_results = data["pd_results"]
        pd_model = data["pd_model"]

        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(pd_results, x="pd_score", nbins=50,
                               title="Probability of Default Distribution Across Portfolio",
                               labels={"pd_score": "Probability of Default", "count": "Obligors"},
                               color_discrete_sequence=[config.BRAND_RED])
            fig.update_layout(height=400, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
            insight_box("Most obligors cluster at low default probabilities (investment-grade). The right tail represents leveraged finance and distressed names.")

        with col2:
            if pd_model.roc_curve is not None:
                fpr, tpr, thresholds = pd_model.roc_curve
                # Thresholds array is one element shorter than fpr/tpr; pad to align
                thresholds_padded = np.append(thresholds, 0.0)
                hover_text = [
                    f"Cutoff: {t:.2%}<br>True Positive Rate: {tp:.2%}<br>False Positive Rate: {fp:.2%}"
                    for fp, tp, t in zip(fpr, tpr, thresholds_padded)
                ]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=fpr, y=tpr, name=f"Model (Area Under Curve={pd_model.auc:.3f})",
                    line=dict(color=config.BRAND_RED, width=2),
                    hoverinfo="text", text=hover_text))
                fig.add_trace(go.Scatter(
                    x=[0, 1], y=[0, 1], name="Random (Area Under Curve=0.500)",
                    line=dict(color="grey", dash="dash"),
                    hoverinfo="skip"))
                fig.update_layout(title="Receiver Operating Characteristic Curve — Discriminatory Power",
                                  xaxis_title="False Positive Rate", yaxis_title="True Positive Rate",
                                  height=400, margin=dict(t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
                insight_box(f"Area Under Curve of <b>{pd_model.auc:.3f}</b> indicates strong discriminatory power. "
                            f"The model clearly separates defaulters from non-defaulters. "
                            f"Regulatory minimum is typically 0.70.")

                with st.expander("How is this curve plotted?", expanded=False):
                    st.markdown("""The model gives every borrower a risk score between 0 and 1. To evaluate the model, we try every possible cutoff threshold — above the cutoff we label a borrower "will default," below it "won't default."

At each cutoff, we calculate two numbers:
- **True Positive Rate (y-axis):** out of all borrowers who actually defaulted, what percentage did the model correctly flag? "Positive" means the model predicts default. "True" means it was right.
- **False Positive Rate (x-axis):** out of all borrowers who did NOT default, what percentage did the model wrongly flag as defaulters? "False" means the model was wrong. "Positive" means it predicted default.

Each point on the red curve is one cutoff threshold. The bottom-left corner is a very strict cutoff (catches almost no one). The top-right corner is a very loose cutoff (flags everyone). A good model hugs the top-left corner — it catches most real defaulters without raising many false alarms.

The dashed diagonal line is what a random coin-flip model would produce. The further the red curve pulls away from this line, the better the model is at separating defaulters from non-defaulters.

**Area Under Curve = {auc_val:.3f}** means: if you randomly pick one actual defaulter and one non-defaulter from the portfolio, there is a **{auc_pct:.1f}%** chance the model assigns the defaulter a higher risk score. Regulators typically require a minimum of 0.70.""".format(auc_val=pd_model.auc, auc_pct=pd_model.auc * 100))

        # Metrics
        st.markdown("##### Model Performance")
        metrics = pd_model.get_metrics()
        st.metric("Area Under Curve", f"{metrics['auc']:.4f}")
        st.markdown(
            f"Ranges from 0.5 (random guessing) to 1.0 (perfect separation). "
            f"Our model scores **{metrics['auc']:.3f}** — it almost perfectly rank-orders borrowers by risk. "
            f"Regulatory minimum is typically 0.70."
        )

        # Feature importance
        st.markdown("##### Feature Importance (Logistic Regression Coefficients)")
        coefs = pd.DataFrame({
            "Feature": list(metrics["coefficients"].keys()),
            "Coefficient": list(metrics["coefficients"].values()),
        }).sort_values("Coefficient", key=abs, ascending=True)
        fig = px.bar(coefs, x="Coefficient", y="Feature", orientation="h",
                     color_discrete_sequence=[config.BRAND_RED])
        fig.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        insight_box("Rating notch is the strongest predictor (positive = higher default risk). "
                    "Interest coverage has a strong negative coefficient — higher coverage means lower default probability, as expected.")

        with st.expander("What do these coefficients mean?", expanded=False):
            st.markdown("""Each bar represents how much influence a financial feature has on the model's default prediction, and in which direction.

**Positive coefficient** = a higher value of this feature increases default probability:
- **Rating notch (~2.3):** The strongest predictor. This is the internal credit rating converted to a number (AAA=1, AA=2, ... CCC=7). A worse rating means higher default probability. The model heavily relies on the existing rating assessment.
- **Sector risk score (~0.3):** Riskier sectors (e.g., cyclical industries) slightly increase default probability.
- **Debt/EBITDA (~0.1):** More debt relative to earnings slightly increases risk — but the effect is small because this signal is already captured by rating notch and interest coverage.

**Negative coefficient** = a higher value of this feature decreases default probability:
- **Interest coverage (~-1.8):** Second strongest predictor. Higher interest coverage means the company earns much more than its interest payments — so it is less likely to default.
- **Current ratio (~-1.7):** More short-term assets versus short-term liabilities means better liquidity and lower default risk.
- **Leverage ratio (~-0.4):** This appears counterintuitive — higher leverage should mean more risk. But in logistic regression, when features are correlated with each other (multicollinearity), individual coefficients can shift. Leverage is already captured by rating notch and debt/EBITDA, so the model adjusts for the overlap.

**Key takeaway:** Rating grade and interest coverage are the two dominant predictors of default in this portfolio, which aligns with fundamental credit analysis principles.""")

        # Scorecard
        if pd_model.scorecard is not None:
            st.markdown("##### Probability of Default Scorecard — Rating-to-Default-Probability Mapping")
            sc = pd_model.scorecard.copy()
            sc["Prob. of Default Range"] = sc.apply(lambda r: f"{r['pd_lower']:.4%} – {r['pd_upper']:.4%}", axis=1)
            sc["Avg Prob. of Default"] = sc["avg_pd"].apply(lambda x: f"{x:.4%}")
            sc = sc.rename(columns={"rating_grade": "Grade", "count": "Obligors"})
            st.dataframe(sc[["Grade", "Prob. of Default Range", "Avg Prob. of Default", "Obligors"]], use_container_width=True, hide_index=True)

    # ── LGD TAB ────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### Loss Given Default")
        method_box(
            "<b>Methodology:</b> Collateral-based Loss Given Default estimation. Base loss rate is set by seniority "
            "(senior secured: 25%, senior unsecured: 45%, subordinated: 70%), then reduced by "
            "collateral value after applying regulatory haircuts. Confidence intervals are generated "
            "via beta distribution simulation (1,000 draws per facility)."
            "<br><br>"
            "<b>Downturn adjustment:</b> Loss Given Default is multiplied by 1.25x for downturn conditions, "
            "reflecting that recovery rates decline during recessions (depressed collateral values, "
            "illiquid secondary markets, longer workout timelines)."
        )

        st.markdown("##### Collateral Haircuts")
        haircut_df = pd.DataFrame([
            {"Collateral Type": "Real Estate", "Haircut": "30%", "Post-Haircut Value": "70% of appraised"},
            {"Collateral Type": "Equipment", "Haircut": "50%", "Post-Haircut Value": "50% of appraised"},
            {"Collateral Type": "Financial Assets", "Haircut": "15%", "Post-Haircut Value": "85% of appraised"},
            {"Collateral Type": "Unsecured", "Haircut": "100%", "Post-Haircut Value": "No recovery from collateral"},
        ])
        st.dataframe(haircut_df, use_container_width=True, hide_index=True)

        lgd_results = data["lgd_results"]
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(lgd_results, x="lgd", nbins=40,
                               title="Loss Given Default Distribution", labels={"lgd": "Loss Given Default", "count": "Facilities"},
                               color_discrete_sequence=[PALETTE[1]])
            fig.update_layout(height=400, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            lgd_box = lgd_results.copy()
            lgd_box["collateral_type"] = lgd_box["collateral_type"].str.replace("_", " ").str.title()
            lgd_box["seniority"] = lgd_box["seniority"].str.replace("_", " ").str.title()
            seniority_order = ["Senior Secured", "Senior Unsecured", "Subordinated"]
            seniority_colors = {"Senior Secured": config.BRAND_RED, "Senior Unsecured": "#3A7CA5", "Subordinated": "#444444"}
            collateral_order = sorted(lgd_box["collateral_type"].unique())

            fig = go.Figure()
            for sen in seniority_order:
                sub = lgd_box[lgd_box["seniority"] == sen]
                fig.add_trace(go.Box(
                    x=sub["collateral_type"], y=sub["lgd"],
                    name=sen, marker_color=seniority_colors[sen],
                    boxmean=False,
                ))
            fig.update_layout(
                title=dict(text="Loss Given Default by Collateral Type & Seniority", y=0.98),
                yaxis_title="Loss Given Default",
                xaxis_title="Collateral Type",
                xaxis=dict(categoryorder="array", categoryarray=collateral_order),
                boxmode="group",
                height=480, margin=dict(t=80, b=40, l=50, r=20),
                legend=dict(
                    title_text="Seniority", orientation="h",
                    yanchor="bottom", y=1.0, xanchor="center", x=0.5,
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

        insight_box(
            f"Mean Loss Given Default: <b>{lgd_results['lgd'].mean():.1%}</b> (through-the-cycle), "
            f"<b>{lgd_results['lgd_downturn'].mean():.1%}</b> (downturn). "
            f"Senior secured facilities with real estate collateral have the lowest loss rate (~5-15%), "
            f"while unsecured subordinated debt can exceed 70%."
        )

    # ── EAD TAB ────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### Exposure at Default")
        method_box(
            "<b>Methodology:</b> Exposure at Default = Drawn Amount + Credit Conversion Factor &times; Undrawn Amount. "
            "Credit Conversion Factors capture the tendency of borrowers to draw down "
            "credit lines before defaulting. Fully drawn facilities (term loans, bonds) have a factor of 100%. "
            "Revolvers at 75% reflects the empirical observation that ~75% of undrawn commitments "
            "are drawn prior to default."
        )

        st.markdown("##### Credit Conversion Factors")
        ccf_df = pd.DataFrame([
            {"Facility Type": k.replace("_", " ").title(), "Credit Conversion Factor": f"{v:.0%}",
             "Rationale": {
                 "term_loan": "Fully drawn at origination",
                 "revolver": "Capital Requirements Regulation Art. 166(8) — borrowers draw down before default",
                 "guarantee": "50% conversion for off-balance-sheet guarantees",
                 "trade_finance": "Short-term, self-liquidating — low conversion",
                 "bond": "Fixed obligation, fully funded",
                 "structured_note": "Fixed obligation, fully funded",
             }[k]}
            for k, v in config.CREDIT_CONVERSION_FACTORS.items()
        ])
        st.dataframe(ccf_df, use_container_width=True, hide_index=True)

        ead_results = data["ead_results"]
        col1, col2 = st.columns(2)
        with col1:
            ead_by_type = ead_results.groupby("facility_type").agg(
                drawn=("drawn_amount", "sum"), contingent=("contingent_exposure", "sum")).reset_index()
            fig = px.bar(ead_by_type.melt(id_vars="facility_type", var_name="Component", value_name="amount"),
                         x="facility_type", y="amount", color="Component",
                         title="Exposure at Default Breakdown: Drawn vs Contingent",
                         labels={"amount": "EUR M", "facility_type": "Facility Type"},
                         barmode="stack", color_discrete_sequence=[config.BRAND_RED, config.BRAND_DARK_GREY])
            fig.update_layout(height=400, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            total_drawn = ead_results["drawn_amount"].sum()
            total_contingent = ead_results["contingent_exposure"].sum()
            fig = px.pie(values=[total_drawn, total_contingent], names=["Drawn", "Contingent"],
                         title="Total Exposure at Default Composition", hole=0.45,
                         color_discrete_sequence=[config.BRAND_RED, config.BRAND_DARK_GREY])
            fig.update_layout(height=400, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        insight_box(
            f"Total Exposure at Default: <b>EUR {ead_results['ead'].sum()/1000:,.0f}B</b> "
            f"(EUR {total_drawn/1000:,.0f}B drawn + EUR {total_contingent/1000:,.0f}B contingent). "
            f"Revolvers contribute the most contingent exposure — undrawn commitments that could be drawn in a stress event."
        )

    # ── CALCULATOR TAB ─────────────────────────────────────────────────
    with tab4:
        st.markdown("### Single Obligor Risk Calculator")
        info_box("Enter hypothetical obligor characteristics to estimate Probability of Default, Loss Given Default, and Expected Loss. "
                 "This uses the trained models to produce a point estimate.")

        col1, col2 = st.columns(2)
        with col1:
            calc_rating = st.selectbox("Internal Rating", RATING_ORDER, index=3)
            calc_sector = st.selectbox("Sector", config.SECTORS, index=0)
            calc_leverage = st.slider("Leverage Ratio (Debt/Assets)", 0.10, 0.90, 0.40, 0.05)
            calc_icr = st.slider("Interest Coverage Ratio (EBITDA/Interest)", 0.5, 15.0, 4.0, 0.5)
        with col2:
            calc_current = st.slider("Current Ratio", 0.5, 3.0, 1.5, 0.1)
            calc_dte = st.slider("Debt/EBITDA", 0.5, 10.0, 3.5, 0.5)
            calc_seniority = st.selectbox("Seniority", config.SENIORITY_LEVELS)
            calc_collateral = st.selectbox("Collateral Type", config.COLLATERAL_TYPES)
            calc_exposure = st.number_input("Exposure (EUR M)", min_value=1, max_value=10000, value=100)

        if st.button("Calculate Risk", type="primary"):
            from models.pd_model import SECTOR_RISK_SCORES
            # PD estimate
            implied_pd = config.RATING_PD_MAP[calc_rating]
            sector_score = SECTOR_RISK_SCORES.get(calc_sector, 5)
            rating_notch = config.RATING_NOTCH[calc_rating]

            features = pd.DataFrame([{
                "leverage_ratio": calc_leverage, "interest_coverage": calc_icr,
                "current_ratio": calc_current, "debt_to_ebitda": calc_dte,
                "sector_risk_score": sector_score, "rating_notch": rating_notch,
            }])
            pd_model = data["pd_model"]
            model_pd = float(pd_model.predict(features)[0])
            blended_pd = 0.6 * model_pd + 0.4 * implied_pd
            blended_pd = max(0.0001, min(blended_pd, 0.9999))

            # LGD estimate
            base_lgd = config.SENIORITY_LGD_BASE[calc_seniority]
            haircut = config.COLLATERAL_HAIRCUTS[calc_collateral]
            if calc_collateral != "unsecured":
                coll_benefit = min(0.8 * (1 - haircut), 1.0) * 0.5
            else:
                coll_benefit = 0.0
            lgd_est = max(base_lgd - coll_benefit, 0.05)

            # EL
            el_est = blended_pd * lgd_est * calc_exposure

            st.markdown("---")
            st.markdown("##### Results")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Estimated Prob. of Default", f"{blended_pd:.2%}")
            r2.metric("Estimated Loss Given Default", f"{lgd_est:.1%}")
            r3.metric("Exposure", f"EUR {calc_exposure:,.0f}M")
            r4.metric("Expected Loss", f"EUR {el_est:,.2f}M")

            insight_box(
                f"A <b>{calc_rating}</b>-rated <b>{calc_sector}</b> obligor with leverage of {calc_leverage:.0%} "
                f"and {calc_seniority.replace('_',' ')} {calc_collateral.replace('_',' ')} exposure "
                f"has an estimated annual expected loss of <b>EUR {el_est:,.2f}M</b> on EUR {calc_exposure}M exposure."
            )


# ══════════════════════════════════════════════════════════════════════════
# PAGE 3: PORTFOLIO RISK
# ══════════════════════════════════════════════════════════════════════════
elif page == "Portfolio Risk":
    st.title("Portfolio Risk Analytics")

    info_box(
        "<b>What are we looking at?</b> Portfolio-level loss estimates. "
        "<b>Expected Loss</b> is the average annual loss — the cost of doing business. "
        "<b>Value at Risk</b> measures tail risk — the loss that would only be exceeded "
        "in extreme scenarios. <b>Risk-Weighted Assets</b> determines how much regulatory capital "
        "the bank must hold against this portfolio."
    )

    var_results = data["var_results"]
    el_df = data["el_df"]
    conc = data["conc"]
    rwa_df = data["rwa_df"]

    total_ead = el_df["ead"].sum()
    total_el = el_df["el"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected Loss", f"EUR {total_el:,.0f}M")
    c2.metric("Value at Risk (95%)", f"EUR {var_results['var_95']:,.0f}M")
    c3.metric("Value at Risk (99.9%)", f"EUR {var_results['var_999']:,.0f}M")
    c4.metric("Total Risk-Weighted Assets", f"EUR {rwa_df['rwa'].sum()/1000:,.0f}B")

    total_rwa = rwa_df['rwa'].sum()
    with st.expander("What do these four numbers mean and how do they connect?", expanded=False):
        st.markdown(f"""**Expected Loss (EUR {total_el:,.0f}M):** The average annual loss across the portfolio. This is Probability of Default x Loss Given Default x Exposure at Default, summed across all {len(el_df)} facilities. The bank prices this into the interest rates it charges borrowers — it is the predictable cost of lending.

**Value at Risk 95% (EUR {var_results['var_95']:,.0f}M):** If you ranked all possible loss outcomes from best to worst, this is the loss at the 95th percentile. In 95 out of 100 years, losses will be below this number.

**Value at Risk 99.9% (EUR {var_results['var_999']:,.0f}M):** The loss that would only be exceeded once in 1,000 years. This is the regulatory standard under Basel III — banks must hold enough capital to survive this level of loss.

**Total Risk-Weighted Assets (EUR {total_rwa/1000:,.0f}B):** Each facility's exposure is risk-weighted using the Basel formula — safe loans shrink, risky loans stay large. The sum is EUR {total_rwa/1000:,.0f}B. The bank must hold 8% of this as capital: 8% x EUR {total_rwa/1000:,.0f}B = approximately EUR {total_rwa*0.08/1000:,.0f}B. This is real equity that shareholders have invested and the bank cannot lend out.

**The chain:** EUR {total_ead/1000:,.0f}B total exposure → risk-weighted down to EUR {total_rwa/1000:,.0f}B → 8% capital requirement → EUR {total_rwa*0.08/1000:,.0f}B the bank must hold.""")

    st.markdown("---")

    with st.expander("Methodology — How is this calculated?", expanded=False):
        method_box(
            "<b>Expected Loss:</b> = &Sigma; Prob. of Default<sub>i</sub> &times; Loss Given Default<sub>i</sub> &times; Exposure at Default<sub>i</sub> "
            "— the probability-weighted average loss across all facilities."
            "<br><br>"
            "<b>Credit Value at Risk (Monte Carlo):</b> We simulate 10,000 portfolio loss scenarios using a "
            "<b>single-factor Gaussian copula</b> (Basel II approach). Each simulation draws a systematic "
            "market factor Z ~ N(0,1) and per-obligor idiosyncratic shocks. An obligor defaults if its "
            "latent asset value falls below the default threshold &Phi;<sup>-1</sup>(Prob. of Default). Asset correlation "
            "follows the Basel formula: R = 0.12 &times; f(Prob. of Default) + 0.24 &times; (1 - f(Prob. of Default))."
            "<br><br>"
            "<b>Risk-Weighted Assets (Internal Ratings-Based):</b> Basel III Foundation Internal Ratings-Based formula with 2.5-year maturity assumption and 1.06x scaling factor. "
            "Risk-Weighted Assets = K &times; 12.5 &times; Exposure at Default, where K is the per-facility capital requirement."
        )

    # Loss distribution with adjustable VaR
    st.markdown("### Loss Distribution")
    var_pct = st.slider("Value at Risk Confidence Level", 90.0, 99.9, 99.0, 0.1, format="%.1f%%")
    var_custom = float(np.percentile(var_results["loss_distribution"], var_pct))

    losses = var_results["loss_distribution"]
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=losses, nbinsx=80, name="Simulated Losses",
                               marker_color=config.BRAND_DARK_GREY, opacity=0.7))
    fig.add_vline(x=total_el, line_dash="dot", line_color="green",
                  annotation_text=f"Expected Loss: {total_el:,.0f}")
    fig.add_vline(x=var_custom, line_dash="dash", line_color=config.BRAND_RED,
                  annotation_text=f"Value at Risk ({var_pct:.1f}%): {var_custom:,.0f}")
    fig.update_layout(title=f"Credit Loss Distribution — 10,000 Monte Carlo Simulations",
                      xaxis_title="Portfolio Loss (EUR M)", yaxis_title="Frequency",
                      height=450, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
    insight_box(
        f"At the <b>{var_pct:.1f}%</b> confidence level, portfolio losses would not exceed "
        f"<b>EUR {var_custom:,.0f}M</b> in {var_pct:.1f}% of years. The distance between Expected Loss "
        f"(EUR {total_el:,.0f}M) and Value at Risk (EUR {var_custom:,.0f}M) is the <b>unexpected loss</b> "
        f"— this is what economic capital covers."
    )

    with st.expander("How does the Monte Carlo simulation work?", expanded=False):
        st.markdown("""The model runs 10,000 hypothetical scenarios for the portfolio. In each scenario:

1. It draws a random value for the economy (the **systematic factor Z**). A very negative Z represents a recession, a positive Z represents a good year.

2. For each borrower, it combines the economic factor with a random company-specific shock to produce an asset value. The formula is: **asset value = \u221aR \u00d7 Z + \u221a(1\u2212R) \u00d7 idiosyncratic shock**. R is the asset correlation — higher for safe borrowers (their defaults are mostly driven by recessions, R up to 0.36) and lower for risky borrowers (they can default for their own reasons, R as low as 0.12). These bounds (0.12 and 0.36) are prescribed by the Basel II regulator.

3. If a borrower's asset value falls below their **default threshold** (set by their Probability of Default), they default in that scenario. When Z is very negative, it drags down many borrowers simultaneously — this is how the model creates correlated defaults during recessions.

4. For every defaulting borrower, the loss is **Loss Given Default \u00d7 Exposure at Default**. These are summed to get the total portfolio loss for that scenario.

After 10,000 scenarios, the results are sorted. The 99.9th percentile is the Value at Risk — the loss exceeded in only 10 out of 10,000 scenarios. The average across all scenarios is the Expected Loss. The gap between the two is the **unexpected loss** — the bank's capital exists to absorb this gap.""")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Expected Loss by Sector")
        el_by_sector = el_df.groupby("sector")["el"].sum().sort_values(ascending=True).reset_index()
        fig = px.bar(el_by_sector, x="el", y="sector", orientation="h",
                     title="Expected Loss Contribution by Sector",
                     labels={"el": "Expected Loss (EUR M)", "sector": "Sector"},
                     color_discrete_sequence=[config.BRAND_RED])
        fig.update_layout(height=400, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Why do some sectors have higher expected loss?", expanded=False):
            st.markdown("""A sector having high expected loss does not necessarily mean it is the riskiest sector. Expected Loss = Probability of Default x Loss Given Default x Exposure at Default. So a sector can have high expected loss because the bank has lent a lot there (high exposure), because the borrowers are more likely to default (high Probability of Default), or because the collateral is weak (high Loss Given Default) — or some combination.

A risk manager would ask: is a sector high because we have large exposures there, or because borrowers in that sector are fundamentally riskier? That distinction matters for deciding whether to reduce exposure or improve collateral requirements.""")

    with col2:
        st.markdown("### Risk-Weighted Assets by Rating Grade")
        rwa_by_rating = rwa_df.groupby("internal_rating")["rwa"].sum().reindex(RATING_ORDER).fillna(0).reset_index()
        fig = px.bar(rwa_by_rating, x="internal_rating", y="rwa",
                     title="Risk-Weighted Assets by Rating",
                     labels={"rwa": "Risk-Weighted Assets (EUR M)", "internal_rating": "Rating"},
                     color_discrete_sequence=[PALETTE[3]])
        fig.update_layout(height=400, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("How are Risk-Weighted Assets calculated and why do BBB and BB dominate?", expanded=False):
            st.markdown("""For each facility: **Risk-Weighted Assets = K x 12.5 x Exposure at Default**, where K is the capital requirement percentage from the Basel Internal Ratings-Based formula.

K takes in the facility's Probability of Default, Loss Given Default, asset correlation, and maturity, and outputs a percentage. A safe facility (AAA, strong collateral) might have K = 1%. A risky facility (CCC, unsecured) might have K = 18%.

The **12.5 multiplier** is simply 1 divided by the 8% minimum capital ratio — it scales K so that 8% x Risk-Weighted Assets = required capital.

**BBB and BB dominate** not because they are the riskiest individual loans, but because they sit at the sweet spot of enough risk to generate a meaningful capital charge combined with enough obligors (80 BBB + 67 BB = almost 60% of the portfolio) to make the total large. AAA through A are tiny because their Probability of Default is so low that K is minimal. CCC and D are smaller because there are relatively few of them (10 and 25 obligors).

**The practical insight:** most of the bank's capital is consumed by the middle of the credit spectrum. A risk manager looking to optimise capital usage would focus on this BBB-BB bucket — could some of those borrowers be upgraded through better structuring or additional collateral?""")

    st.markdown("---")
    st.markdown("### Concentration Risk")
    info_box(
        "Concentration risk arises when too much exposure is held in a single name, sector, or geography. "
        "The <b>Herfindahl-Hirschman Index</b> measures this: Index = &Sigma;(share<sub>i</sub>)<sup>2</sup>. "
        "Index = 1.0 means 100% concentrated in one entity. Index < 0.10 is well-diversified."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Sector Herfindahl-Hirschman Index", f"{conc['hhi_sector']:.4f}", conc['hhi_sector_classification'])
    c2.metric("Top-10 Obligor Share", f"{conc['top_10_concentration_ratio']:.1%}")
    c3.metric("Single-Name Breaches (>5%)", str(conc['single_name_breaches']))

    with st.expander("How is the Herfindahl-Hirschman Index calculated?", expanded=False):
        st.markdown(f"""Take each sector's share of total exposure as a decimal (e.g. if Energy is 15% of the portfolio, its share is 0.15). Square each share and add them all up.

**Example** — if exposure is perfectly spread across 8 sectors (12.5% each): Index = 8 x (0.125\u00b2) = 0.125.
If one sector dominates at 80%: Index is driven by 0.80\u00b2 = 0.64 — highly concentrated.

- Below **0.10** = well diversified
- **0.10 to 0.18** = moderate concentration
- Above **0.25** = highly concentrated
- **1.0** = everything in one sector

**Top-10 Obligor Share** shows whether a small number of borrowers hold a disproportionate amount of risk. At {conc['top_10_concentration_ratio']:.0%}, the 10 largest borrowers out of {el_df['obligor_id'].nunique()} account for nearly a quarter of total exposure.

**Single-Name Breaches** check whether any individual borrower exceeds 5% of total portfolio exposure. {conc['single_name_breaches']} breaches means {"no single borrower could cause outsized damage on its own" if conc['single_name_breaches'] == 0 else "some borrowers exceed the concentration limit"}.""")


# ══════════════════════════════════════════════════════════════════════════
# PAGE 4: MIGRATION & STRESS TESTING
# ══════════════════════════════════════════════════════════════════════════
elif page == "Migration & Stress Testing":
    st.title("Rating Migration & Stress Testing")

    info_box(
        "<b>What are we looking at?</b> Credit quality doesn't stay static — obligors get upgraded, "
        "downgraded, or default over time. The <b>transition matrix</b> shows the probability of "
        "moving between rating grades in one year. <b>Stress testing</b> asks: what happens to our "
        "portfolio if the economy deteriorates — how much do losses increase?"
    )

    migration = data["migration"]
    stress = data["stress"]

    tab1, tab2 = st.tabs(["Rating Migration", "Stress Testing"])

    with tab1:
        method_box(
            "<b>Transition Matrix:</b> An 8&times;8 matrix where each cell (i,j) shows the probability "
            "of an obligor rated i at the start of the year being rated j at year-end. "
            "Calibrated to long-run Moody's/S&P historical averages. Row D (Default) is an <b>absorbing state</b> — "
            "once defaulted, the obligor stays in default. Rows sum to 100%."
        )

        col1, col2 = st.columns(2)
        with col1:
            matrix = migration["matrix"]
            fig = px.imshow(matrix.values, x=RATING_ORDER, y=RATING_ORDER,
                            text_auto=".1%", color_continuous_scale="RdYlGn_r",
                            title="1-Year Rating Transition Probabilities",
                            labels={"x": "To Rating", "y": "From Rating", "color": "Probability"})
            fig.update_layout(height=500, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
            insight_box("Diagonal = probability of staying at the same rating. Off-diagonal = migration probability. "
                        "Read row-wise: a BBB obligor has ~85% chance of staying BBB, ~8% of moving to BB, ~0.3% of defaulting.")

        with col2:
            cum_def = migration["cumulative_defaults"].drop("D")
            fig = go.Figure()
            for rating in cum_def.index:
                fig.add_trace(go.Scatter(
                    x=[int(c.replace("Y", "")) for c in cum_def.columns],
                    y=cum_def.loc[rating].values, name=rating, mode="lines+markers"))
            fig.update_layout(title="Cumulative Default Rate by Rating",
                              xaxis_title="Horizon (Years)", yaxis_title="Cumulative Probability of Default",
                              yaxis_tickformat=".1%", height=500, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
            insight_box("CCC-rated obligors have ~23% chance of defaulting within 1 year and ~62% within 5 years. "
                        "AAA obligors: <0.01% at 1 year. This is why rating is the primary risk differentiator.")

        st.markdown("##### Average Time to Default")
        ttd = migration["avg_time_to_default"]
        fig = px.bar(x=ttd.index, y=ttd.values, title="Expected Years to Default by Starting Rating",
                     labels={"x": "Rating", "y": "Years"},
                     color_discrete_sequence=[config.BRAND_RED])
        fig.update_layout(height=300, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        method_box(
            "<b>Stress Testing Framework:</b> Three European Banking Authority-style macroeconomic scenarios are applied to the portfolio. "
            "Each scenario shocks macro variables (GDP, unemployment, interest rates), which transmit to credit risk via:<br>"
            "1. <b>GDP shock</b> &rarr; direct Probability of Default multiplier<br>"
            "2. <b>Unemployment shock</b> &rarr; sector-specific default probability adjustment (e.g., Consumer & Real Estate most affected)<br>"
            "3. <b>Rate shock</b> &rarr; interest coverage degradation &rarr; default probability increase<br>"
            "4. <b>Collateral value shock</b> &rarr; Loss Given Default increase (real estate hit hardest)"
        )

        st.markdown("##### Scenario Parameters")
        scenario_params = pd.DataFrame([
            {"Scenario": "Baseline", "GDP Growth": "+1.8%", "Unemployment": "6.5%",
             "Rate Change": "+0 basis points", "Default Prob. Multiplier": "1.0x", "Collateral Shock": "0%"},
            {"Scenario": "Adverse", "GDP Growth": "-1.2%", "Unemployment": "9.0%",
             "Rate Change": "+200 basis points", "Default Prob. Multiplier": "1.8x", "Collateral Shock": "-15%"},
            {"Scenario": "Severely Adverse", "GDP Growth": "-3.5%", "Unemployment": "12.0%",
             "Rate Change": "+400 basis points", "Default Prob. Multiplier": "3.0x", "Collateral Shock": "-30%"},
        ])
        st.dataframe(scenario_params, use_container_width=True, hide_index=True)

        st.markdown("##### Results")
        comparison = stress["_comparison"]
        st.dataframe(comparison, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            colors = {"baseline": "green", "adverse": "orange", "severely_adverse": "red"}
            for key in ["baseline", "adverse", "severely_adverse"]:
                if key in stress and "loss_distribution" in stress[key]:
                    fig.add_trace(go.Histogram(x=stress[key]["loss_distribution"],
                                               name=stress[key]["scenario"], opacity=0.5, nbinsx=60,
                                               marker_color=colors[key]))
            fig.update_layout(title="Stressed Loss Distributions (Overlay)",
                              xaxis_title="Portfolio Loss (EUR M)", yaxis_title="Frequency",
                              barmode="overlay", height=450, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            scenarios = ["Baseline", "Adverse", "Severely Adverse"]
            els = [stress[k]["total_el_stressed"] for k in ["baseline", "adverse", "severely_adverse"]]
            vars99 = [stress[k]["var_999_stressed"] for k in ["baseline", "adverse", "severely_adverse"]]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=scenarios, y=els, name="Expected Loss", marker_color=config.BRAND_RED))
            fig.add_trace(go.Bar(x=scenarios, y=vars99, name="Value at Risk 99.9%", marker_color=config.BRAND_DARK_GREY))
            fig.update_layout(title="Capital Impact by Scenario", yaxis_title="EUR M",
                              barmode="group", height=450, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        severe = stress["severely_adverse"]
        warning_box(
            f"Under the <b>severely adverse scenario</b> (GDP -3.5%, unemployment 12%), "
            f"expected loss increases from EUR {stress['baseline']['total_el_stressed']:,.0f}M to "
            f"<b>EUR {severe['total_el_stressed']:,.0f}M (+{severe['el_increase_pct']:.0f}%)</b>. "
            f"Average Probability of Default rises to {severe['avg_pd_stressed']:.1%} and average Loss Given Default to {severe['avg_lgd_stressed']:.0%}. "
            f"Value at Risk (99.9%) reaches EUR {severe['var_999_stressed']:,.0f}M — "
            f"the bank would need significant capital buffers to absorb this."
        )


# ══════════════════════════════════════════════════════════════════════════
# PAGE 5: SQL EXPLORER
# ══════════════════════════════════════════════════════════════════════════
elif page == "SQL Explorer":
    st.title("SQL Explorer")
    info_box(
        "Run pre-built analytical queries directly against the portfolio database. "
        "Each query is designed for a specific risk management use case — "
        "select one below to see the results and underlying SQL."
    )

    sql_files = sorted(glob.glob(str(config.SQL_DIR / "*.sql")))
    query_map = {}
    for f in sql_files:
        content = Path(f).read_text()
        # Extract description from SQL comment header
        desc_match = re.search(r"--\s*={5,}\n--\s*(.+?)\n--\s*={5,}\n--\s*(.+?)(?:\n--)", content, re.DOTALL)
        name = Path(f).stem
        title = name.replace("_", " ").title()
        description = ""
        if desc_match:
            title = desc_match.group(1).strip()
            description = desc_match.group(2).strip().lstrip("- ")
        query_map[name] = {"path": f, "title": title, "description": description, "sql": content}

    selected = st.selectbox("Select Query", list(query_map.keys()),
                            format_func=lambda x: f"{query_map[x]['title']}")

    if selected:
        q = query_map[selected]
        if q["description"]:
            st.caption(q["description"])

        with st.expander("View SQL", expanded=False):
            st.code(q["sql"], language="sql")

        conn = sqlite3.connect(str(config.DB_PATH))
        try:
            df = pd.read_sql(q["sql"], conn)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"{len(df)} rows returned")
        except Exception as e:
            st.error(f"Query error: {e}")
        finally:
            conn.close()
