import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.main { background: #0f1117; }

/* KPI cards */
.kpi-card {
    background: linear-gradient(135deg, #1e2130 0%, #252840 100%);
    border: 1px solid #2e3250;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(99,102,241,0.15);
}
.kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #f9fafb;
    font-family: 'DM Mono', monospace;
}
.kpi-sub {
    font-size: 12px;
    color: #10b981;
    margin-top: 4px;
}

/* Date banner */
.date-banner {
    background: linear-gradient(135deg, #1a1f35 0%, #1e2540 100%);
    border: 1px solid #2e3250;
    border-left: 4px solid #6366f1;
    border-radius: 12px;
    padding: 14px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 40px;
}
.date-banner-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 4px;
}
.date-banner-value {
    font-size: 16px;
    font-weight: 700;
    color: #a5b4fc;
    font-family: 'DM Mono', monospace;
}

/* Section headers */
.section-header {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #6366f1;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2130;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d0f1a !important;
    border-right: 1px solid #1e2130;
}
</style>
""", unsafe_allow_html=True)


# ── DB Connection ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    host     = "db31521.public.databaseasp.net"
    port     = 3306
    database = "db31521"
    username = "db31521"
    password = quote_plus(st.secrets["DB_PASSWORD"])
    return create_engine(f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}")


@st.cache_data(ttl=300)
def load_data(table_name: str) -> pd.DataFrame:
    engine = get_engine()
    df = pd.read_sql_table(table_name, engine)
    numeric_cols = ['Net_Cost', 'Net_Discount', 'Net_Sale', 'Net_Scheme']
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    if 'Date' in df.columns:
        df['Date']  = pd.to_datetime(df['Date'], errors='coerce')
        df['Month'] = df['Date'].dt.to_period('M').astype(str)
        df['Year']  = df['Date'].dt.year
    return df


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💊 Sales Analytics")
    st.markdown("---")

    table_name = st.text_input("Table Name", value="your_table_name",
                               help="Enter the exact MySQL table name")

    if st.button("🔄 Load / Refresh Data", use_container_width=True):
        st.cache_data.clear()

    st.markdown("---")
    st.markdown("### Filters")


# ── Load Data ───────────────────────────────────────────────────────────────────
try:
    df = load_data(table_name)
except Exception as e:
    st.error(f"❌ Could not load table **{table_name}**: {e}")
    st.info("👈 Enter a valid table name in the sidebar and click **Load Data**.")
    st.stop()


# ── Sidebar Filters ─────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Date Range ────────────────────────────────────────────────────────────
    if 'Date' in df.columns:
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        from_date = st.date_input("📅 From Date", value=min_date,
                                  min_value=min_date, max_value=max_date)
        to_date   = st.date_input("📅 To Date",   value=max_date,
                                  min_value=min_date, max_value=max_date)
    else:
        from_date = to_date = None

    # ── Region ───────────────────────────────────────────────────────────────
    if 'Region' in df.columns:
        regions = st.multiselect("Region", df['Region'].dropna().unique().tolist(),
                                 default=df['Region'].dropna().unique().tolist())
    else:
        regions = []

    # ── Unit Name ─────────────────────────────────────────────────────────────
    if 'Unit' in df.columns:
        units = st.multiselect("Unit Name", sorted(df['Unit'].dropna().unique().tolist()),
                               default=sorted(df['Unit'].dropna().unique().tolist()))
    else:
        units = []

    # ── Customer Type ─────────────────────────────────────────────────────────
    if 'Customer_Type' in df.columns:
        cx_types = st.multiselect("Customer Type", df['Customer_Type'].dropna().unique().tolist(),
                                  default=df['Customer_Type'].dropna().unique().tolist())
    else:
        cx_types = []

    # ── Month ─────────────────────────────────────────────────────────────────
    if 'Month' in df.columns:
        months = st.multiselect("Month", sorted(df['Month'].dropna().unique().tolist()),
                                default=sorted(df['Month'].dropna().unique().tolist()))
    else:
        months = []


# ── Apply Filters ───────────────────────────────────────────────────────────────
fdf = df.copy()

if from_date and to_date and 'Date' in fdf.columns:
    fdf = fdf[(fdf['Date'].dt.date >= from_date) & (fdf['Date'].dt.date <= to_date)]
if regions and 'Region' in fdf.columns:
    fdf = fdf[fdf['Region'].isin(regions)]
if units and 'Unit' in fdf.columns:
    fdf = fdf[fdf['Unit'].isin(units)]
if cx_types and 'Customer_Type' in fdf.columns:
    fdf = fdf[fdf['Customer_Type'].isin(cx_types)]
if months and 'Month' in fdf.columns:
    fdf = fdf[fdf['Month'].isin(months)]


# ── Helper ──────────────────────────────────────────────────────────────────────
def fmt(n):
    if abs(n) >= 1_000_000: return f"₹{n/1_000_000:.1f}M"
    if abs(n) >= 1_000_000:     return f"₹{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:         return f"₹{n/1_000:.1f}K"
    return f"₹{n:.0f}"


# ── Dashboard Header ──────────────────────────────────────────────────────────
st.markdown("## 📊 Sales Analytics Dashboard")

# ── Date Period Banner ────────────────────────────────────────────────────────
if from_date and to_date:
    st.markdown(f"""
    <div class="date-banner">
        <div>
            <div class="date-banner-label">📅 Reporting Period</div>
            <div class="date-banner-value">
                {from_date.strftime('%d %b %Y')} &nbsp;→&nbsp; {to_date.strftime('%d %b %Y')}
            </div>
        </div>
        <div>
            <div class="date-banner-label">📋 Total Records</div>
            <div class="date-banner-value">{len(fdf):,}</div>
        </div>
        <div>
            <div class="date-banner-label">🏢 Units Selected</div>
            <div class="date-banner-value">{len(units) if units else 'All'}</div>
        </div>
        <div>
            <div class="date-banner-label">🌍 Regions Selected</div>
            <div class="date-banner-value">{len(regions) if regions else 'All'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── KPI Row ───────────────────────────────────────────────────────────────────
total_sale     = fdf['Net_Sale'].sum()     if 'Net_Sale'     in fdf.columns else 0
total_cost     = fdf['Net_Cost'].sum()     if 'Net_Cost'     in fdf.columns else 0
total_discount = fdf['Net_Discount'].sum() if 'Net_Discount' in fdf.columns else 0
total_scheme   = fdf['Net_Scheme'].sum()   if 'Net_Scheme'   in fdf.columns else 0
profit         = total_sale - total_cost
gp_pct         = (profit / total_sale * 100) if total_sale else 0
dis_pct        = (total_discount / total_sale * 100) if total_sale else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
for col, label, value, sub in [
    (k1, "NET SALES",    fmt(total_sale),     ""),
    (k2, "NET COST",     fmt(total_cost),     ""),
    (k3, "DISCOUNT",     fmt(total_discount), f"{dis_pct:.2f}%"),
    (k4, "SCHEME",       fmt(total_scheme),   ""),
    (k5, "GROSS PROFIT", fmt(profit),         ""),
    (k6, "GP %",         f"{gp_pct:.2f}%",   ""),
]:
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🌍 Region & State", "📅 Trend", "🏢 Unit & ASM", "👥 Customer"])

COLORS = px.colors.qualitative.Vivid

# ── Tab 1: Region & State ─────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        if 'Region' in fdf.columns:
            rdf = fdf.groupby('Region', as_index=False)['Net_Sale'].sum().sort_values('Net_Sale', ascending=False)
            fig = px.bar(rdf, x='Region', y='Net_Sale', color='Region',
                         title='Region-wise Net Sales', color_discrete_sequence=COLORS,
                         template='plotly_dark', text_auto='.2s')
            fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor='rgba(0,0,0,0)', title_font_size=14)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if 'Region' in fdf.columns:
            fig2 = px.pie(rdf, names='Region', values='Net_Sale',
                          title='Region Share', hole=0.45,
                          color_discrete_sequence=COLORS, template='plotly_dark')
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', title_font_size=14)
            st.plotly_chart(fig2, use_container_width=True)

    if 'State' in fdf.columns:
        sdf = fdf.groupby('State', as_index=False)['Net_Sale'].sum().sort_values('Net_Sale', ascending=False).head(15)
        fig3 = px.bar(sdf, x='Net_Sale', y='State', orientation='h',
                      color='Net_Sale', color_continuous_scale='Tealrose',
                      title='Top 15 States by Net Sales', template='plotly_dark', text_auto='.2s')
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           title_font_size=14, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig3, use_container_width=True)

    if 'Region' in fdf.columns:
        st.markdown("<div class='section-header'>Region Summary Table</div>", unsafe_allow_html=True)
        rtbl = fdf.groupby('Region').agg(
            Sales=('Net_Sale','sum'), Discount=('Net_Discount','sum'),
            Cost=('Net_Cost','sum'), Scheme=('Net_Scheme','sum')
        ).reset_index()
        rtbl['Profit'] = rtbl['Sales'] - rtbl['Cost']
        rtbl['GP %']   = (rtbl['Profit'] / rtbl['Sales'] * 100).round(2)
        rtbl['Dis %']  = (rtbl['Discount'] / rtbl['Sales'] * 100).round(2)
        for col in ['Sales','Discount','Cost','Scheme','Profit']:
            rtbl[col] = rtbl[col].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(rtbl, use_container_width=True, hide_index=True)


