#python -m streamlit run app.py
from pathlib import Path
import base64
import json
import re

import streamlit as st
import streamlit.components.v1 as components
import plotly.io as pio
import pandas as pd
import pygwalker as pyg


PROJECT_ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = PROJECT_ROOT / "main.ipynb"

st.set_page_config(
    page_title="PLOTTED GRAPHS",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: #f4f7fb; }
    .stApp { background: #101522; color: #e8edf5; }
    [data-testid="stSidebar"] { background: #080c15; }
    [data-testid="stSidebar"] * { color: #e8edf5; }
    .hero { border-bottom: 1px solid #2b3548; padding-bottom: 1.4rem; margin-bottom: 1.4rem; }
    .eyebrow { color: #f26b38; font-size: .72rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    .hero h1 { font-size: clamp(2rem, 4vw, 3.4rem); margin: .2rem 0 .35rem; }
    .hero p, .muted, .cell-meta, [data-testid="stCaptionContainer"] { color: #aeb9ca; }
    .cell-meta { font-size: .9rem; margin-bottom: 1rem; }
    div.stButton > button { text-align: left; background: #182236; color: #e8edf5; border: 1px solid #2b3a53; border-radius: 6px; margin-bottom: .25rem; }
    div.stButton > button:hover { background: #24324a; border-color: #f26b38; color: #ffffff; }
    [data-testid="stDivider"] { border-color: #2b3548; }
    [data-testid="stAlert"] { background: #182236; color: #e8edf5; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_notebook():
    if not NOTEBOOK_PATH.exists():
        return []
    with NOTEBOOK_PATH.open("r", encoding="utf-8") as notebook_file:
        return json.load(notebook_file).get("cells", [])


def visualization_cells(cells):
    visible = []
    for cell in cells:
        if cell.get("cell_type") == "code":
            match = re.match(r"\s*#\s*(\d+)\.", source_text(cell))
            if match and 3 <= int(match.group(1)) <= 51:
                visible.append(cell)
        elif cell.get("cell_type") == "markdown" and re.search(
            r"(^|\n)\s*##\s+", source_text(cell)
        ):
            visible.append(cell)
    return visible


@st.cache_data(show_spinner=False)
def load_explorer_data(explorer_name):
    paths = {
        "Bank financials": PROJECT_ROOT / "MERGED DATASETS" / "merged_bank_financials.csv",
        "Crime and socio-economic data": PROJECT_ROOT / "MERGED DATASETS" / "merged_crime_data.csv",
        "Transactions (50K sample)": PROJECT_ROOT / "MERGED DATASETS" / "bank_transactions_clean.csv",
    }
    path = paths[explorer_name]
    frame = pd.read_csv(path)
    if explorer_name == "Transactions (50K sample)" and len(frame) > 50000:
        frame = frame.sample(n=50000, random_state=42)
    return frame


def source_text(cell):
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else source


def clean_text(value):
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[`*_#]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def cell_title(cell, index):
    source = source_text(cell)
    for line in source.splitlines():
        line = line.strip().lstrip("#").strip()
        line = re.sub(r"^[\-=_]+", "", line).strip()
        if line:
            line = re.sub(r"^CELL\s+\d+\s*[—-]?\s*", "", line, flags=re.IGNORECASE)
            return clean_text(line)[:85] or f"Cell {index + 1}"
    return f"Cell {index + 1}"


def section_title(cell):
    text = clean_text(source_text(cell))
    headings = re.findall(r"(?:^|\s)#{1,3}\s+([^\n]+)", source_text(cell))
    if headings:
        return clean_text(headings[0]).strip("- ")[:90]
    return text[:90] if text else "Notebook introduction"


def output_text(output):
    text_parts = []
    if "text" in output:
        text_parts.append("".join(output["text"]) if isinstance(output["text"], list) else output["text"])
    if "ename" in output or "evalue" in output:
        text_parts.append(f"{output.get('ename', 'Error')}: {output.get('evalue', '')}")
    data = output.get("data", {})
    for mime in ("text/plain", "text/markdown", "text/html"):
        if mime in data:
            value = data[mime]
            text_parts.append("".join(value) if isinstance(value, list) else value)
            break
    return "\n".join(part for part in text_parts if part).strip()


def render_output(output):
    data = output.get("data", {})
    if "application/vnd.plotly.v1+json" in data:
        figure = pio.from_json(json.dumps(data["application/vnd.plotly.v1+json"]))
        figure.update_layout(
            paper_bgcolor="#101522",
            plot_bgcolor="#182236",
            font_color="#e8edf5",
            title_font_color="#f4f7fb",
            legend_font_color="#e8edf5",
        )
        figure.update_xaxes(gridcolor="#2b3548", zerolinecolor="#2b3548")
        figure.update_yaxes(gridcolor="#2b3548", zerolinecolor="#2b3548")
        st.plotly_chart(figure, use_container_width=True)
        return True
    if "image/png" in data:
        image = data["image/png"]
        image = "".join(image) if isinstance(image, list) else image
        st.image(base64.b64decode(image), use_container_width=True)
        return True
    if "text/html" in data:
        html = data["text/html"]
        html = "".join(html) if isinstance(html, list) else html
        components.html(html, height=620, scrolling=True)
        return True
    text = output_text(output)
    if text:
        st.text(text)
        return True
    return False


def render_saved_map(cell):
    title = cell_title(cell, 0).lower()
    map_files = {
        "34.": "folium_transaction_heatmap.html",
        "35.": "folium_transaction_columns.html",
        "36.": "folium_state_crime_choropleth.html",
        "37.": "folium_transaction_hotspots.html",
    }
    filename = next((name for marker, name in map_files.items() if title.startswith(marker)), None)
    if filename is None:
        return False
    map_path = PROJECT_ROOT / "data" / "WAREHOUSE" / "plots" / filename
    if not map_path.exists():
        st.info("Run this map cell in main.ipynb first to create its interactive HTML map.")
        return True
    components.html(map_path.read_text(encoding="utf-8"), height=760, scrolling=True)
    return True


def notebook_groups(cells):
    groups = []
    current = {"name": "Notebook setup", "cells": []}
    for index, cell in enumerate(cells):
        if cell.get("cell_type") == "markdown" and re.search(r"(^|\n)\s*#{1,3}\s+", source_text(cell)):
            if current["cells"]:
                groups.append(current)
            current = {"name": section_title(cell), "cells": []}
            current["intro"] = cell
            continue
        current["cells"].append((index, cell))
    if current["cells"] or "intro" in current:
        groups.append(current)
    return groups


cells = visualization_cells(load_notebook())
if not cells:
    st.error(f"Notebook not found: {NOTEBOOK_PATH}")
    st.stop()

groups = notebook_groups(cells)
cell_lookup = {index: cell for index, cell in enumerate(cells)}

if "selected_cell" not in st.session_state:
    st.session_state.selected_cell = next(
        (index for index, cell in enumerate(cells) if cell.get("cell_type") == "code"),
        0,
    )


def notebook_cell_number(cell, fallback_index):
    match = re.match(r"\s*#\s*(\d+)\.", source_text(cell))
    return match.group(1) if match else str(fallback_index + 1)

st.sidebar.markdown("## PLOTTED GRAPHS")
st.sidebar.caption(f"Visualization cells 3–51 · {len(groups)} groups")
st.sidebar.divider()

for group_index, group in enumerate(groups):
    st.sidebar.markdown(f"**{group_index + 1}. {group['name']}**")
    for index, cell in group["cells"]:
        label = cell_title(cell, index)
        if st.sidebar.button(label, key=f"cell_{index}", use_container_width=True):
            st.session_state.selected_cell = index

explorer_choice = st.sidebar.selectbox(
    "Interactive explorer",
    ["None", "Bank financials", "Crime and socio-economic data", "Transactions (50K sample)"],
)

selected_index = st.session_state.selected_cell
selected_cell = cell_lookup[selected_index]

st.markdown(
    '<div class="hero"><div class="eyebrow">Local notebook platform</div>'
    '<h1>PLOTTED GRAPHS</h1>'
    '<p>Compare each analysis graph from the notebook through grouped, named buttons.</p></div>',
    unsafe_allow_html=True,
)

if explorer_choice != "None":
    st.markdown(f"## {explorer_choice}")
    try:
        explorer_html = pyg.to_html(
            load_explorer_data(explorer_choice),
            theme_key="streamlit",
            appearance="dark",
            default_tab="vis",
        )
        components.html(explorer_html, height=820, scrolling=True)
    except Exception as error:
        st.error(f"Interactive explorer could not be loaded: {error}")
    st.divider()

st.markdown(f"## {cell_title(selected_cell, selected_index)}")
st.markdown(
    f'<div class="cell-meta">Notebook cell {notebook_cell_number(selected_cell, selected_index)}</div>',
    unsafe_allow_html=True,
)

outputs = selected_cell.get("outputs", [])
saved_map_rendered = render_saved_map(selected_cell)
if saved_map_rendered:
    pass
elif outputs:
    rendered = False
    for output in outputs:
        rendered = render_output(output) or rendered
    if not rendered:
        st.caption("This cell has no displayable graph output.")
else:
    st.caption("No saved graph output for this cell. Run it in main.ipynb first.")

st.divider()
st.caption("PLOTTED GRAPHS · Notebook graph browser · Run with: python -m streamlit run app.py")
