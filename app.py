import pandas as pd
import re
import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

# Load and clean data
file_path = r"/Users/rithyly/Desktop/data-science-roadmap-2024/CKFTA/PSR Annex 3-A Combined_Sheet_Corrected.xlsx"
data = pd.read_excel(file_path)
data.columns = data.columns.str.strip().str.replace("\n", " ")
data = data[['Chapter', 'Subheading', 'Product Description', 'Product Specific Rule']].copy()
data['Chapter'] = data['Chapter'].ffill().astype(str).str.strip()
data['Subheading'] = data['Subheading'].ffill().astype(str).str.strip()
data['Product Description'] = data['Product Description'].fillna("No description").astype(str).str.strip()
data['Product Specific Rule'] = data['Product Specific Rule'].fillna("No rule").astype(str).str.strip()

def clean_text(text):
    return re.sub(r'[^\x20-\x7E]', '', text)

data['Product Description'] = data['Product Description'].apply(clean_text)
data['Product Specific Rule'] = data['Product Specific Rule'].apply(clean_text)
data = data[data['Product Specific Rule'].str.strip() != ""]
data = data.drop_duplicates(subset=['Subheading'])

# Add short versions for table preview
data['Short Description'] = data['Product Description'].apply(lambda x: " ".join(x.split()[:10]) + ("..." if len(x.split()) > 10 else ""))
data['Short Rule'] = data['Product Specific Rule'].apply(lambda x: " ".join(x.split()[:10]) + ("..." if len(x.split()) > 10 else ""))

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    html.H2("CKFTA - Product Specific Rules", className="my-4 text-center"),

    dcc.Input(
        id="search-input",
        type="text",
        placeholder="Search Subheading...",
        className="form-control mb-3"
    ),

    dash_table.DataTable(
        id='rule-table',
        columns=[
            {"name": "Chapter", "id": "Chapter"},
            {"name": "Subheading", "id": "Subheading"},
            {"name": "Short Description", "id": "Short Description"},
            {"name": "Short Rule", "id": "Short Rule"},
        ],
        data=data.to_dict('records'),
        page_size=12,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        row_selectable='single'
    ),

    # Modal for full description and rule
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody([
            html.H6("Product Description"),
            html.P(id="modal-description", style={"whiteSpace": "pre-wrap"}),
            html.H6("Product Specific Rule", className="mt-3"),
            html.P(id="modal-rule", style={"whiteSpace": "pre-wrap"})
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="info-modal", is_open=False)
], fluid=True)


# Callback to filter data
@app.callback(
    Output('rule-table', 'data'),
    Input('search-input', 'value')
)
def filter_table(search_value):
    if not search_value:
        return data.to_dict('records')
    filtered = data[data['Subheading'].str.contains(search_value, case=False, na=False)]
    return filtered.to_dict('records')


# Callback to open modal on row click
@app.callback(
    Output("info-modal", "is_open"),
    Output("modal-title", "children"),
    Output("modal-description", "children"),
    Output("modal-rule", "children"),
    Input("rule-table", "selected_rows"),
    State("rule-table", "data"),
    Input("close-modal", "n_clicks"),
    State("info-modal", "is_open")
)
def display_modal(selected_rows, table_data, close_click, is_open):
    if selected_rows:
        selected = table_data[selected_rows[0]]
        return True, f"Subheading: {selected['Subheading']}", selected['Product Description'], selected['Product Specific Rule']
    if close_click and is_open:
        return False, "", "", ""
    return is_open, "", "", ""

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

