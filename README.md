📊 Business Insights Dashboard

An interactive data analytics dashboard built with Python + Streamlit to analyze a business directory dataset.
It provides insights on services offered, company distribution, lead scoring, online presence, geographic reach, and data quality — all in a single interactive web app.

<!-- optional if you add a screenshot -->

🚀 Features

Overview Dashboard

KPI header (total companies, cities, top city, % with website)

City distribution bar charts

Online presence analysis (phone/email/website)

Services Analysis

Treemap & bar charts of top services offered

Keyword breakdown per company

Lead Management

Interactive lead table with search, filter, sort (AG Grid)

Lead scoring system (weighted: email, phone, website, keywords)

Export filtered leads as CSV

Interactive Map

Folium map with company markers

Popup cards (company, score, contact links)

Network Graph

Company–City network built with NetworkX

Centrality ranking of top companies by geographic reach

Data Quality Report

Missing values %, unique counts, data types

Duplicate company detection

Polished UI/UX

Custom dark theme & branding

Global filters (city, service, lead score range)

Tabs for navigation

🛠️ Tech Stack

Python – Core language

Streamlit – Interactive dashboard framework

Pandas – Data cleaning & transformation

Plotly Express – Interactive charts (bar, treemap, pie)

Folium + streamlit-folium – Interactive maps

NetworkX – Graph analysis (reach, centrality)

st-aggrid – Searchable/filterable data grid

📂 Project Structure
business-dashboard/
│── app.py                 # Main Streamlit app
│── data/
│    └── companies.csv     # Dataset
│── assets/
│    └── logo.png          # Optional logo
│    └── demo.png          # Screenshot
│── requirements.txt       # Dependencies
│── .streamlit/
│    └── config.toml       # Theme config
│── README.md              # Project documentation

⚙️ Installation & Setup

Clone the repo

git clone https://github.com/yourusername/business-dashboard.git
cd business-dashboard


Create & activate a virtual environment

python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows


Install dependencies

pip install -r requirements.txt


Or install one by one:

pip install pandas streamlit plotly folium streamlit-folium networkx streamlit-aggrid


Run the dashboard

streamlit run app.py


Open in your browser: http://localhost:8501

📊 Dataset

The dataset (companies.csv) contains a business directory of transport & logistics companies.

Key fields: co_name, city, phone, email, website, keywords, contact.

You can replace it with your own dataset as long as it has these columns.

🌐 Deployment

Deploy for free on Streamlit Community Cloud
:

Push this repo to GitHub.

Go to Streamlit Cloud → New App → Connect GitHub.

Select repo + branch + app.py.

Done! 🎉 Share your dashboard link.

📈 Future Improvements

✅ Geocoding cities to latitude/longitude for accurate maps

✅ Add MarkerCluster & Heatmap layers

✅ Export charts & reports as PDF

✅ Authentication (login page) for restricted access

✅ Machine Learning lead scoring
