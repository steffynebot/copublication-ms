import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pydeck as pdk
import math
import time
import numpy as np
import random

# -------------------
# Page config
# -------------------
st.set_page_config(page_title="Copublications Inria (centres Sophia et Bordeaux)", layout="wide")

# -------------------
# Détection du thème actuel
# -------------------
theme = st.get_option("theme.base")  # 'light' ou 'dark'
is_dark = theme == "dark"

# -------------------
# Couleurs selon le mode
# -------------------
if is_dark:
    PRIMARY_COLOR = "#83c9ff"
    SECONDARY_COLOR = "#ffabab"
    ACCENT_COLOR = "#7defa1"
    BACKGROUND_COLOR = "#004280"
else:
    PRIMARY_COLOR = "#0484fc"
    SECONDARY_COLOR = "#faa48a"
    ACCENT_COLOR = "#4cada3"
    BACKGROUND_COLOR = "#e4f5ff"

# -------------------
# Load data
# -------------------
@st.cache_data
def load_data():
    df = pd.read_excel("Copubliants_par_auteur_Inria_Bordeaux_Sophia.xlsx")
    df.columns = [str(c).strip().replace("\xa0", "").replace(" ", "_") for c in df.columns]
    return df

df = load_data()
if df.empty:
    st.error("Aucune donnée trouvée.")
    st.stop()

# Colonnes
hal_col, auteurs_fr_col, auteurs_copub_col = "HalID", "Auteurs_FR", "Auteurs_copubliants"
ville_col, org_col, annee_col, equipe_col, centre_col, pays_col = "Ville", "Organisme_copubliant", "Année", "Equipe", "Centre", "Pays"

