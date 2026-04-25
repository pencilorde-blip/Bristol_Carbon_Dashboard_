import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# --- 1. RESEARCH PARAMETERS ---
st.set_page_config(page_title="Bristol Net-Zero Decision Suite", layout="wide")

TOTAL_POP = 472400
INTERCEPT = 520.0  

COEFFS = {
    'Domestic': -0.12, 'Industry_Business': 0.05, 'PETROL': 0.08,      
    'DIESEL': 0.10, 'Green_Transition': -5.5, 'Cycling_Percentage': -1.2,
    'Mid-year Population (thousands)': 0.05, 'Other local bus': -0.02
}

# --- 2. SIDEBAR NAVIGATION & UK POLICY PRESETS ---
st.sidebar.title("MSc Project Menu")
page = st.sidebar.radio("Navigation", ["Decision Model", "Policy Benchmarking"])

st.sidebar.header("UK Policy Presets")
preset = st.sidebar.selectbox(
    "Select Evidence-Based Strategy:",
    [
        "Manual Adjustment", 
        "Manchester: Bee Network (Bus/Active Focus)", 
        "Birmingham: CAZ (EV Focus)", 
        "Nottingham: Workplace Parking Levy (Transit Focus)",
        "London: ULEZ Expansion (Aggressive Mix)"
    ]
)

# Preset Logic
if preset == "Manchester: Bee Network (Bus/Active Focus)":
    d_active, d_bus, d_ev = 180000, 120000, 25
elif preset == "Birmingham: CAZ (EV Focus)":
    d_active, d_bus, d_ev = 120000, 80000, 65
elif preset == "Nottingham: Workplace Parking Levy (Transit Focus)":
    d_active, d_bus, d_ev = 130000, 180000, 20
elif preset == "London: ULEZ Expansion (Aggressive Mix)":
    d_active, d_bus, d_ev = 200000, 150000, 55
else: 
    d_active, d_bus, d_ev = 141720, 89756, 20

st.sidebar.header("Variable Controls")
active_pop = st.sidebar.slider("Active Travel (Walking/Cycling)", 0, TOTAL_POP, d_active)
max_bus = TOTAL_POP - active_pop
bus_pop = st.sidebar.slider("Public Transport (Bus/Rail)", 0, max_bus, min(d_bus, max_bus))
car_pop = TOTAL_POP - active_pop - bus_pop
st.sidebar.metric("Private Vehicles (Residual)", f"{car_pop:,}")
ev_percent = st.sidebar.slider("EV Adoption (% of Car Fleet)", 0, 100, d_ev)

# --- 3. MATH ENGINE ---
ice_users_units = (car_pop * (1 - (ev_percent / 100))) / 1000
cycling_val = (active_pop / TOTAL_POP) * 100
bus_units = bus_pop / 1000
pop_units = TOTAL_POP / 1000

# Breakdown Components for the Donut Chart
domestic_comp = 150.0 
industry_comp = 200.0 * COEFFS['Industry_Business']
transport_comp = (ice_users_units * COEFFS['PETROL']) + (ice_users_units * COEFFS['DIESEL']) + (bus_units * COEFFS['Other local bus'])
pop_growth_impact = (pop_units * COEFFS['Mid-year Population (thousands)'])

raw_prediction = (350.0 * COEFFS['Domestic']) + industry_comp + transport_comp + (50.0 * COEFFS['Green_Transition']) + (cycling_val * COEFFS['Cycling_Percentage']) + pop_growth_impact + INTERCEPT
predicted_2030 = max(20.0, raw_prediction)
reduction = ((441.7 - predicted_2030) / 441.7) * 100

# --- 4. PAGE 1: DECISION MODEL (Trend Only) ---
if page == "Decision Model":
    st.title("Bristol Transport Decarbonization Suite")
    st.markdown(f"**Current Strategy Simulation:** {preset}")

    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("2030 Forecast", f"{predicted_2030:.1f} kt", delta=f"{predicted_2030-441.7:.1f}", delta_color="inverse")
    k2.metric("Target Reduction", f"{reduction:.1f}%")
    k3.metric("Sustainable Mode Share", f"{((active_pop + bus_pop)/TOTAL_POP*100):.1f}%")

    # Chart: The Trend Line
    st.subheader("Emission Projection Pathway")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=[2013, 2015, 2017, 2019, 2021, 2023], y=[523.5, 515.0, 496.0, 467.0, 454.9, 441.7], name="Historical", line=dict(color='#636EFA', width=3)))
    fig_line.add_trace(go.Scatter(x=[2023, 2030], y=[441.7, predicted_2030], name="Ridge Prediction", line=dict(color='#00CC96', width=5, dash='dot')))
    fig_line.add_hline(y=0, line_dash="dash", line_color="#EF553B")
    fig_line.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_line, use_container_width=True)

# --- 5. PAGE 2: POLICY BENCHMARKING (Analytics Focus) ---
else:
    st.title("Policy Benchmark Analysis")
    st.write("Validation and decomposition of the simulated 2030 emissions profile.")

    # Setting up two columns for side-by-side charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Regional Performance Comparison")
        benchmark_df = pd.DataFrame({
            'Policy Model': ['Your Scenario', 'London ULEZ', 'Nottingham WPL', 'Birmingham CAZ', 'Manchester Bee'],
            'Reduction %': [reduction, 28.4, 22.1, 19.5, 24.8]
        })
        # The Bar Chart
        st.plotly_chart(px.bar(benchmark_df, x='Policy Model', y='Reduction %', color='Policy Model'), use_container_width=True)

    with col_right:
        st.subheader("Forecast Source Breakdown")
        breakdown_data = pd.DataFrame({
            'Source': ['Transport (Car/Bus)', 'Industry/Business', 'Domestic Baseline', 'Pop. Growth Factor'],
            'Emissions (kt)': [max(0, transport_comp), industry_comp, domestic_comp, pop_growth_impact]
        })
        # The Donut Chart
        fig_donut = px.pie(breakdown_data, values='Emissions (kt)', names='Source', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_donut, use_container_width=True)

    st.info("💡 **MSc Analysis Note:** The 'Your Scenario' metrics are calculated dynamically using the Ridge Regression model weights calibrated for Bristol's socio-economic profile.")