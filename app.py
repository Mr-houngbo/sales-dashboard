import streamlit as st
import pandas as pd
import plotly.express as px
import io
import base64
import urllib.parse
import time
import requests
from fpdf import FPDF
import matplotlib.pyplot as plt
from apscheduler.schedulers.background import BackgroundScheduler
# pip install -U kaleido
from datetime import datetime, timedelta
import yagmail
import subprocess
import pickle





st.experimental_rerun_interval = 30  # toutes les 60 secondes


# Config de la page
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Titre du dashboard

st.markdown("""
        <div class="header-container">
            <div class="header-left">
                <h2>👤 Enver - Sales Dashboard </h2>
            </div>
        </div>
    """,unsafe_allow_html=True)
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------


#  st.title("Sales Dashboard")

# Chargement des données
@st.cache_data
def load_data():
    df = pd.read_csv("sales_dashboard_dataset.csv", parse_dates=["Date"])
    return df

df = load_data()

#--------------------------------------------------------------------------------------------------------
# -----------------------------------------------------
# Sidebar stylée avec titres, emojis et bouton reset
# -----------------------------------------------------

#--------------------------------------------------------------------------------------------------------

with st.sidebar:
    # Initialisation des valeurs par défaut dans session_state
    if "reset" not in st.session_state:
        st.session_state.reset = False
        st.session_state.date_range = [df["Date"].min(), df["Date"].max()]
        st.session_state.selected_countries = list(df["Country"].unique())
        st.session_state.selected_customers = list(df["Customer_Type"].unique())
        st.session_state.selected_products = list(df["Product"].unique())

    # Bouton Réinitialiser
    if st.button("🔄 Réinitialiser les filtres"):
        st.session_state.reset = True
        st.rerun()

    # Application des valeurs par défaut si reset
    if st.session_state.reset:
        st.session_state.date_range = [df["Date"].min(), df["Date"].max()]
        st.session_state.selected_countries = list(df["Country"].unique())
        st.session_state.selected_customers = list(df["Customer_Type"].unique())
        st.session_state.selected_products = list(df["Product"].unique())
        st.session_state.reset = False

    # Filtres
    with st.expander(" Période d'analyse", expanded=False):
        st.session_state.date_range = st.date_input(
            label="Choisir la période",
            value=st.session_state.date_range,
            min_value=df["Date"].min(),
            max_value=df["Date"].max()
        )

    with st.expander(" Choix des pays", expanded=False):
        countries = list(df["Country"].unique())
        st.session_state.selected_countries = st.multiselect(
            label="Choisir le pays",
            options=countries,
            default=st.session_state.selected_countries
        )

    with st.expander(" Type de client", expanded=False):
        customer_types = list(df["Customer_Type"].unique())
        st.session_state.selected_customers = st.multiselect(
            label="Choisir le type de client ",
            options=customer_types,
            default=st.session_state.selected_customers
        )

    with st.expander(" Produits", expanded=False):
        products = list(df["Product"].unique())
        st.session_state.selected_products = st.multiselect(
            label="Choisir le produit",
            options=products,
            default=st.session_state.selected_products
        )

# Pour utiliser les valeurs sélectionnées dans ton code principal :
date_range = st.session_state.date_range
selected_countries = st.session_state.selected_countries
selected_customers = st.session_state.selected_customers
selected_products = st.session_state.selected_products

#--------------------------------------------------------------------------------------------------------

# Application des filtres
df_filtered = df[
    (df["Date"] >= pd.to_datetime(date_range[0])) &
    (df["Date"] <= pd.to_datetime(date_range[1])) &
    (df["Country"].isin(selected_countries)) &
    (df["Customer_Type"].isin(selected_customers)) &
    (df["Product"].isin(selected_products))
]
#--------------------------------------------------------------------------------------------------------

#---------------------------------TESTTTTTTTTTTTTTTTTTTTTTTTTTTT-----------------------------------------------------------------------

# Init session states
if "search_text" not in st.session_state:
    st.session_state.search_text = ""

if "filter_applied" not in st.session_state:
    st.session_state.filter_applied = False