# ── Tab 2: Trend ──────────────────────────────────────────────────────────────
with tab2:
    if 'Month' in fdf.columns:
        mdf = fdf.groupby('Month', as_index=False).agg(
            Net_Sale=('Net_Sale','sum'), Net_Discount=('Net_Discount','sum'),
            Net_Cost=('Net_Cost','sum')
        ).sort_values('Month')
        mdf['Profit'] = mdf['Net_Sale'] - mdf['Net_Cost']

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=mdf['Month'], y=mdf['Net_Sale'], mode='lines+markers',
                                  name='Net Sale', line=dict(color='#6366f1', width=3),
                                  marker=dict(size=8)))
        fig4.add_trace(go.Scatter(x=mdf['Month'], y=mdf['Profit'], mode='lines+markers',
                                  name='Profit', line=dict(color='#10b981', width=2, dash='dot'),
                                  marker=dict(size=6)))
        fig4.add_trace(go.Bar(x=mdf['Month'], y=mdf['Net_Discount'], name='Discount',
                              marker_color='#f59e0b', opacity=0.5, yaxis='y2'))
        fig4.update_layout(
            title='Month-wise Sales Trend', template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis2=dict(overlaying='y', side='right', showgrid=False),
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            title_font_size=14
        )
        st.plotly_chart(fig4, use_container_width=True)

        if 'Region' in fdf.columns:
            mrdf = fdf.groupby(['Month','Region'], as_index=False)['Net_Sale'].sum().sort_values('Month')
            fig5 = px.line(mrdf, x='Month', y='Net_Sale', color='Region',
                           title='Month-wise Sales by Region', markers=True,
                           color_discrete_sequence=COLORS, template='plotly_dark')
            fig5.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               title_font_size=14)
            st.plotly_chart(fig5, use_container_width=True)