# -------------------
# Sidebar filtres (version simplifiée & réactive)
# -------------------
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.caption("Logo manquant")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### DATALAKE")
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Initialisation des clés ---
    for key in ["centres", "pays", "villes", "organismes", "annees", "equipes"]:
        if key not in st.session_state:
            if key == "villes":
                st.session_state[key] = "Toutes"
            else:
                st.session_state[key] = []

    # --- Calcul des options selon sélection en cours ---
    # 1. Centres (global)
    centres_opts = sorted(df[centre_col].dropna().unique())
    st.session_state.centres = st.multiselect(
        "Centre",
        centres_opts,
        default=st.session_state.centres
    )

    tmp = df.copy()
    if st.session_state.centres:
        tmp = tmp[tmp[centre_col].isin(st.session_state.centres)]

    # 2. Pays
    pays_opts = sorted(tmp[pays_col].dropna().unique())
    st.session_state.pays = st.multiselect(
        "Pays",
        pays_opts,
        default=[x for x in st.session_state.pays if x in pays_opts]
    )

    if st.session_state.pays:
        tmp = tmp[tmp[pays_col].isin(st.session_state.pays)]

    # 3. Villes
    villes_opts = ["Toutes"] + sorted(tmp[ville_col].dropna().unique())
    st.session_state.villes = st.selectbox(
        "Ville",
        villes_opts,
        index=villes_opts.index(st.session_state.villes)
        if st.session_state.villes in villes_opts else 0
    )

    if st.session_state.villes != "Toutes":
        tmp = tmp[tmp[ville_col] == st.session_state.villes]

    # 4. Organismes
    orgs_opts = sorted(tmp[org_col].dropna().unique())
    st.session_state.organismes = st.multiselect(
        "Organismes copubliants",
        orgs_opts,
        default=[x for x in st.session_state.organismes if x in orgs_opts]
    )

    if st.session_state.organismes:
        tmp = tmp[tmp[org_col].isin(st.session_state.organismes)]

    # 5. Années
    annees_opts = sorted(tmp[annee_col].dropna().unique())
    st.session_state.annees = st.multiselect(
        "Années",
        annees_opts,
        default=[x for x in st.session_state.annees if x in annees_opts]
    )

    if st.session_state.annees:
        tmp = tmp[tmp[annee_col].isin(st.session_state.annees)]

    # 6. Équipes
    equipes_opts = sorted(tmp[equipe_col].dropna().unique())
    st.session_state.equipes = st.multiselect(
        "Équipes",
        equipes_opts,
        default=[x for x in st.session_state.equipes if x in equipes_opts]
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(
        "Proposé par le groupe **DATALAKE** : Kumar Guha, Daniel Da Silva et Andréa Nebot  \n"
        "à la demande de Luigi Liquori et Maria Kazolea"
    )

# -------------------
# Filtrage final
# -------------------
def get_filtered_df():
    tmp = df.copy()
    if st.session_state.centres:
        tmp = tmp[tmp[centre_col].isin(st.session_state.centres)]
    if st.session_state.pays:
        tmp = tmp[tmp[pays_col].isin(st.session_state.pays)]
    if st.session_state.villes != "Toutes":
        tmp = tmp[tmp[ville_col] == st.session_state.villes]
    if st.session_state.organismes:
        tmp = tmp[tmp[org_col].isin(st.session_state.organismes)]
    if st.session_state.annees:
        tmp = tmp[tmp[annee_col].isin(st.session_state.annees)]
    if st.session_state.equipes:
        tmp = tmp[tmp[equipe_col].isin(st.session_state.equipes)]
    return tmp

df_filtered = get_filtered_df()

# -------------------
# Fonctions utiles
# -------------------
@st.cache_data(ttl=300)
def compute_yearly(df):
    return df.groupby(annee_col)[hal_col].nunique().reset_index()

@st.cache_data(ttl=300)
def compute_top(df, col, n=10):
    return df[col].value_counts().nlargest(n)

@st.cache_data(ttl=300)
def build_graph(df, max_nodes=200):
    G = nx.Graph()
    subset = df.head(max_nodes)
    for _, row in subset.dropna(subset=[auteurs_fr_col, auteurs_copub_col, ville_col]).iterrows():
        G.add_node(row[auteurs_fr_col], type="Inria")
        G.add_node(row[auteurs_copub_col], type="Copubliant")
        G.add_node(row[ville_col], type="Ville")
        G.add_node(row[pays_col], type="Pays")
        G.add_edge(row[auteurs_fr_col], row[auteurs_copub_col])
        G.add_edge(row[auteurs_copub_col], row[ville_col])
    pos = nx.spring_layout(G, k=0.3, iterations=10, seed=42)
    return G, pos

@st.cache_data
def make_wordcloud(text):
    wc = WordCloud(width=800, height=400, background_color="white" if not is_dark else "#004280",
                   colormap="tab10").generate(text)
    return wc

# -------------------
# Titre principal
# -------------------
st.title("Copublications d'auteurs Inria (Sophia & Bordeaux)")

# -------------------
# Tabs
# -------------------
tab1, tab2, tab3, tab4 = st.tabs(["Visualisation générale", "Réseau de copublication", "Carte du monde", "Contact"])


# -------------------
# Onglet 1 : Dashboard
# -------------------
with tab1:
    st.subheader("Indicateurs clés")
    pubs_year = compute_yearly(df_filtered)
    total_pubs = pubs_year[hal_col].sum()
    total_villes = df_filtered[ville_col].nunique()
    total_pays = df_filtered[pays_col].nunique()
    total_auteurs_inria = df_filtered[auteurs_fr_col].nunique()
    total_auteurs_copub = df_filtered[auteurs_copub_col].nunique()
    pubs_par_centre = df_filtered.groupby(centre_col)[hal_col].nunique()
    pubs_bordeaux = df_filtered[df_filtered[centre_col] == "Bordeaux"][hal_col].nunique()
    pubs_sophia = df_filtered[df_filtered[centre_col] == "Sophia"][hal_col].nunique()

    kpi_data = [
        ("Publications", total_pubs),
        ("Pays", total_pays),
        ("Villes", total_villes),
        ("Auteurs Inria", total_auteurs_inria),
        ("Auteurs copubliants", total_auteurs_copub),     
        ("Bordeaux", pubs_bordeaux),
        ("Sophia", pubs_sophia),
    ]

    cols = st.columns(len(kpi_data))
    for col, (label, value) in zip(cols, kpi_data):
        col.metric(label, int(value))

    st.markdown("---")

    st.subheader("Publications par années")

# Palette de bleus moderne (de clair à foncé)
    blue_scale = px.colors.sequential.Blues  # dégradé intégré Plotly

    fig_year = px.bar(
        pubs_year,
        x=annee_col,
        y=hal_col,
        color=hal_col,  # Couleur en fonction du nombre de publications
        text_auto=True,
        color_continuous_scale=blue_scale,   # Dégradé de bleus
    )

#  Barres arrondies + style hover
    fig_year.update_traces(
        marker_line_width=0,
        hovertemplate='<b>Année</b>: %{x}<br><b>Publications</b>: %{y}',
        width=0.6,
    )

#  Layout moderne
    fig_year.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,  # Cache la légende du gradient
        xaxis=dict(
            title="Année",
            showgrid=False,
            zeroline=False,
            tickangle=-30,
        ),
        yaxis=dict(
            title="Nombre de publications",
            showgrid=True,
            gridcolor="rgba(200,200,200,0.2)",
        ),
        font=dict(size=14),
        bargap=0.25,
    )

