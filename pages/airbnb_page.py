"""
Airbnb Price Prediction Page
============================

This Streamlit module renders the main Airbnb pricing interface of the app.
It provides a complete prediction workflow including:

- Sidebar inputs for listing characteristics
- ML-based nightly price and cleaning cost predictions
- Monthly revenue estimation based on occupancy rates
- Interactive choropleth map of predicted prices across all Paris Arrondissements
- Price impact breakdown (baseline → quality → location)
- Clean UI sections: Summary, Map Analysis, Contribution Breakdown

All business logic (ML, KPIs, feature engineering) is handled in computations.py.
This file focuses solely on user interaction, layout, visualization, and UI logic.

No prediction logic is implemented here.
"""




import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from login import load_data
from computations import (
    run_computations_airbnb,
    predict_all_arrondissement_prices,
    calculate_price_impact_kpis,
    label_to_amenity_col,
    airbnb_confidence_interval,
)
from utils.constants import INSEE_MAP, ARRONDISSEMENT_NAMES


def fmt(num: float | int) -> str:
    """Format numbers with thousands separator 1'000 style."""
    return f"{num:,.0f}".replace(",", "'")


def _inject_minimal_styles():
    """Inject basic CSS styles for headings and cards."""
    st.markdown(
        """
        <style>
        .big-title { font-size: 36px; font-weight: 800; margin-bottom: 0.25rem; }
        .subtitle { color: #6b7280; margin-top: -0.25rem; }
        .card {
            border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; background: #ffffff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        .pill {
            display:inline-block; padding:2px 8px; border-radius:999px;
            background:#eef2ff; color:#4338ca; font-size:12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_city_coords() -> dict[str, tuple[float, float]]:
    """Return center coordinates for supported cities."""
    return {
        "Paris": (48.8566, 2.3522),
        "Vienna": (48.2082, 16.3738),
        "Berlin": (52.5200, 13.4050),
        "Zurich": (47.3769, 8.5417),
    }


def airbnb_page():
    """Render the Airbnb price prediction dashboard."""
    # ------------------------------------------------------------------
    # GeoJSON loading
    # ------------------------------------------------------------------
    geojson_data = None
    GEOJSON_FEATURE_ID_KEY = "properties.c_arinsee"

    try:
        geojson_path = "data/paris.geojson"
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
    except FileNotFoundError:
        st.error(f"Error: paris.geojson not found at expected path: {geojson_path}. Map cannot be rendered.")
    except json.JSONDecodeError:
        st.error("Error: Could not decode paris.geojson. Check file format.")
    except Exception as e:
        st.error(f"An unexpected error occurred during GeoJSON loading: {e}")

    # ------------------------------------------------------------------
    # Load user profile and defaults
    # ------------------------------------------------------------------
    username = st.session_state.get("username")
    all_users = load_data()
    user_profile = all_users.get(username, {}) if username else {}

    arr_default = int(user_profile.get("arrondissement", 1))
    bed_default = int(user_profile.get("bedrooms", 1))
    bath_default = int(user_profile.get("bathrooms", 1))
    host_list_default = int(user_profile.get("host_listings_count", 0))
    host_verified_default = bool(user_profile.get("host_identity_verified", False))
    host_superhost_default = bool(user_profile.get("host_is_superhost", False))

    room_type_options = ["Entire home/apt", "Private room", "Shared room", "Hotel room"]
    saved_room_type = user_profile.get("room_type", "Entire home/apt")

    # Amenities options from ML feature map
    amenities_options = list(label_to_amenity_col.keys())
    user_amenities = user_profile.get("amenities", []) or []

    # Normalize saved amenities to valid options
    normalized_amenities = []
    for a in user_amenities:
        if a in amenities_options:
            normalized_amenities.append(a)
        else:
            for opt in amenities_options:
                if opt.lower() == a.lower():
                    normalized_amenities.append(opt)
                    break

    default_amenities = normalized_amenities

    # ------------------------------------------------------------------
    # Sidebar default values stored in session_state
    # ------------------------------------------------------------------
    sidebar_defaults = {
        "sb_city": "Paris",
        "sb_arrondissement": arr_default,
        "sb_bedrooms": bed_default,
        "sb_bathrooms": bath_default,
        "sb_host_listings_count": host_list_default,
        "sb_host_identity_verified": host_verified_default,
        "sb_room_type": saved_room_type,
        "sb_host_is_superhost": host_superhost_default,
        "sb_amenities": default_amenities,
    }

    # Handle reset request before widgets are created
    if st.session_state.get("sb_reset_requested", False):
        for k, v in sidebar_defaults.items():
            st.session_state[k] = v
        st.session_state["sb_reset_requested"] = False

    # Initialize any missing keys (first run)
    for k, v in sidebar_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ------------------------------------------------------------------
    # Styling and header
    # ------------------------------------------------------------------
    _inject_minimal_styles()

    st.markdown('<div class="big-title">Airbnb Price Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Data-driven pricing for optimal profitability</div>', unsafe_allow_html=True)
    st.divider()

    # ------------------------------------------------------------------
    # Sidebar inputs (listing details)
    # ------------------------------------------------------------------
    with st.sidebar:
        st.header("Listing details")

        city = st.selectbox("City", ["Paris", "Vienna", "Berlin", "Zurich"], key="sb_city")
        arrondissement = st.number_input(
            "Arrondissement", min_value=1, max_value=20, key="sb_arrondissement"
        )

        colA, colB = st.columns(2)
        with colA:
            bedrooms = st.number_input(
                "Bedrooms", min_value=1, max_value=10, key="sb_bedrooms"
            )
            bathrooms = st.number_input(
                "Bathrooms", min_value=1, max_value=10, key="sb_bathrooms"
            )
            host_is_superhost = st.checkbox("Host is Superhost", key="sb_host_is_superhost")

        with colB:
            room_type = st.selectbox(
                "Property type", room_type_options, key="sb_room_type"
            )
            host_listings_count = st.number_input(
                "Host Listings Count", min_value=0, max_value=50, key="sb_host_listings_count"
            )
            host_identity_verified = st.checkbox(
                "Host Identity Verified", key="sb_host_identity_verified"
            )

        st.subheader("Amenities")
        amenities = st.multiselect(
            "Choose amenities", amenities_options, key="sb_amenities"
        )

        if st.button("Reset to your default values"):
            st.session_state["sb_reset_requested"] = True
            st.rerun()

        user_sidebar_data = {
            "host_is_superhost": host_is_superhost,
            "host_listings_count": host_listings_count,
            "host_identity_verified": host_identity_verified,
            "bathrooms": bathrooms,
            "bedrooms": bedrooms,
            "arrondissement": arrondissement,
            "room_type": room_type,
            "amenities": amenities,
        }

        # ------------------------------------------------------------------
        # Run ML computations (Airbnb + heatmap + KPIs)
        # ------------------------------------------------------------------
        run_computations_airbnb(user_sidebar_data)

        try:
            df_map_prices = predict_all_arrondissement_prices(user_sidebar_data)
            st.session_state["df_map_prices"] = df_map_prices
        except Exception as e:
            st.warning(f"Could not run all Arrondissement predictions: {e}")
            st.session_state["df_map_prices"] = None

        pred_price_per_night = st.session_state.get("user_price_prediction", 0)
        pred_cleaning_cost = st.session_state.get("user_cleaning_cost_prediction", 0)

        try:
            impact_kpis = calculate_price_impact_kpis(user_sidebar_data, pred_price_per_night)
            st.session_state["impact_kpis"] = impact_kpis
        except Exception as e:
            st.error(f"Could not calculate price impact KPIs: {e}")
            st.session_state["impact_kpis"] = None

        # ------------------------------------------------------------------
        # Revenue computation (occupancy-based)
        # ------------------------------------------------------------------
        try:
            data_arrondissement_occupancy = pd.read_csv("data/occupancy_arrondissement.csv")
            city_median_occupancy = data_arrondissement_occupancy["Occupancy in percent"].median()
            st.session_state["city_median_occupancy"] = city_median_occupancy

            arrondissement_user = int(arrondissement)
            occ_series = data_arrondissement_occupancy.loc[
                data_arrondissement_occupancy["Arrondissement"] == arrondissement_user,
                "Occupancy in percent",
            ]

            if not occ_series.empty:
                occupation = occ_series.iloc[0] / 100.0
            else:
                occupation = 0.5
                st.warning(
                    "Occupancy data missing for the selected Arrondissement. Using default 50%."
                )

        except FileNotFoundError:
            st.error(
                "Occupancy data file (occupancy_arrondissement.csv) not found. Using default 50%."
            )
            occupation = 0.5
        except Exception as e:
            st.error(f"Error reading occupancy data: {e}")
            occupation = 0.5

        prediction_monthly_revenue_user = pred_price_per_night * 30 * occupation
        number_of_monthly_cleanings = (30 * occupation) / 4.8
        prediction_cleaning_costs_per_month_user = number_of_monthly_cleanings * pred_cleaning_cost
        prediction_net_income_user = (
            prediction_monthly_revenue_user - prediction_cleaning_costs_per_month_user
        )

        st.session_state["prediction_net_income_user"] = prediction_net_income_user
        st.session_state["prediction_monthly_revenue_user"] = prediction_monthly_revenue_user
        st.session_state["prediction_cleaning_costs_per_month_user"] = (
            prediction_cleaning_costs_per_month_user
        )
        st.session_state["occupation_rate"] = occupation

    # ------------------------------------------------------------------
    # Main content: Tabs
    # ------------------------------------------------------------------
    tab_summary, tab_map_analysis, tab_price_breakdown = st.tabs(
        ["Prediction Summary", "Location & Map", "Price Contribution Breakdown"]
    )

    # ------------------------------------------------------------------
    # TAB 1: Prediction Summary
    # ------------------------------------------------------------------
    with tab_summary:
        prediction_net_income_user = st.session_state.get("prediction_net_income_user", 0)
        prediction_monthly_revenue_user = st.session_state.get(
            "prediction_monthly_revenue_user", 0
        )
        prediction_cleaning_costs_per_month_user = st.session_state.get(
            "prediction_cleaning_costs_per_month_user", 0
        )

        # Price per night card
        st.markdown(
            '<div class="card" style="background: #333; color: white;">',
            unsafe_allow_html=True,
        )
        st.subheader("📈 Price per Night")

        # Quartile-based RMSE interval
        price_low, price_high = airbnb_confidence_interval(float(pred_price_per_night))
        low = max(0, int(price_low))
        high = max(low + 1, int(price_high))

        col_price1, col_price2 = st.columns(2)
        col_price1.metric("Suggested nightly rate", f"€{pred_price_per_night}")
        col_price2.metric("Competitive range", f"€{low} - €{high}")

        range_max = high
        target_value = pred_price_per_night

        fig_price = go.Figure()
        fig_price.add_trace(
            go.Bar(
                y=["Price"],
                x=[range_max],
                orientation="h",
                marker=dict(color="rgba(107, 114, 128, 0.2)"),
                name="Competitive Range",
            )
        )
        fig_price.add_trace(
            go.Bar(
                y=["Price"],
                x=[target_value],
                orientation="h",
                marker=dict(color="#E57370"),
                name="Suggested Rate",
                width=0.6,
            )
        )
        fig_price.add_shape(
            type="line",
            x0=low,
            x1=low,
            y0=-0.5,
            y1=0.5,
            line=dict(color="darkgray", width=2, dash="dot"),
        )
        fig_price.add_shape(
            type="line",
            x0=high,
            x1=high,
            y0=-0.5,
            y1=0.5,
            line=dict(color="darkgray", width=2, dash="dot"),
        )
        fig_price.update_layout(
            barmode="overlay",
            height=150,
            xaxis=dict(range=[0, range_max * 1.1], title="Price (€)"),
            yaxis=dict(showticklabels=False),
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
        )
        st.plotly_chart(fig_price, use_container_width=True)

        # Net Monthly Income card
        st.markdown(
            '<div class="card" style="background: #333; color: white;">',
            unsafe_allow_html=True,
        )
        st.subheader("💰 Net Monthly Income")

        # Compute income range based on nightly RMSE interval
        price_low, price_high = airbnb_confidence_interval(float(pred_price_per_night))

        # Revenue extremes
        revenue_low = price_low * 30 * occupation
        revenue_high = price_high * 30 * occupation

        # Cleaning costs scale with occupancy exactly like main prediction
        cleanings_low = (30 * occupation) / 4.8 #avg cleaning every 4.8 night --> avg stay duration used in model
        cleanings_high = cleanings_low  # same frequency, cost per clean stable

        cleaning_costs_low = cleanings_low * pred_cleaning_cost
        cleaning_costs_high = cleaning_costs_low  # same logic as above

        # Calculate net income bounds
        low_net_income = int(revenue_low - cleaning_costs_low)
        high_net_income = int(revenue_high - cleaning_costs_high)


        col_net1, col_net2 = st.columns([1.5, 2])
        col_net1.markdown(f"## €{fmt(prediction_net_income_user)}")
        col_net2.metric(
            "Potential range", f"€{fmt(low_net_income)} - €{fmt(high_net_income)}"
        )

        st.markdown("</div>", unsafe_allow_html=True)

        breakdown_data = {
            "Metric": ["Gross Revenue", "Cleaning Costs", "Net Income"],
            "Value (€)": [
                fmt(prediction_monthly_revenue_user),
                f"-{fmt(prediction_cleaning_costs_per_month_user)}",
                f"**{fmt(prediction_net_income_user)}**",
            ],
        }
        st.table(pd.DataFrame(breakdown_data))
        st.caption(f"*Estimated monthly cleaning cost per cleaning: €{pred_cleaning_cost}")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # TAB 2: Location & Map
    # ------------------------------------------------------------------
    with tab_map_analysis:
        map_price_df = st.session_state.get("df_map_prices")
        arrondissement_user_num = int(arrondissement)
        occupation = st.session_state.get("occupation_rate", 0.5)
        city_selected = st.session_state.get("sb_city", "Paris")
        coords_dict = _get_city_coords()
        coords = coords_dict.get(city_selected, coords_dict["Paris"])

        arrondissement_insee_code = str(INSEE_MAP.get(arrondissement_user_num, 75101))

        st.markdown(
            '<div class="card" style="background: #242424; color: white;">',
            unsafe_allow_html=True,
        )
        st.subheader("Map & Price Analysis")

        if geojson_data and map_price_df is not None:
            # Add human-readable arrondissement names if missing
            if "Arrondissement_Name" not in map_price_df.columns:
                map_price_df = map_price_df.copy()
                map_price_df["Arrondissement_Name"] = map_price_df["Arrondissement_Number"].map(
                    ARRONDISSEMENT_NAMES
                )

            fig_map = px.choropleth_mapbox(
                map_price_df,
                geojson=geojson_data,
                locations="Arrondissement_Code",
                featureidkey=GEOJSON_FEATURE_ID_KEY,
                color="Avg_Price_Apt",
                color_continuous_scale="Reds",
                range_color=(
                    map_price_df["Avg_Price_Apt"].min() * 0.9,
                    map_price_df["Avg_Price_Apt"].max() * 1.1,
                ),
                mapbox_style="carto-positron",
                zoom=10.5,
                center={"lat": coords[0], "lon": coords[1]},
                opacity=0.8,
                hover_name="Arrondissement_Name",
                hover_data={
                    "Arrondissement_Code": False,
                    "Arrondissement_Name": False,
                    "Arrondissement_Number": True,
                    "Avg_Price_Apt": ":.0f€",
                },
            )

            # Highlight selected arrondissement
            target_df = map_price_df[
                map_price_df["Arrondissement_Code"] == arrondissement_insee_code
            ]
            if not target_df.empty:
                highlight_trace = px.choropleth_mapbox(
                    target_df,
                    geojson=geojson_data,
                    locations="Arrondissement_Code",
                    featureidkey=GEOJSON_FEATURE_ID_KEY,
                    color_discrete_sequence=["#E57370"],
                    mapbox_style="carto-positron",
                    zoom=10.5,
                    center={"lat": coords[0], "lon": coords[1]},
                    opacity=0.01,
                ).data[0]

                highlight_trace.marker.line.width = 3
                highlight_trace.marker.line.color = "white"
                fig_map.add_trace(highlight_trace)

            fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=500)
            fig_map.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig_map, use_container_width=True)
            st.caption(
                f"The map displays the predicted nightly rate for your listing type in every Arrondissement, "
                f"highlighting your selected Arrondissement {arrondissement}."
            )
        else:
            st.warning("Cannot display interactive heatmap. Check GeoJSON file and price data.")
            fallback_df = pd.DataFrame([{"lat": coords[0], "lon": coords[1]}])
            st.map(fallback_df, zoom=11)

        st.markdown("</div>", unsafe_allow_html=True)

        # Neighborhood performance card
        st.markdown(
            '<div class="card" style="background: #242424; color: white;">',
            unsafe_allow_html=True,
        )
        st.subheader("Neighborhood Performance")

        accent_color = "#E57370"
        background_color = "#331818"

        st.markdown(
            f"""
            <div style="
                background-color: {background_color};
                color: {accent_color};
                padding: 10px;
                border-radius: 5px;
                border: 1px solid {background_color};
                font-size: 16px;
                margin-bottom: 20px;
            ">
                The calculated occupancy rate for Arrondissement <strong>{arrondissement}</strong>
                is <strong>{occupation * 100:.1f}%</strong> (used for income prediction).
            </div>
            """,
            unsafe_allow_html=True,
        )

        city_median_occupancy = st.session_state.get("city_median_occupancy", 65)
        comparison_df = pd.DataFrame(
            {
                "Category": ["Your Arrondissement", "City Median"],
                "Occupancy (%)": [occupation * 100, city_median_occupancy],
            }
        )

        fig_occupancy = px.bar(
            comparison_df,
            x="Category",
            y="Occupancy (%)",
            color="Category",
            color_discrete_map={
                "Your Arrondissement": "#E57370",
                "City Median": "#808080",
            },
            text="Occupancy (%)",
            title="Occupancy Rate vs. City Median",
        )
        fig_occupancy.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_occupancy.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0, 0, 0, 0)",
            paper_bgcolor="rgba(0, 0, 0, 0)",
            font=dict(color="white"),
            title_font_color="white",
            height=500,
        )

        st.plotly_chart(fig_occupancy, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # TAB 3: Price Contribution Breakdown
    # ------------------------------------------------------------------
    with tab_price_breakdown:
        st.markdown(
            '<div class="card" style="background: #242424; color: white;">',
            unsafe_allow_html=True,
        )
        st.subheader("Key Price Drivers")

        impact_kpis = st.session_state.get("impact_kpis")
        current_predicted_price = pred_price_per_night

        if impact_kpis:
            baseline_price = impact_kpis["baseline_price"]
            quality_impact = impact_kpis["quality_impact"]
            location_impact = impact_kpis["location_impact"]

            data_waterfall = {
                "x": [
                    "1. Baseline Price",
                    "2. Quality Premium",
                    "3. Location Impact",
                    "Final Price",
                ],
                "y": [
                    baseline_price,
                    quality_impact,
                    location_impact,
                    current_predicted_price,
                ],
                "measure": ["absolute", "relative", "relative", "total"],
            }

            fig_drivers = go.Figure(
                go.Waterfall(
                    name="Price Breakdown",
                    orientation="v",
                    x=data_waterfall["x"],
                    y=data_waterfall["y"],
                    measure=data_waterfall["measure"],
                    increasing={"marker": {"color": "#E57370"}},
                    decreasing={"marker": {"color": "#C70039"}},
                    totals={"marker": {"color": "#808080"}},
                    connector={"line": {"color": "#808080"}},
                    textposition="outside",
                    text=[f"{v}€" for v in data_waterfall["y"]],
                )
            )
            fig_drivers.update_layout(
                title="Price Contribution Breakdown",
                xaxis_title="",
                yaxis_title="Price (€)",
                showlegend=False,
                plot_bgcolor="rgba(0, 0, 0, 0)",
                paper_bgcolor="rgba(0, 0, 0, 0)",
                font=dict(color="white"),
                title_font_color="white",
                height=550,
            )

            st.plotly_chart(fig_drivers, use_container_width=True)
            st.markdown("---")

            st.markdown(
                f"""
                <h5 style='color: #E57370;'>Summary of Price Impact:</h5>
                <ul style='color: white;'>
                    <li>Your chosen <b>Features and Quality</b> add a premium of:
                        <b>€{fmt(quality_impact)}</b></li>
                    <li>Your <b>Arrondissement Location</b> adds/subtracts:
                        <b>€{fmt(abs(location_impact))}</b> (vs. median location)</li>
                    <li>The final predicted price is
                        <b>€{fmt(current_predicted_price)}</b>.</li>
                </ul>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning("Feature impact data could not be loaded. Please check model execution.")

        st.markdown("</div>", unsafe_allow_html=True)
