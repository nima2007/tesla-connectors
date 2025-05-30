import json
import streamlit as st
import pandas as pd
import glob

# --- Load Connector Metadata ---
@st.cache_data # Cache this to avoid reloading on every interaction
def load_connector_metadata():
    connector_files_metadata = []
    file_pattern = "connectors_*.json" 

    for filename in glob.glob(file_pattern):
        if "old_" in filename.lower(): # Heuristic to skip files like 'old_connectors_prog-13.json'
            st.info(f"Skipping file with 'old_' in name: {filename}")
            continue
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                # Ensure all required top-level keys are present
                if 'model' in data and 'prog_id' in data and 'sop' in data and 'connectors' in data:
                    connector_files_metadata.append({
                        "model": data["model"],
                        "prog_id": data["prog_id"],
                        "sop": data["sop"],
                        "filename": filename,
                        "build_information": data.get("build_information", [])
                    })
                else:
                    st.warning(f"Skipping {filename}: missing one or more required keys ('model', 'prog_id', 'sop', 'connectors') in JSON structure.")
        except json.JSONDecodeError:
            st.error(f"Error decoding JSON from {filename}. Please ensure it's valid.")
        except Exception as e:
            st.error(f"An unexpected error occurred while processing {filename}: {e}")
    return connector_files_metadata

# --- Load Specific Connector Data ---
@st.cache_data # Cache data for each specific connector file
def load_specific_connector_data(filename):
    try:
        with open(filename, 'r') as f:
            full_file_data = json.load(f)
            # Return only the 'connectors' list, or the whole data if needed elsewhere
            return full_file_data.get("connectors", [])
    except FileNotFoundError:
        st.error(f"Error: File '{filename}' not found.")
        return []
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from '{filename}'. Ensure it is valid.")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while loading data from {filename}: {e}")
        return []

all_connectors_metadata = load_connector_metadata()

if not all_connectors_metadata:
    st.error("No valid connector data files found or loaded. "
             "Please ensure 'connectors_ModelX_prog-Y.json' files exist, "
             "are valid JSON, and contain 'model', 'prog_id', 'sop', and 'connectors' keys.")
    st.stop()

st.sidebar.header("Select Vehicle Program")

models = sorted(list(set(meta["model"] for meta in all_connectors_metadata)))
selected_model = st.sidebar.selectbox("1. Select Model", models, index=0 if models else -1) # Select first model by default if available

selected_sop_display = None
target_filename = None
connectors_data = [] # Initialize as empty list; this will hold the list of connector dicts
current_build_info = []

if selected_model:
    metadata_for_selected_model = [meta for meta in all_connectors_metadata if meta["model"] == selected_model]
    
    def sop_sort_key(sop_string):
        if isinstance(sop_string, str) and sop_string.startswith("SOP") and sop_string[3:].isdigit():
            return int(sop_string[3:])
        return float('inf') # Place non-standard or non-string SOPs at the end

    # Create a list of unique SOP display names (including build info) for the selected model, sorted correctly
    sops_for_model_display_tuples = [] # Will store (display_string, original_sop, original_prog_id)
    seen_sops_for_selectbox = set() # To track unique SOPs based on their original string (e.g. "SOP1")
    
    # Sort metadata by SOP and then prog_id to ensure consistent ordering
    sorted_metadata_for_model = sorted(metadata_for_selected_model, key=lambda x: (sop_sort_key(x["sop"]), x["prog_id"]))

    for meta in sorted_metadata_for_model:
        # We want one entry per unique SOP string (like "SOP1", "SOP2")
        # The build_information from the *first* encountered prog_id for that SOP will be used for display.
        # This assumes that if multiple prog_ids share an SOP string, their build info is either identical
        # or the first one encountered by sort order is representative.
        # For this version, the display_text in the selectbox will be just the SOP identifier.
        if meta["sop"] not in seen_sops_for_selectbox:
            display_text = meta['sop'] # Just the SOP name, e.g., "SOP1"
            # We still store the original prog_id to uniquely identify the file later
            sops_for_model_display_tuples.append((display_text, meta["sop"], meta["prog_id"]))
            seen_sops_for_selectbox.add(meta["sop"])
            
    # sops_display_strings will now be just ["SOP1", "SOP2", ...]
    sops_display_strings = [item[0] for item in sops_for_model_display_tuples]

    if not sops_display_strings:
        st.sidebar.warning(f"No SOPs found for model {selected_model}.")
    else:
        # selected_sop_display_string is now just the SOP identifier like "SOP1"
        selected_sop_display_string = st.sidebar.selectbox( 
            f"2. Select Program (SOP) for {selected_model}", 
            sops_display_strings, 
            index=0 if sops_display_strings else -1 
        )

    # Display static list of ALL SOPs and their build info for the selected MODEL within an expander
    st.sidebar.markdown("---")
    with st.sidebar.expander(f"View All SOPs & Build Info for {selected_model}", expanded=False):

        temp_seen_sops = set()
        for meta_item in sorted_metadata_for_model: # Iterate through all metadata for the model, sorted by SOP
            if meta_item["sop"] not in temp_seen_sops: # Display each SOP string only once
                st.markdown(f"**{meta_item['sop']}**") # Display SOP name boldly
                build_info_lines = meta_item.get("build_information", [])
                if build_info_lines:
                    for info_line in build_info_lines:
                        st.caption(info_line) # Each build info on its own line as caption
                else:
                    st.caption("No build information available.")
                temp_seen_sops.add(meta_item["sop"])
    st.sidebar.markdown("---")


