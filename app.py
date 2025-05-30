import json
import streamlit as st
import pandas as pd

# Load data
try:
    with open('connectors.json') as f:
        connectors_data = json.load(f)
except FileNotFoundError:
    st.error("Error: 'connectors.json' not found. Please make sure the file exists in the same directory.")
    st.stop()
except json.JSONDecodeError:
    st.error("Error: Could not decode 'connectors.json'. Please ensure it's a valid JSON file.")
    st.stop()

if not connectors_data:
    st.warning("No data found in 'connectors.json'.")
    df = pd.DataFrame()
else:
    df = pd.DataFrame(connectors_data)

# --- Precompute necessary columns ---
if not df.empty:
    df['pinout_table'] = df['pinout_table'].apply(lambda x: x if isinstance(x, list) else [])

    df['total_cavities'] = df['pinout_table'].apply(lambda pinouts: len(pinouts))
    df['num_connected_cavities'] = df['pinout_table'].apply(
        lambda pinouts: len([p for p in pinouts if p.get('Terminal Manufacturer') != 'unused' and p.get('Terminal Manufacturer') is not None])
    )
    df['num_unconnected_cavities'] = df['pinout_table'].apply(
        lambda pinouts: len([p for p in pinouts if p.get('Terminal Manufacturer') == 'unused'])
    )
    
    df['manufacturer'] = df['connector'].astype(str).str.split().str[0].fillna('')
    df['connector_part_number_full'] = df['connector'].fillna('') # Full connector string
    df['tesla_part_number_str'] = df['tesla_part_number'].fillna('')
    df['connector_body_color'] = df['color'].fillna('') # 'color' is the connector body color

    # --- Prepare predefined lists for selectboxes ---
    all_wire_colors = set()
    for pinout_list in df['pinout_table']:
        for pin in pinout_list:
            wc = pin.get('Wire Color')
            if wc and wc not in ['unused', '']:
                all_wire_colors.add(wc)
    PREDEFINED_WIRE_COLORS = sorted(list(all_wire_colors))
    PREDEFINED_WIRE_COLORS.insert(0, "ANY")

    all_connector_body_colors = sorted(list(set(c for c in df['connector_body_color'].unique() if c)))
    PREDEFINED_CONNECTOR_BODY_COLORS = sorted(list(all_connector_body_colors))
    PREDEFINED_CONNECTOR_BODY_COLORS.insert(0, "ANY")

else: # Handle empty DataFrame case for sliders and selectboxes
    df['total_cavities'] = pd.Series(dtype='int')
    df['num_unconnected_cavities'] = pd.Series(dtype='int')
    df['manufacturer'] = pd.Series(dtype='str')
    df['connector_part_number_full'] = pd.Series(dtype='str')
    df['tesla_part_number_str'] = pd.Series(dtype='str')
    df['connector_body_color'] = pd.Series(dtype='str')
    PREDEFINED_WIRE_COLORS = ["ANY"]
    PREDEFINED_CONNECTOR_BODY_COLORS = ["ANY"]


# --- Sidebar filters ---
st.sidebar.header("Connector Search Filters")

# Slider for Total Cavities
max_total_cav = int(df.total_cavities.max()) if not df.total_cavities.empty else 0
min_total_cav_filter, max_total_cav_filter = st.sidebar.slider(
    "Total number of cavities", 
    0, 
    max_total_cav, 
    (0, max_total_cav)
)

# Slider for Unconnected Cavities
max_unconn_cav = int(df.num_unconnected_cavities.max()) if not df.num_unconnected_cavities.empty else 0
min_unconn_cav_filter, max_unconn_cav_filter = st.sidebar.slider(
    "Number of unconnected cavities",
    0,
    max_unconn_cav,
    (0, max_unconn_cav)
)

manuf_filter = st.sidebar.text_input("Manufacturer (starts with, case-insensitive)")
tesla_pn_filter = st.sidebar.text_input("Tesla Part Number (contains, case-insensitive)")
connector_pn_filter = st.sidebar.text_input("Connector Part Number (contains in 'connector' field, case-insensitive)")

selected_body_color_filter = st.sidebar.selectbox("Connector Body Color", PREDEFINED_CONNECTOR_BODY_COLORS)

st.sidebar.markdown("---")
st.sidebar.subheader("Wire in Specific Cavity")
cavity_num_input = st.sidebar.text_input("Cavity #", "")
selected_wire_color_filter = st.sidebar.selectbox("Wire Color (for specific cavity)", PREDEFINED_WIRE_COLORS, key="specific_cavity_wire_color")

st.sidebar.markdown("---")
st.sidebar.subheader("Count of Specific Wire Color")
count_wire_color_to_filter = st.sidebar.selectbox("Wire Color (for count)", PREDEFINED_WIRE_COLORS, key="count_wire_color")
count_wire_color_target_quantity = st.sidebar.number_input("Exact quantity of this wire color", min_value=0, value=0, step=1)


# --- Apply filters ---
if not df.empty:
    mask = pd.Series([True] * len(df))

    mask &= (df.total_cavities.between(min_total_cav_filter, max_total_cav_filter))
    mask &= (df.num_unconnected_cavities.between(min_unconn_cav_filter, max_unconn_cav_filter))

    if manuf_filter:
        mask &= df.manufacturer.str.upper().str.startswith(manuf_filter.upper())
    
    if tesla_pn_filter:
        mask &= df.tesla_part_number_str.str.upper().str.contains(tesla_pn_filter.upper())

    if connector_pn_filter:
        # Search within the full 'connector' string (which includes manufacturer and part number)
        mask &= df.connector_part_number_full.str.upper().str.contains(connector_pn_filter.upper())

    if selected_body_color_filter != "ANY":
        mask &= (df.connector_body_color == selected_body_color_filter)

    if cavity_num_input and selected_wire_color_filter != "ANY":
        def check_wire_in_cavity(pinout_list, cavity_num, wire_color_val):
            if not pinout_list: return False
            for p in pinout_list:
                if p.get('Cavity') == cavity_num and p.get('Wire Color') == wire_color_val:
                    return True
            return False
        mask &= df['pinout_table'].apply(lambda pts: check_wire_in_cavity(pts, cavity_num_input, selected_wire_color_filter))

    if count_wire_color_to_filter != "ANY" and count_wire_color_target_quantity > 0:
        def count_specific_wires(pinout_list, color_to_count):
            if not pinout_list: return 0
            count = 0
            for p in pinout_list:
                if p.get('Wire Color') == color_to_count:
                    count += 1
            return count
        mask &= df['pinout_table'].apply(lambda pts: count_specific_wires(pts, count_wire_color_to_filter) == count_wire_color_target_quantity)
    
    filtered_df = df[mask]
else:
    filtered_df = df # Empty DataFrame

# --- Show results ---
st.header("Connector Search Results")
st.write(f"### {len(filtered_df)} connectors found")

if not filtered_df.empty:
    st.dataframe(filtered_df[[
        'name', 
        'connector', # Full connector string
        'total_cavities', 
        'num_unconnected_cavities',
        'num_connected_cavities',
        'manufacturer', 
        'connector_body_color',
        'tesla_part_number'
    ]])
else:
    st.write("No connectors match the current filters.")

st.sidebar.markdown("---")
st.sidebar.info("Tip: Clear filters or adjust ranges if you don't see expected results.")

# For debugging or viewing all data:
# if st.checkbox("Show all data (first 100 rows)"):
#    st.subheader("Raw Data Sample (first 100 rows)")
#    st.dataframe(df.head(100))