# Barre de recherche
search_query = st.text_input("🔍 Rechercher...", value=st.session_state.search_text).lower().strip()

# Mots-clés
keyword_map = {
    "selected_countries": ["ghana", "senegal", "kenya", "nigeria", "south africa"],
    "selected_customers": ["new", "loyal", "returning"],
    "selected_products": ["home", "decor", "range", "disney", "bag", "bathroom", "essentials", "apple", "smartwatches"]
}

# Détection et application (une seule fois)
if not st.session_state.filter_applied and search_query:
    for col_key, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in search_query:
                if col_key == "selected_countries":
                    st.session_state.selected_countries = [c for c in df["Country"].unique() if keyword in c.lower()]
                elif col_key == "selected_customers":
                    st.session_state.selected_customers = [c for c in df["Customer_Type"].unique() if keyword in c.lower()]
                elif col_key == "selected_products":
                    st.session_state.selected_products = [c for c in df["Product"].unique() if keyword in c.lower()]
                # Marquer comme appliqué + déclencher rerun
                st.session_state.filter_applied = True
                st.session_state.search_text = ""
                st.rerun()

# Réinitialisation si champ vide
if not search_query:
    st.session_state.filter_applied = False

#--------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------

# Exemple si nécessaire
# df_filtered = ...

st.markdown("## Indicateurs Clés")

col1, col2, col3, col4 = st.columns(4)

# KPI 1: Ventes
with col1:
    total_sales = df_filtered["Sales"].sum()
    previous_month = (df_filtered["Date"].max() - pd.DateOffset(months=1)).month
    sales_last_month = df_filtered[df_filtered["Date"].dt.month == previous_month]["Sales"].sum()
    variation = total_sales - sales_last_month
    variation_str = f"+{variation:,.0f} CFA" if variation >= 0 else f"{variation:,.0f} CFA"

    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">💰</div>
            <p class="kpi-title">Total Ventes</p>
            <p class="kpi-value">{total_sales:,.0f} CFA</p>
            
        </div>
    """, unsafe_allow_html=True)
# --- <p class="kpi-sub">{variation_str}</p> 

# KPI 2: Commandes
with col2:
    total_orders = df_filtered["Order_ID"].nunique()
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">📦</div>
            <p class="kpi-title">Total Commandes</p>
            <p class="kpi-value">{total_orders}</p>
        </div>
    """, unsafe_allow_html=True)

# KPI 3: Produits
with col3:
    total_products = df_filtered["Product"].nunique()
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">🛒</div>
            <p class="kpi-title">Produits Vendus</p>
            <p class="kpi-value">{total_products}</p>
        </div>
    """, unsafe_allow_html=True)

# KPI 4: Nouveaux Clients
with col4:
    new_customers = df_filtered[df_filtered["Customer_Type"] == "New"]["Order_ID"].nunique()
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">👤</div>
            <p class="kpi-title">Nouveaux Clients</p>
            <p class="kpi-value">{new_customers}</p>
        </div>
    """, unsafe_allow_html=True)

#----------------------------------------PREMIERS GRAPHIQUES---------------------------------------------------------------

col1, col2 = st.columns(2)
with col1:
    st.markdown("## Visitor Insights")

    # Préparer les données mensuelles
    df_visitors = df_filtered.copy()
    df_visitors["Month"] = df_visitors["Date"].dt.to_period("M").astype(str)

    # Groupement
    df_grouped_visitors = df_visitors.groupby(["Month", "Customer_Type"]).agg({
        "Order_ID": "nunique"
    }).reset_index().rename(columns={"Order_ID": "Number_of_Customers"})

    # Graphique
    fig_visitors = px.line(
        df_grouped_visitors,
        x="Month",
        y="Number_of_Customers",
        color="Customer_Type",
        markers=True,
        title="👥 Evolution des visiteurs (Nouveaux vs Existants)"
    )

    fig_visitors.update_layout(
        xaxis_title="Mois",
        yaxis_title="Nombre de clients",
        legend_title="Type de client",
        height=400
    )

    st.plotly_chart(fig_visitors, use_container_width=True)
    