if selected_model and selected_sop_display_string: # This is now just "SOP1", "SOP2", etc.
    # Find the tuple that matches the selected SOP string.
    selected_sop_tuple = next((item for item in sops_for_model_display_tuples if item[0] == selected_sop_display_string), None)

    if selected_sop_tuple:
        original_sop_val = selected_sop_tuple[1] 
        target_prog_id = selected_sop_tuple[2]   

        matching_meta = next((meta for meta in sorted_metadata_for_model 
                              if meta["model"] == selected_model and 
                                 meta["sop"] == original_sop_val and 
                                 meta["prog_id"] == target_prog_id), None) 
        
        if matching_meta:
            selected_sop_display = original_sop_val 
        else:
            st.error(f"Internal error: Could not re-find data for selected SOP. Model: {selected_model}, SOP: {original_sop_val}, Prog ID: {target_prog_id}")
            st.stop()
    else:
        st.error(f"Internal error: Could not parse selected SOP. Selected string: {selected_sop_display_string}")
        st.stop()

    if matching_meta: 
        target_filename = matching_meta["filename"]
        # current_build_info is still loaded here from matching_meta["build_information"]
        # but it's not explicitly displayed again, as the static list above covers it.
        current_build_info = matching_meta["build_information"] 
    else:
        st.error(f"Internal error: Could not find data file for Model: {selected_model}, SOP: {selected_sop_display_string}")
        st.stop()

# Load connector data from the determined file using the cached function
if target_filename:
    connectors_data = load_specific_connector_data(target_filename)
    if not connectors_data: # If loading failed or returned empty, connectors_data might be an empty list
        # Error messages are handled within load_specific_connector_data,
        # but we might want to stop or show a specific message here if it's critical.
        # For now, if connectors_data is empty, the downstream logic will handle it (e.g., show "No connector data loaded").
        pass
else:
    # Handle cases where a file couldn't be determined (target_filename is None)
    if selected_model and selected_sop_display:
        st.warning("Could not determine the data file for the selected model and program.")
    elif selected_model:
        st.info("Please select a Program (SOP) to load connector data.")
    else:
        st.info("Please select a Model to begin.")
    # connectors_data remains an empty list, df will be empty.

# --- DataFrame Creation and Initial Processing ---
# This section now uses the dynamically loaded `connectors_data` (which is a list of connector dictionaries)
if not connectors_data: # Check if the list of connectors itself is empty or not populated
    st.warning(f"No connector data loaded. Please make a selection or check data files.")
    df = pd.DataFrame()
else:
    df = pd.DataFrame(connectors_data) # connectors_data is already the list of connector objects
    # Ensure image_urls column exists and handles missing lists/NaN values
    if 'image_urls' not in df.columns:
        df['image_urls'] = [[] for _ in range(len(df))] 
    else:
        df['image_urls'] = df['image_urls'].apply(lambda x: x if isinstance(x, list) else [])

