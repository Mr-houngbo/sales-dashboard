# generate_report.py
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


if __name__ == "__main__":
    #============================================================================ RECEPTION DU DATASET FILTRE ==================================================================================================
    df_filtered = pd.read_pickle("temp_df.pkl")
    print(df_filtered.head())

    #============================================================ FONCTION DE GENERATION DU PDF , ENVOI EMAIL ET DAILY TASK ==================================================================================================================
    #==============================================================================================================================================================================

    #--------------------------GENERATION DE RAPPORTS---------------------------------------------------------------

    def generate_pdf(kpis, charts_paths, output_path='rapport.pdf'):
        pdf = FPDF()
        pdf.add_page()

        # Titre
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Rapport Journalier - {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')

        # Résumé des KPIs
        pdf.ln(10)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, f"""Résumé des KPIs :
                                    - Ventes totales : {kpis['ventes_totales']}
                                    - Pays les plus performants : {', '.join(kpis['pays_tops'])}
                                    - Produits les plus vendus : {', '.join(kpis['produits_tops'])}
                            """)

        # Visualisations
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Visualisations clés :", ln=True)

        for chart_path in charts_paths:
            try:
                pdf.image(chart_path, w=180)
                pdf.ln(10)
            except Exception as e:
                print(f"Erreur insertion image {chart_path} :", e)

        # Conclusion
        pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(0, 10, "Conclusion : Les ventes sont en croissance stable. Poursuivre les actions sur les marchés performants.")

        # Sauvegarde
        pdf.output(output_path)
    #==============================================================================================================================================================================
    # Fichier : generate_report_matplotlib.py (partie graphique seulement)

    # ========================== Graphique 1 : Evolution visiteurs ============================
    df_visitors = df_filtered.copy()
    df_visitors["Month"] = df_visitors["Date"].dt.to_period("M").astype(str)
    df_grouped_visitors = df_visitors.groupby(["Month", "Customer_Type"]).agg({"Order_ID": "nunique"}).reset_index()

    plt.figure(figsize=(10,6))
    for ctype in df_grouped_visitors["Customer_Type"].unique():
        data = df_grouped_visitors[df_grouped_visitors["Customer_Type"] == ctype]
        plt.plot(data["Month"], data["Order_ID"], label=ctype, marker='o')
    plt.title("Evolution des visiteurs (Nouveaux vs Existants)")
    plt.xlabel("Mois")
    plt.ylabel("Nombre de clients")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig("fig_visitors.png")

    # ========================== Graphique 2 : Chiffre d'affaires ============================
    df_revenue = df_filtered.copy()
    df_revenue["Month"] = df_revenue["Date"].dt.to_period("M").astype(str)
    df_grouped_revenue = df_revenue.groupby("Month")["Sales"].sum().reset_index()

    plt.figure(figsize=(10,6))
    plt.bar(df_grouped_revenue["Month"], df_grouped_revenue["Sales"], color='skyblue')
    plt.title("Chiffre d'affaires par mois")
    plt.xlabel("Mois")
    plt.ylabel("Ventes (CFA)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("fig_revenue.png")

    # ========================== Graphique 3 : Evolution Satisfaction ============================
    today = df_filtered["Date"].max()
    one_year_ago = today - timedelta(days=365)
    two_years_ago = today - timedelta(days=730)
    three_years_ago = today - timedelta(days=1095)

    # Groupements par année
    df_filtered["Month"] = df_filtered["Date"].dt.to_period("M").astype(str)
    df_current = df_filtered[df_filtered["Date"] >= one_year_ago].groupby("Month")["Satisfaction"].mean()
    df_last = df_filtered[(df_filtered["Date"] >= two_years_ago) & (df_filtered["Date"] < one_year_ago)].groupby("Month")["Satisfaction"].mean()
    df_two = df_filtered[(df_filtered["Date"] >= three_years_ago) & (df_filtered["Date"] < two_years_ago)].groupby("Month")["Satisfaction"].mean()

    plt.figure(figsize=(10,6))
    plt.plot(df_current.index, df_current.values, label="Année 0", color="#FF4B4B")
    plt.plot(df_last.index, df_last.values - 6, label="Année -1", color="#4B7BFF")
    plt.plot(df_two.index, df_two.values, label="Année -2", color="#00B88B")
    plt.title("Evolution Satisfaction : 3 dernières années")
    plt.xlabel("Mois")
    plt.ylabel("Score de Satisfaction")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("fig_compare.png")

    # ========================== Graphique 4 : Ventes vs Objectifs ============================
    df_sales = df_filtered.copy()
    df_sales["Month"] = df_sales["Date"].dt.to_period("M").astype(str)
    df_grouped_sales = df_sales.groupby("Month")[["Sales", "Target_Sales"]].sum().reset_index()

    plt.figure(figsize=(10,6))
    bar_width = 0.4
    index = range(len(df_grouped_sales))

    plt.bar([i - bar_width/2 for i in index], df_grouped_sales["Sales"], width=bar_width, label="Ventes")
    plt.bar([i + bar_width/2 for i in index], df_grouped_sales["Target_Sales"], width=bar_width, label="Objectifs")
    plt.xticks(index, df_grouped_sales["Month"], rotation=45)
    plt.title("Ventes Réelles vs Objectifs")
    plt.xlabel("Mois")
    plt.ylabel("Montant des ventes")
    plt.legend()
    plt.tight_layout()
    plt.savefig("fig_target.png")

    # ========================== Graphique 5 : Service Level ============================
    df_service = df_filtered.copy()
    df_service["Month"] = df_service["Date"].dt.to_period("M").astype(str)
    df_grouped_service = df_service.groupby("Month")["Service_Level"].mean().reset_index()

    plt.figure(figsize=(10,6))
    plt.bar(df_grouped_service["Month"], df_grouped_service["Service_Level"], color="#00B88B")
    plt.title("Service Level mensuel")
    plt.xlabel("Mois")
    plt.ylabel("Niveau de Service (%)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("fig_service.png")

    # ========================== Graphique 6 : Volume vs Service ============================
    df_volume_service = df_filtered.copy()
    df_volume_service["Month"] = df_volume_service["Date"].dt.to_period("M").astype(str)
    df_grouped_vs = df_volume_service.groupby("Month")[["Sales", "Service_Level"]].mean().reset_index()

    plt.figure(figsize=(10,6))
    plt.plot(df_grouped_vs["Month"], df_grouped_vs["Sales"], label="Sales", marker='o')
    plt.plot(df_grouped_vs["Month"], df_grouped_vs["Service_Level"], label="Service Level", marker='x')
    plt.title("Volume vs Niveau de Service")
    plt.xlabel("Mois")
    plt.ylabel("Valeur")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("fig_vs.png")

    # ========================== Graphique 7 : Top Produits ============================
    produits = df_filtered["Product"].value_counts().index
    pourcentages = list(df_filtered["Product"].value_counts()/len(df_filtered)*100)

    plt.figure(figsize=(10,6))
    plt.barh(produits, pourcentages, color="lightcoral")
    plt.xlabel("Pourcentage de ventes")
    plt.title("Top Produits - Parts de Marché")
    plt.xlim(0, 30)
    plt.tight_layout()
    plt.savefig("fig_top_products.png")

    # ========================== Graphique 8 : Évolution mensuelle Sales + Satisfaction + Service ============================
    df_monthly = df_filtered.copy()
    df_monthly["Month"] = df_monthly["Date"].dt.to_period("M").astype(str)
    df_grouped = df_monthly.groupby("Month")[["Sales", "Satisfaction", "Service_Level"]].mean().reset_index()

    plt.figure(figsize=(10,6))
    plt.plot(df_grouped["Month"], df_grouped["Sales"], label="Sales", marker='o')
    plt.plot(df_grouped["Month"], df_grouped["Satisfaction"], label="Satisfaction", marker='x')
    plt.plot(df_grouped["Month"], df_grouped["Service_Level"], label="Service Level", marker='s')
    plt.title("Évolution mensuelle")
    plt.xlabel("Mois")
    plt.ylabel("Valeur")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("fig_evolution_globale.png")


    kpis = {
            'ventes_totales': '125,000 ',
            'pays_tops': ['France', 'Allemagne'],
            'produits_tops': ['Produit A', 'Produit B']
        }
    charts_paths = ['fig_revenue.png', 'fig_top_products.png',"fig_evolution_globale.png","fig_vs.png","fig_compare.png","fig_service.png","fig_visitors.png","fig_target.png"]

    generate_pdf(kpis, charts_paths)
    #============================================================================================