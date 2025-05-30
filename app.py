import json, streamlit as st
import pandas as pd

# Load data
connectors = json.load(open('connectors.json'))
df = pd.DataFrame(connectors)
df['num_cavities'] = df['pinout_table'].apply(lambda rows: len([r for r in rows if r['Terminal Manufacturer']!='unused']))
df['manufacturer'] = df['connector'].str.split().str[0].fillna('')

# Sidebar filters
st.sidebar.header("Filters")
min_cav, max_cav = st.sidebar.slider("Number of cavities", 0, int(df.num_cavities.max()), (0, int(df.num_cavities.max())))
manuf = st.sidebar.text_input("Manufacturer (prefix)")
cavity = st.sidebar.text_input("Cavity #", "")
color = st.sidebar.text_input("Wire color", "").upper()

# Apply filters
mask = (
    (df.num_cavities.between(min_cav, max_cav)) &
    df.manufacturer.str.upper().str.startswith(manuf.upper())
)
if cavity and color:
    mask &= df.pinout_table.apply(lambda pts: any(p['Cavity']==cavity and p['Wire Color']==color for p in pts))

# Show results
st.write(f"### {mask.sum()} connectors found")
st.dataframe(df[mask][['name','connector','num_cavities','manufacturer']])