# --- Precompute necessary columns ---
if not df.empty:
    df['pinout_table'] = df['pinout_table'].apply(lambda x: x if isinstance(x, list) else [])

    # Optimized total_cavities calculation
    df['total_cavities'] = df['pinout_table'].str.len()
    df['num_connected_cavities'] = df['pinout_table'].apply(
        lambda pinouts: len([p for p in pinouts if p.get('Terminal Manufacturer') != 'unused' and p.get('Terminal Manufacturer') is not None])
    )
    df['num_unconnected_cavities'] = df['pinout_table'].apply(
        lambda pinouts: len([p for p in pinouts if p.get('Terminal Manufacturer') == 'unused'])
    )
    
    df['manufacturer'] = df['connector'].astype(str).str.split().str[0].fillna('')
    df['connector_part_number_full'] = df['connector'].fillna('')
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
    df['num_connected_cavities'] = pd.Series(dtype='int')
    df['num_unconnected_cavities'] = pd.Series(dtype='int')
    df['manufacturer'] = pd.Series(dtype='str')
    df['connector_part_number_full'] = pd.Series(dtype='str')
    df['tesla_part_number_str'] = pd.Series(dtype='str')
    df['connector_body_color'] = pd.Series(dtype='str')
    df['image_urls'] = pd.Series(dtype=object) # Ensure schema for empty df
    PREDEFINED_WIRE_COLORS = ["ANY"]
    PREDEFINED_CONNECTOR_BODY_COLORS = ["ANY"]

# --- Helper function for counting specific wires ---
def count_specific_wires(pinout_list, color_to_count):
    if not pinout_list: return 0
    count = 0
    for p in pinout_list:
        if p.get('Wire Color') == color_to_count:
            count += 1
    return count
# --- End Helper function ---

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

# Slider for Connected Cavities
max_conn_cav = int(df.num_connected_cavities.max()) if not df.num_connected_cavities.empty else 0
min_conn_cav_filter, max_conn_cav_filter = st.sidebar.slider(
    "Number of connected cavities",
    0,
    max_conn_cav, # Use max_total_cav here as connected can be up to total
    (0, max_conn_cav) # Default to full range
)

# Slider for Unconnected Cavities
max_unconn_cav = int(df.num_unconnected_cavities.max()) if not df.num_unconnected_cavities.empty else 0
min_unconn_cav_filter, max_unconn_cav_filter = st.sidebar.slider(
    "Number of unconnected cavities",
    0,
    max_unconn_cav, # Use max_total_cav here as unconnected can be up to total
    (0, max_unconn_cav) # Default to full range
)

tesla_pn_filter = st.sidebar.text_input("Tesla Part Number (contains, case-insensitive)")
combined_manuf_connector_pn_filter = st.sidebar.text_input("Manuf. / Connector P/N (contains, case-insensitive)")


selected_body_color_filter = st.sidebar.selectbox("Connector Body Color", PREDEFINED_CONNECTOR_BODY_COLORS)

# "Wire in Specific Cavity" section removed