with col2:
    st.markdown("## Total Revenue")

    # Préparer les données mensuelles
    df_revenue = df_filtered.copy()
    df_revenue["Month"] = df_revenue["Date"].dt.to_period("M").astype(str)

    # Groupement par mois
    df_grouped_revenue = df_revenue.groupby("Month").agg({
        "Sales": "sum"
    }).reset_index()

    # Graphique
    fig_revenue = px.bar(
        df_grouped_revenue,
        x="Month",
        y="Sales",
        title="💵 Chiffre d'affaires par mois",
        labels={"Sales": "Total des ventes", "Month": "Mois"},
        color_discrete_sequence=["#0083B8"]  # Bleu Streamlit stylé
    )

    fig_revenue.update_layout(
        xaxis_title="Mois",
        yaxis_title="Ventes (CFA)",
        height=400
    )

    st.plotly_chart(fig_revenue, use_container_width=True)
    


#--------------------------------------------------------------------------------------------------------
col1, col2 ,col3 = st.columns(3)
with col1:
    st.markdown("## Customer Satisfaction : 3 dernières années")

        # Assurer le format datetime
    df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])

    # Bornes de temps
    today = df_filtered["Date"].max()
    one_year_ago = today - timedelta(days=365)
    two_years_ago = today - timedelta(days=-730)
    three_years_ago = today - timedelta(days=995)

    # Année actuelle (Year 0)
    df_current_year = df_filtered[df_filtered["Date"] >= one_year_ago].copy()
    df_current_year["Month"] = df_current_year["Date"].dt.to_period("M").astype(str)
    df_current_grouped = df_current_year.groupby("Month").agg({
        "Satisfaction": "mean"
    }).reset_index()
    df_current_grouped.rename(columns={"Satisfaction": "Satisfaction_Year_0"}, inplace=True)


    # Année précédente (Year -1)
    df_last_year = df_filtered[(df_filtered["Date"] >= two_years_ago) & (df_filtered["Date"] < one_year_ago)].copy()
    df_last_year["Month"] = df_last_year["Date"].dt.to_period("M").astype(str)
    df_last_grouped = df_last_year.groupby("Month").agg({
        "Satisfaction": "mean"
    }).reset_index()
    df_last_grouped.rename(columns={"Satisfaction": "Satisfaction_Year_1"}, inplace=True)
    df_last_grouped["Satisfaction_Year_1"]=df_last_grouped["Satisfaction_Year_1"]-6

    # Année -2 (Year -2)
    df_two_years_ago = df_filtered[(df_filtered["Date"] >= three_years_ago) & (df_filtered["Date"] < two_years_ago)].copy()
    df_two_years_ago["Month"] = df_two_years_ago["Date"].dt.to_period("M").astype(str)
    df_two_years_grouped = df_two_years_ago.groupby("Month").agg({
        "Satisfaction": "mean"
    }).reset_index()
    df_two_years_grouped.rename(columns={"Satisfaction": "Satisfaction_Year_2"}, inplace=True)

    # Fusionner les 3 datasets
    df_compare = pd.merge(df_current_grouped, df_last_grouped, on="Month", how="outer")
    df_compare = pd.merge(df_compare, df_two_years_grouped, on="Month", how="outer").sort_values("Month")

    df_compare.fillna(0, inplace=True)

    # Plot Area
    fig_compare = px.area(
        df_compare,
        x="Month",
        y=["Satisfaction_Year_0", "Satisfaction_Year_1", "Satisfaction_Year_2"],
        labels={"value": "Score de Satisfaction", "variable": "Période", "Month": "Mois"},
        title="📊 Evolution Satisfaction : 3 dernières années",
        color_discrete_map={
            "Satisfaction_Year_0": "#FF4B4B",  # Rouge actuel
            "Satisfaction_Year_1": "#4B7BFF",  # Bleu année -1
            "Satisfaction_Year_2": "#00B88B"   # Vert année -2
        }
    )

    fig_compare.update_layout(
        xaxis_title="Mois",
        yaxis_title="Score de Satisfaction",
        height=450,
        legend_title="Période"
    )

    st.plotly_chart(fig_compare, use_container_width=True)
    

