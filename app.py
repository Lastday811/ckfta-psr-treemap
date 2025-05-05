import os
import re
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# File loading
file_path = os.getenv('DATA_FILE_PATH', 'PSR Annex 3-A Combined_Sheet_Corrected.xlsx')

try:
    data = pd.read_excel(file_path)
except FileNotFoundError:
    raise FileNotFoundError(f"Could not find the Excel file at: {file_path}")

# Clean column names
data.columns = data.columns.str.strip().str.replace("\n", " ")

# Select and clean relevant columns
data = data[['Chapter', 'Subheading', 'Product Description', 'Product Specific Rule']].copy()
data['Chapter'] = data['Chapter'].ffill()
data['Subheading'] = data['Subheading'].ffill()
data = data.dropna(subset=['Chapter', 'Subheading'])

# Clean string fields
data['Chapter'] = data['Chapter'].astype(str).str.strip()
data['Subheading'] = data['Subheading'].astype(str).str.strip()
data['Product Description'] = data['Product Description'].fillna("No description").astype(str).str.strip()
data['Product Specific Rule'] = data['Product Specific Rule'].fillna("No rule").astype(str).str.strip()

# Remove non-printable characters
def clean_text(text):
    return re.sub(r'[^\x20-\x7E]', '', text)

data['Product Description'] = data['Product Description'].apply(clean_text)
data['Product Specific Rule'] = data['Product Specific Rule'].apply(clean_text)
data = data[data['Product Specific Rule'].str.strip() != ""]
data = data[(data['Chapter'] != "") & (data['Subheading'] != "")]
data = data.drop_duplicates(subset=['Subheading'])

# Short text for treemap tooltip
data['Short Description'] = data['Product Description'].apply(lambda x: " ".join(x.split()[:10]) + ("..." if len(x.split()) > 10 else ""))
data['Short Rule'] = data['Product Specific Rule'].apply(lambda x: " ".join(x.split()[:10]) + ("..." if len(x.split()) > 10 else ""))

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # for deployment

# Layout
app.layout = html.Div([
    html.H1("CKFTA - Product Specific Rules by Chapter and Subheading", style={'text-align': 'center'}),
    html.Div([
        dcc.Input(id="search-input", type="text", placeholder="Search Subheading", style={'width': '50%', 'padding': '10px', 'margin': '10px 0'}),
    ], style={'display': 'flex', 'justify-content': 'center'}),
    dcc.Graph(id='treemap', style={'height': '80vh'})
])

# Callback
@app.callback(
    Output('treemap', 'figure'),
    Input('search-input', 'value')
)
def update_treemap(search_value):
    filtered = data
    if search_value:
        filtered = data[data['Subheading'].str.contains(search_value, case=False, na=False)]

    fig = px.treemap(
        filtered,
        path=['Chapter', 'Subheading'],
        values=None,
        hover_data=['Short Description', 'Short Rule'],
        title="CKFTA - Product Specific Rules by Chapter and Subheading",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_traces(
        hovertemplate="<b>%{label}</b><br><br><b>Description:</b><br>%{customdata[0]}<br><br><b>Rule:</b><br>%{customdata[1]}"
    )
    fig.update_layout(
        margin=dict(t=60, l=30, r=30, b=30),
        title_x=0.5,
        paper_bgcolor='white'
    )
    return fig

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))  # For Render or local
    app.run(debug=True, host="0.0.0.0", port=port)