#  Ajout d’un effet arrondi visuel avec des coins doux (via shape + opacity)
    fig_year.update_traces(marker=dict(cornerradius=8))  # nécessite plotly >=5.20

    st.plotly_chart(fig_year, use_container_width=True)




    # ---------- TOP 10 ----------
    st.subheader("TOP 10")
    top_villes = compute_top(df_filtered, ville_col)
    top_pays = compute_top(df_filtered, pays_col)
    top_orgs = compute_top(df_filtered, org_col)

    #  Ligne 1 : Villes & Pays côte à côte
    col1, col2 = st.columns(2)

    fig_villes = go.Figure(go.Pie(labels=top_villes.index, values=top_villes.values, hole=0.4,
                                  marker_colors=px.colors.sequential.Teal[:len(top_villes)],
                                  textinfo='label+percent'))
    fig_villes.update_layout(title="Villes copubliantes", title_x=0.5)
    col1.plotly_chart(fig_villes, use_container_width=True)

    fig_pays = go.Figure(go.Pie(labels=top_pays.index, values=top_pays.values, hole=0.4,
                                marker_colors=px.colors.sequential.Teal[:len(top_pays)],
                                textinfo='label+percent'))
    fig_pays.update_layout(title="Pays", title_x=0.5)
    col2.plotly_chart(fig_pays, use_container_width=True)

    #  Ligne 2 : Organismes centré
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    fig_orgs = go.Figure(go.Pie(labels=top_orgs.index, values=top_orgs.values, hole=0.4,
                                marker_colors=px.colors.sequential.Teal[:len(top_orgs)],
                                textinfo='label+percent'))
    fig_orgs.update_layout(title="Organismes copubliants", title_x=0.5)
    st.plotly_chart(fig_orgs, use_container_width=False)  # pas full width pour le centrer
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- WordCloud ----------
    if "Mots-cles" in df_filtered.columns and st.button("Générer le WordCloud"):
        text = " ".join(df_filtered["Mots-cles"].dropna().astype(str))
        if text:
            wc = make_wordcloud(text)
            fig_wc, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig_wc)

# -------------------
# Onglet 2 : Réseau copublication complet
# -------------------
with tab2:
    st.header("Réseau de copublication complet")
    if st.button("Générer le réseau"):
        G = nx.Graph()

        # Centres à afficher
        centres = ["Bordeaux", "Sophia"]

        # Comptage publications
        pub_ville = df_filtered.groupby(ville_col).size().to_dict()
        pub_pays = df_filtered.groupby("Pays").size().to_dict()
        pub_centre = df_filtered.groupby(centre_col).size().to_dict()

        # Palette RGBA personnalisée
        palette = [
            [255,128,0,180], [255,255,0,180], [128,255,0,180], [0,255,0,180],
            [0,255,128,180], [0,255,255,180], [0,128,255,180], [128,0,255,180],
            [255,0,255,180], [255,0,128,180]
        ]
        palette_hex = [f'rgba({r},{g},{b},{a/255})' for r,g,b,a in palette]

        # Tous les nœuds uniques pour attribuer une couleur
        unique_nodes = list(set(df_filtered[ville_col].dropna().tolist() +
                                df_filtered["Pays"].dropna().tolist() +
                                centres))
        node_color_map = {node: palette_hex[i % len(palette_hex)] for i, node in enumerate(unique_nodes)}

        # Ajouter les centres
        for centre in centres:
            G.add_node(centre, type="Centre", pub_count=pub_centre.get(centre, 0))

        # Ajouter tous les Pays et toutes les Villes
        for _, row in df_filtered.dropna(subset=[centre_col, ville_col, "Pays"]).iterrows():
            G.add_node(row["Pays"], type="Pays", pub_count=pub_pays.get(row["Pays"], 1))
            G.add_node(row[ville_col], type="Ville", pub_count=pub_ville.get(row[ville_col], 1))
            G.add_edge(row[centre_col], row["Pays"], weight=1)
            G.add_edge(row["Pays"], row[ville_col], weight=1)

        # Positionnement
        pos = nx.spring_layout(G, k=0.5, iterations=100, seed=42)

        # Arêtes
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines",
            showlegend=False
        )

        # Création des nœuds avec labels pour Centres et Pays
        node_x, node_y, node_text, node_size, node_color, node_labels = [], [], [], [], [], []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            pub_count = G.nodes[node].get("pub_count", 1)
            node_text.append(f"{node} ({G.nodes[node]['type']}) - {pub_count} publications")
            node_size.append(10 + pub_count*2)
            node_color.append(node_color_map[node])
            node_labels.append(node if G.nodes[node]['type'] in ["Centre", "Pays"] else "")

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=node_labels,
            textposition="top center",
            hovertext=node_text,
            hoverinfo="text",
            marker=dict(color=node_color, size=node_size, line_width=2),
            showlegend=False
        )

        # Figure finale avec grande taille
        fig_net = go.Figure(data=[edge_trace, node_trace],
                             layout=go.Layout(
                                 title="Réseau Centres ↔ Pays ↔ Villes",
                                 hovermode="closest",
                                 plot_bgcolor="#ffffff",
                                 paper_bgcolor="#ffffff",
                                 width=1600,
                                 height=900
                             ))
        st.plotly_chart(fig_net, use_container_width=True)