with col2:
    st.markdown("## Target vs Reality")

    # Préparation des données
    df_sales = df_filtered.copy()
    df_sales["Month"] = df_sales["Date"].dt.to_period("M").astype(str)

    # Agrégation mensuelle
    df_grouped_sales = df_sales.groupby("Month").agg({
        "Sales": "sum",
        "Target_Sales": "sum"
    }).reset_index()

    # Reshape en format long pour groupé (barres côte à côte)
    df_melted = df_grouped_sales.melt(id_vars="Month", 
                                    value_vars=["Sales", "Target_Sales"],
                                    var_name="Type", 
                                    value_name="Valeur")

    # Graphique barres groupées
    fig_target = px.bar(
        df_melted,
        x="Month",
        y="Valeur",
        color="Type",
        barmode="group",
        text="Valeur",
        labels={"Month": "Mois", "Valeur": "Montant", "Type": "Catégorie"},
        title="📊 Ventes Réelles vs Objectifs"
    )

    fig_target.update_layout(
        xaxis_title="Mois",
        yaxis_title="Montant des ventes",
        height=450
    )

    st.plotly_chart(fig_target, use_container_width=True)
    

with col3:
    st.markdown("## Ventes par Pays")

    # Agrégation des ventes par pays
    df_sales_country = df_filtered.groupby("Country").agg({
        "Sales": "sum"
    }).reset_index()

    # Création de la carte
    fig_map = px.choropleth(
        df_sales_country,
        locations="Country",
        locationmode="country names",  # on suppose que ce sont des noms de pays
        color="Sales",
        color_continuous_scale="Blues",
        title="💰 Ventes totales par pays",
        labels={"Sales": "Montant des ventes"}
    )

    fig_map.update_layout(
        geo=dict(showframe=False, showcoastlines=False),
        height=500
    )

    st.plotly_chart(fig_map, use_container_width=True)
    
#--------------------------------------------------------------------------------------------------------

col1, col2 = st.columns(2)
with col1:
    st.markdown("## Service Level")

    # Préparation des données
    df_service = df_filtered.copy()
    df_service["Month"] = df_service["Date"].dt.to_period("M").astype(str)

    # Agrégation mensuelle
    df_grouped_service = df_service.groupby("Month").agg({
        "Service_Level": "mean"
    }).reset_index()

    # Graphique
    fig_service = px.bar(
        df_grouped_service,
        x="Month",
        y="Service_Level",
        title="📦 Service Level mensuel",
        labels={"Service Level": "Niveau de Service (%)", "Month": "Mois"},
        color_discrete_sequence=["#00B88B"]
    )

    fig_service.update_layout(
        xaxis_title="Mois",
        yaxis_title="Niveau de Service (%)",
        height=400
    )

    st.plotly_chart(fig_service, use_container_width=True)
    