st.sidebar.markdown("---")
st.sidebar.subheader("Count of Specific Wire Color 1")
count_wire_color_to_filter_1 = st.sidebar.selectbox(
    "Wire Color (for count 1)", 
    PREDEFINED_WIRE_COLORS, 
    key="count_wire_color_1"
)
min_count_filter_1, max_count_filter_1 = st.sidebar.slider(
    "Quantity range for wire color 1",
    0,
    max_total_cav, 
    (0, max_total_cav),
    key="count_wire_color_slider_1"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Count of Specific Wire Color 2")
count_wire_color_to_filter_2 = st.sidebar.selectbox(
    "Wire Color (for count 2)", 
    PREDEFINED_WIRE_COLORS, 
    key="count_wire_color_2"
)
min_count_filter_2, max_count_filter_2 = st.sidebar.slider(
    "Quantity range for wire color 2",
    0,
    max_total_cav,
    (0, max_total_cav),
    key="count_wire_color_slider_2"
)

# --- Apply filters ---
if not df.empty:
    mask = pd.Series([True] * len(df))

    mask &= (df.total_cavities.between(min_total_cav_filter, max_total_cav_filter))
    mask &= (df.num_connected_cavities.between(min_conn_cav_filter, max_conn_cav_filter))
    mask &= (df.num_unconnected_cavities.between(min_unconn_cav_filter, max_unconn_cav_filter))

    if tesla_pn_filter:
        mask &= df.tesla_part_number_str.str.upper().str.contains(tesla_pn_filter.upper())

    if combined_manuf_connector_pn_filter:
        search_term_upper = combined_manuf_connector_pn_filter.upper()
        mask &= (
            df.manufacturer.str.upper().str.contains(search_term_upper) | 
            df.connector_part_number_full.str.upper().str.contains(search_term_upper)
        )

    if selected_body_color_filter != "ANY":
        mask &= (df.connector_body_color == selected_body_color_filter)

    # "Wire in Specific Cavity" filter logic removed

    # Filter for Count of Specific Wire Color 1
    if count_wire_color_to_filter_1 != "ANY":
        actual_counts_1 = df['pinout_table'].apply(lambda pts: count_specific_wires(pts, count_wire_color_to_filter_1))
        mask &= (actual_counts_1 >= min_count_filter_1) & (actual_counts_1 <= max_count_filter_1)

    # Filter for Count of Specific Wire Color 2
    if count_wire_color_to_filter_2 != "ANY":
        actual_counts_2 = df['pinout_table'].apply(lambda pts: count_specific_wires(pts, count_wire_color_to_filter_2))
        mask &= (actual_counts_2 >= min_count_filter_2) & (actual_counts_2 <= max_count_filter_2)
    
    filtered_df = df[mask]
else:
    filtered_df = df

# --- Show results ---
st.header("Connector Search Results")
st.write(f"### {len(filtered_df)} connectors found")

if not filtered_df.empty:
    ITEMS_PER_PAGE = 10  # Number of items to display per page

    # Initialize page number in session state if it doesn't exist
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0
    
    # Reset page number if the number of filtered items changes (indicates new filter applied)
    if 'last_filtered_count' not in st.session_state or st.session_state.last_filtered_count != len(filtered_df):
        st.session_state.page_number = 0
    st.session_state.last_filtered_count = len(filtered_df)

    total_items = len(filtered_df)
    total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1 if total_items > 0 else 1
    
    # Ensure current page number is valid
    st.session_state.page_number = max(0, min(st.session_state.page_number, total_pages - 1))

    # --- Helper function for pagination controls ---
    def render_pagination_controls(current_page, total_pages_val, key_prefix):
        if total_pages_val <= 1:
            return

        nav_cols = st.columns([1, 2, 1])
        with nav_cols[0]:
            if st.button("Previous", key=f"{key_prefix}_prev_page") and current_page > 0:
                st.session_state.page_number -= 1
                st.rerun()
        with nav_cols[1]:
            st.write(f"Page {current_page + 1} of {total_pages_val}")
        with nav_cols[2]:
            if st.button("Next", key=f"{key_prefix}_next_page") and current_page < total_pages_val - 1:
                st.session_state.page_number += 1
                st.rerun()
    
    # --- Render pagination controls at the top ---
    render_pagination_controls(st.session_state.page_number, total_pages, "top")

    start_idx = st.session_state.page_number * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_df_view = filtered_df.iloc[start_idx:end_idx]

    for index, row in paginated_df_view.iterrows():
        st.subheader(row.get('name', 'N/A'))
        
        # Display textual details in two columns for better layout
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Connector:** {row.get('connector', 'N/A')}")
            st.write(f"**Tesla Part #:** {row.get('tesla_part_number_str', 'N/A')}")
            st.write(f"**Manufacturer:** {row.get('manufacturer', 'N/A')}")
        with col2:
            st.write(f"**Body Color:** {row.get('connector_body_color', 'N/A')}")
            st.write(f"**Total Cavities:** {row.get('total_cavities', 'N/A')}")
            st.write(f"**Connected Cavities:** {row.get('num_connected_cavities', 'N/A')}")
            st.write(f"**Unconnected Cavities:** {row.get('num_unconnected_cavities', 'N/A')}")

        # Display images
        image_urls = row.get('image_urls', []) 
        if image_urls: 
            st.write("**Images:**")
            num_img_display_cols = min(len(image_urls), 2) # Use at most 2 columns
            if num_img_display_cols > 0: # Ensure we have columns to create
                img_display_cols = st.columns(num_img_display_cols)
                for i, img_url in enumerate(image_urls):
                    with img_display_cols[i % num_img_display_cols]:
                        st.image(img_url, caption=f"Image {i+1}", use_container_width=True)
            else: # Fallback if somehow num_img_display_cols is 0 but image_urls is not empty (should not happen with min(len,2))
                 for i, img_url in enumerate(image_urls):
                    st.image(img_url, caption=f"Image {i+1}", use_container_width=True)


        st.markdown("---")
    
    # --- Render pagination controls at the bottom ---
    render_pagination_controls(st.session_state.page_number, total_pages, "bottom")

else:
    st.write("No connectors match the current filters.")

st.sidebar.markdown("---")
st.sidebar.info("Tip: Clear filters (refresh) or adjust ranges if you don't see expected results.")
