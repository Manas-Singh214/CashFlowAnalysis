from pathlib import Path
import base64
import json
import re

import streamlit as st
import streamlit.components.v1 as components
import plotly.io as pio


PROJECT_ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = PROJECT_ROOT / "main.ipynb"

st.set_page_config(
    page_title="This vs That",
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


cells = load_notebook()
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

st.sidebar.markdown("## This vs That")
st.sidebar.caption(f"{len(cells)} cells · {len(groups)} groups")
st.sidebar.divider()

for group_index, group in enumerate(groups):
    st.sidebar.markdown(f"**{group_index + 1}. {group['name']}**")
    for index, cell in group["cells"]:
        label = cell_title(cell, index)
        if st.sidebar.button(label, key=f"cell_{index}", use_container_width=True):
            st.session_state.selected_cell = index

selected_index = st.session_state.selected_cell
selected_cell = cell_lookup[selected_index]

st.markdown(
    '<div class="hero"><div class="eyebrow">Local notebook platform</div>'
    '<h1>This vs That</h1>'
    '<p>Compare each analysis graph from the notebook through grouped, named buttons.</p></div>',
    unsafe_allow_html=True,
)

st.markdown(f"## {cell_title(selected_cell, selected_index)}")
st.markdown(
    f'<div class="cell-meta">Cell {selected_index + 1} of {len(cells)}</div>',
    unsafe_allow_html=True,
)

outputs = selected_cell.get("outputs", [])
if outputs:
    rendered = False
    for output in outputs:
        rendered = render_output(output) or rendered
    if not rendered:
        st.caption("This cell has no displayable graph output.")
else:
    st.caption("No saved graph output for this cell. Run it in main.ipynb first.")

st.divider()
st.caption("This vs That · Notebook graph browser · Run with: python -m streamlit run app.py")