with col2:
    produits = df_filtered["Product"].value_counts().index
    n=list(df_filtered["Product"].value_counts()/len(df_filtered["Product"])*100)
    data = {
        "Product": produits,
        "Percentage": n
    }
    df_ = pd.DataFrame(data)

    # === Affichage du titre ===
    st.subheader("Top Products – Parts de Vente (%)")

    # === Graphique en barre horizontale style barre de progression ===
    fig = px.bar(
        df_.sort_values(by="Percentage"),
        x="Percentage",
        y="Product",
        orientation="h",
        text="Percentage",
        color="Product",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(
        xaxis_title="Pourcentage de ventes",
        yaxis_title="",
        showlegend=False,
        xaxis_range=[0, 30],
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # === Affichage dans Streamlit ===
    st.plotly_chart(fig, use_container_width=True)
    

#--------------------------------------------------------------------------------------------------------

st.markdown("## Volume vs Service Level")

# Agrégation mensuelle
df_volume_service = df_filtered.copy()
df_volume_service["Month"] = df_volume_service["Date"].dt.to_period("M").astype(str)

df_grouped_vs = df_volume_service.groupby("Month").agg({
    "Sales": "sum",
    "Service_Level": "mean"
}).reset_index()

# Mise à l'échelle pour une comparaison visuelle plus fluide
# Optionnel : si échelles très différentes, on peut normaliser
# df_grouped_vs["Service Level"] *= df_grouped_vs["Sales"].max() / df_grouped_vs["Service Level"].max()

# Transformation en format long
df_melted_vs = df_grouped_vs.melt(id_vars="Month", 
                                   value_vars=["Sales", "Service_Level"],
                                   var_name="Indicateur", 
                                   value_name="Valeur")

# Graphique barres groupées
fig_vs = px.bar(
    df_melted_vs,
    x="Month",
    y="Valeur",
    color="Indicateur",
    barmode="group",
    text="Valeur",
    labels={"Month": "Mois", "Valeur": "Valeur", "Indicateur": "Indicateur"},
    title="📊 Volume vs Niveau de Service"
)

fig_vs.update_layout(
    xaxis_title="Mois",
    yaxis_title="Valeur",
    height=450
)

st.plotly_chart(fig_vs, use_container_width=True)
#------------------------------------------------------------------------------------

# Agrégation mensuelle
df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])
df_monthly = df_filtered.copy()
df_monthly["Month"] = df_monthly["Date"].dt.to_period("M").astype(str)
df_grouped = df_monthly.groupby("Month").agg({
    "Sales": "sum",
    "Satisfaction": "mean",
    "Service_Level": "mean"
}).reset_index()

# Création du graphique
fig = px.line(df_grouped, x="Month", 
                y=["Sales", "Satisfaction", "Service_Level"],
                labels={"value": "Valeur", "variable": "Indicateur", "Month": "Mois"},
                title="📈 Évolution mensuelle")

fig.update_layout(
    showlegend=True,
    height=300,
    margin=dict(l=0, r=0, t=40, b=0)
)

st.plotly_chart(fig, use_container_width=True)

#----------------------------------Télécharger les données (CSV)----------------------------------------------------------------------

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(df_filtered)

st.download_button(
    label="📥 Télécharger les données (CSV)",
    data=csv,
    file_name='export.csv',
    mime='text/csv',
)

#----------------------------------------------------Générer et envoyer le rapport PDF maintenant----------------------------------------------------

if st.button("Générer et envoyer le rapport PDF maintenant"):

    #-------------------------------------- Sauvegarder les variables -----------------------

    # Supposons que tu as un DataFrame df à transférer
    df_filtered.to_pickle("temp_df.pkl")

    #-----------------------------------------------------------------------------------------
    # Appeler le script
    
    result = subprocess.run(['python', 'generate_report.py'], capture_output=True, text=True)
    st.text(result.stdout)  # Ajoute ceci temporairement pour debug

    if result.returncode == 0:
        st.success("Rapport généré avec succès !")
    else:
        st.error(f"Erreur lors de la génération : {result.stderr}")
    # Option : proposer le téléchargement du PDF généré
    try:
        with open("rapport.pdf", "rb") as f:
            st.download_button("📥 Télécharger le dernier rapport PDF", f, file_name="rapport.pdf")
    except FileNotFoundError:
        st.info("Aucun rapport PDF généré pour l'instant.")

#--------------------------------------------------------------------------------------------------------

def send_email_from_streamlit(pdf_path="rapport.pdf"):

    if st.button("📤 Envoyer le rapport par mail"):
        receiver_email = st.text_input("Entrer l'adresse e-mail du destinataire")
        if not receiver_email:
            st.warning("Veuillez saisir une adresse email valide.")
        else:
            try:
                # Config compte expéditeur
                yag = yagmail.SMTP(user="ton.email@gmail.com", password="tonMotDePasseApp")
                subject = "Rapport de performance - Généré automatiquement"
                body = "Bonjour,\nVeuillez trouver ci-joint le rapport des performances du jour.\nCordialement."
                yag.send(to=receiver_email, subject=subject, contents=body, attachments=pdf_path)
                st.success(f"✅ Rapport envoyé à {receiver_email}")
            except Exception as e:
                st.error("❌ Erreur lors de l'envoi du mail :")
                st.text(str(e))

#--------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------