# ── Tab 3: Unit & ASM ─────────────────────────────────────────────────────────
with tab3:
    c1, c2 = st.columns(2)

    with c1:
        if 'Unit' in fdf.columns:
            udf = fdf.groupby('Unit', as_index=False)['Net_Sale'].sum().sort_values('Net_Sale', ascending=False).head(15)
            fig6 = px.bar(udf, x='Net_Sale', y='Unit', orientation='h',
                          color='Net_Sale', color_continuous_scale='Blues',
                          title='Top 15 Units by Net Sales', template='plotly_dark', text_auto='.2s')
            fig6.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               yaxis={'categoryorder':'total ascending'}, title_font_size=14)
            st.plotly_chart(fig6, use_container_width=True)

    with c2:
        if 'Area_Sales_Man' in fdf.columns:
            adf = fdf.groupby('Area_Sales_Man', as_index=False)['Net_Sale'].sum().sort_values('Net_Sale', ascending=False).head(15)
            fig7 = px.bar(adf, x='Net_Sale', y='Area_Sales_Man', orientation='h',
                          color='Net_Sale', color_continuous_scale='Greens',
                          title='Top 15 ASMs by Net Sales', template='plotly_dark', text_auto='.2s')
            fig7.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               yaxis={'categoryorder':'total ascending'}, title_font_size=14)
            st.plotly_chart(fig7, use_container_width=True)

    if 'Unit' in fdf.columns:
        st.markdown("<div class='section-header'>Unit Summary Table</div>", unsafe_allow_html=True)
        utbl = fdf.groupby('Unit').agg(
            Sales=('Net_Sale','sum'), Discount=('Net_Discount','sum'),
            Cost=('Net_Cost','sum')
        ).reset_index().sort_values('Sales', ascending=False)
        utbl['Profit'] = utbl['Sales'] - utbl['Cost']
        utbl['GP %']   = (utbl['Profit'] / utbl['Sales'] * 100).round(2)
        utbl['Dis %']  = (utbl['Discount'] / utbl['Sales'] * 100).round(2)
        for col in ['Sales','Discount','Cost','Profit']:
            utbl[col] = utbl[col].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(utbl, use_container_width=True, hide_index=True)