# ----------------------
# onglet 3
# ----------------------
with tab3:
    # ----------------------
    # Préparer les données
    # ----------------------
    df_map = df_filtered.dropna(subset=["Latitude", "Longitude", "Ville", "HalID"])

    cities_df = df_map.groupby("Ville").agg({
        "Latitude": "mean",
        "Longitude": "mean",
        "HalID": "count"
    }).reset_index()

    cities_df.rename(columns={
        "Latitude": "lat",
        "Longitude": "lon",
        "Ville": "name",
        "HalID": "count"
    }, inplace=True)

    # ----------------------
    # Top 100 villes en bleu
    # ----------------------
    top100_cities = cities_df.nlargest(100, "count")["name"].tolist()

    # ----------------------
    # Taille des cercles
    # ----------------------
    def compute_radius(row):
        base_radius = math.sqrt(row["count"]) * 3000
        if row["name"] in top100_cities:
            return base_radius * 1.5
        return base_radius

    cities_df["radius"] = cities_df.apply(compute_radius, axis=1)

    # ----------------------
    # Palette pour les autres villes
    # ----------------------
    palette = [
        [255,128,0,180], [255,255,0,180], [128,255,0,180], [0,255,0,180],
        [0,255,128,180], [0,255,255,180], [0,128,255,180], [128,0,255,180],
        [255,0,255,180], [255,0,128,180]
    ]
    colors = []
    for _, row in cities_df.iterrows():
        if row["name"] in top100_cities:
            colors.append([0,0,255,200])
        else:
            colors.append(random.choice(palette))
    cities_df["color"] = colors

    # ----------------------
    # Centres Inria (texte seulement)
    # ----------------------
    inria_centers = [
        {"name": "Bordeaux", "lat": 44.833328, "lon": -0.56667},
        {"name": "Sophia", "lat": 43.6200, "lon": 7.0500}
    ]
    centers_df = pd.DataFrame(inria_centers)

    text_layer = pdk.Layer(
        "TextLayer",
        data=centers_df,
        get_position=["lon","lat"],
        get_text="name",
        get_size=40,               # taille plus grande pour visibilité
        get_color=[0,255,0],
        get_alignment_baseline="bottom",
        get_pixel_offset=[0, -20], # décale le texte au-dessus des cercles
        billboard=True,
        pickable=True
    )

    # ----------------------
    # ScatterplotLayer pour toutes les villes
    # ----------------------
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        cities_df,
        pickable=True,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=5,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position=["lon","lat"],
        get_radius="radius",
        get_fill_color="color",
        get_line_color=[0,0,0],
    )

    # ----------------------
    # ViewState
    # ----------------------
    view_state = pdk.ViewState(
        latitude=df_map["Latitude"].mean(),
        longitude=df_map["Longitude"].mean(),
        zoom=5,
        pitch=45,
        bearing=0
    )

    # ----------------------
    # Deck
    # ----------------------
    deck = pdk.Deck(
        layers=[text_layer, scatter_layer], # TextLayer avant pour être visible
        initial_view_state=view_state,
        map_style=pdk.map_styles.CARTO_DARK,
        tooltip={"html": "<b>{name}</b><br>Publications: {count}"}
    )

    st.pydeck_chart(deck)

# -------------------
# Onglet 4 : Contact
# -------------------
with tab4:
    st.header("À propos de nous")
    st.markdown("""
    Le groupe **Datalake**, créé en 2022, travaille à rendre possible le croisement de données entre **HAL** et divers référentiels,
    de développer des outils et méthodes d’analyse et de prospection pour permettre à différents acteurs décisionnaires (**ADS, DPE, etc.**) ou scientifiques
    de répondre à leurs préoccupations du moment.  
    Il est constitué de **6 membres** aux profils de data scientistes, développeurs et documentalistes experts.
    """)
    st.markdown("---")
    st.header("📬 Formulaire de contact")
    with st.form("contact_form", clear_on_submit=True):
        nom = st.text_input("Votre nom")
        email = st.text_input("Votre email")
        message = st.text_area("Votre message")
        submitted = st.form_submit_button("Envoyer")
        if submitted:
            if not nom or not email or not message:
                st.error("⚠️ Merci de remplir tous les champs.")
            else:
                st.success(f"Merci {nom} ! Votre message a bien été envoyé ✅")