# ── Tab 4: Customer ───────────────────────────────────────────────────────────
with tab4:
    c1, c2 = st.columns(2)

    with c1:
        if 'Customer_Type' in fdf.columns:
            ctdf = fdf.groupby('Customer_Type', as_index=False)['Net_Sale'].sum().sort_values('Net_Sale', ascending=False)
            fig8 = px.pie(ctdf, names='Customer_Type', values='Net_Sale',
                          title='Customer Type Share', hole=0.4,
                          color_discrete_sequence=COLORS, template='plotly_dark')
            fig8.update_layout(paper_bgcolor='rgba(0,0,0,0)', title_font_size=14)
            st.plotly_chart(fig8, use_container_width=True)

    with c2:
        if 'Customer_Type' in fdf.columns:
            fig9 = px.bar(ctdf, x='Customer_Type', y='Net_Sale', color='Customer_Type',
                          title='Customer Type - Net Sales', color_discrete_sequence=COLORS,
                          template='plotly_dark', text_auto='.2s')
            fig9.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
                               plot_bgcolor='rgba(0,0,0,0)', title_font_size=14)
            st.plotly_chart(fig9, use_container_width=True)

    if 'Customer' in fdf.columns:
        st.markdown("<div class='section-header'>Top 20 Customers</div>", unsafe_allow_html=True)
        cust = fdf.groupby(['Customer','Customer_Type'], as_index=False).agg(
            Sales=('Net_Sale','sum'), Discount=('Net_Discount','sum')
        ).sort_values('Sales', ascending=False).head(20)
        cust['Dis %']    = (cust['Discount'] / cust['Sales'] * 100).round(2)
        cust['Sales']    = cust['Sales'].apply(lambda x: f"₹{x:,.0f}")
        cust['Discount'] = cust['Discount'].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(cust, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<p style='text-align:center;color:#374151;font-size:12px'>Sales Analytics Dashboard • Powered by Streamlit + Plotly</p>",
            unsafe_allow_html=True)