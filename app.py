import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

# -------------------
# Page config
# -------------------
st.set_page_config(page_title="Copublications Inria", layout="wide")

# -------------------
# Détection du thème actuel
# -------------------
theme = st.get_option("theme.base")  # 'light' ou 'dark'
is_dark = theme == "dark"

# -------------------
# Load data
# -------------------
@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath)

    # nettoyage de noms de colonnes
    df.columns = [str(c).strip().replace("\xa0", "").replace(" ", "_") for c in df.columns]

    # Harmonisation vers des colonnes "dashboard" stables
    # (on renomme seulement si la source existe)
    mapping = {
        # Identifiants / année
        "Hal_ID": "HalID",
        "HalID": "HalID",
        "Annee": "Année",
        "Année": "Année",
        "year_halinria": "Année",
        "year": "Année",

        # Centres / équipes
        "Centre_inria": "Centre",
        "Centre": "Centre",
        "Centre_halinria": "Centre",
        "Equipe_inria": "Equipe",
        "Equipe": "Equipe",
        "acronym_halinria": "Equipe",

        # Auteurs
        "Auteur_Inria": "Auteurs_Inria",
        "Auteur_inria": "Auteurs_Inria",
        "Auteurs_FR": "Auteurs_Inria",
        "Auteur_coauteur": "Coauteurs",
        "Auteur_etranger": "Coauteurs",
        "Auteur_international": "Coauteurs",
        "Auteurs_copubliants": "Coauteurs",

        # Organisations / pays
        "Nom_org_copubliant": "Organisme_copubliant",
        "Nom_org_Top_copubliant": "Organisme_copubliant",
        "Organisme_copubliant": "Organisme_copubliant",
        "Nom_Pays_org_copubliant": "Pays",
        "Pays": "Pays",
        "Code_Pays_orgs_copubliant": "Code_Pays",

        # Nouvelles colonnes
        "Type_copublication": "Type_copublication",
        "Copub_scope_int": "Type_copublication",
        "Copub_scope": "Type_copublication",
        "Fonction_auteur_inria": "Fonction_auteur_inria",
        "authQuality_s_halinria": "Fonction_auteur_inria",
        "Fonction_coauteur": "Fonction_coauteur",
        "authQuality_s_int": "Fonction_coauteur",
    }

    for src, tgt in mapping.items():
        if src in df.columns:
            df = df.rename(columns={src: tgt})

    # Normalisations utiles
    if "Année" in df.columns:
        df["Année"] = pd.to_numeric(df["Année"], errors="coerce")

    # si Pays manquant mais Code_Pays présent, on garde au moins le code
    if "Pays" not in df.columns and "Code_Pays" in df.columns:
        df["Pays"] = df["Code_Pays"]

    return df


FILEPATH = "copublications_Inria_MS.xlsx"
df = load_data(FILEPATH)

if df.empty:
    st.error("Aucune donnée trouvée dans le fichier Excel.")
    st.stop()

# -------------------
# Colonnes "cibles" du dashboard
# -------------------
hal_col = "HalID" if "HalID" in df.columns else None
annee_col = "Année" if "Année" in df.columns else None
centre_col = "Centre" if "Centre" in df.columns else None
equipe_col = "Equipe" if "Equipe" in df.columns else None
pays_col = "Pays" if "Pays" in df.columns else None
org_col = "Organisme_copubliant" if "Organisme_copubliant" in df.columns else None
auteurs_inria_col = "Auteurs_Inria" if "Auteurs_Inria" in df.columns else None
coauteurs_col = "Coauteurs" if "Coauteurs" in df.columns else None

type_copub_col = "Type_copublication" if "Type_copublication" in df.columns else None
func_inria_col = "Fonction_auteur_inria" if "Fonction_auteur_inria" in df.columns else None
func_coauteur_col = "Fonction_coauteur" if "Fonction_coauteur" in df.columns else None

missing_core = [x for x in [hal_col, annee_col, centre_col, pays_col, org_col] if x is None]
if missing_core:
    st.warning(
        "Certaines colonnes clés n'ont pas été trouvées. "
        "Le dashboard peut être partiellement dégradé.\n\n"
        f"Colonnes trouvées: {list(df.columns)}"
    )

# -------------------
# Sidebar filtres (sans Villes)
# -------------------
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        st.caption("Logo manquant")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### DATALAKE")
    st.markdown("<br>", unsafe_allow_html=True)

    # clés session_state
    for key in ["centres", "pays", "organismes", "annees", "equipes", "type_copub", "fonctions_inria", "fonctions_coauteur"]:
        if key not in st.session_state:
            st.session_state[key] = []

    tmp = df.copy()

    # 1) Centres (tous)
    if centre_col:
        centres_opts = sorted(tmp[centre_col].dropna().unique())
        st.session_state.centres = st.multiselect(
            "Centre",
            centres_opts,
            default=[x for x in st.session_state.centres if x in centres_opts]
        )
        if st.session_state.centres:
            tmp = tmp[tmp[centre_col].isin(st.session_state.centres)]

    # 2) Pays
    if pays_col:
        pays_opts = sorted(tmp[pays_col].dropna().unique())
        st.session_state.pays = st.multiselect(
            "Pays",
            pays_opts,
            default=[x for x in st.session_state.pays if x in pays_opts]
        )
        if st.session_state.pays:
            tmp = tmp[tmp[pays_col].isin(st.session_state.pays)]

    # 3) Organismes copubliants
    if org_col:
        orgs_opts = sorted(tmp[org_col].dropna().unique())
        st.session_state.organismes = st.multiselect(
            "Organismes copubliants",
            orgs_opts,
            default=[x for x in st.session_state.organismes if x in orgs_opts]
        )
        if st.session_state.organismes:
            tmp = tmp[tmp[org_col].isin(st.session_state.organismes)]

    # 4) Années
    if annee_col:
        annees_opts = sorted([int(x) for x in tmp[annee_col].dropna().unique() if pd.notna(x)])
        st.session_state.annees = st.multiselect(
            "Années",
            annees_opts,
            default=[x for x in st.session_state.annees if x in annees_opts]
        )
        if st.session_state.annees:
            tmp = tmp[tmp[annee_col].isin(st.session_state.annees)]

    # 5) Équipes
    if equipe_col:
        equipes_opts = sorted(tmp[equipe_col].dropna().unique())
        st.session_state.equipes = st.multiselect(
            "Équipes",
            equipes_opts,
            default=[x for x in st.session_state.equipes if x in equipes_opts]
        )
        if st.session_state.equipes:
            tmp = tmp[tmp[equipe_col].isin(st.session_state.equipes)]

    # 6) Type copublication (si dispo)
    if type_copub_col:
        type_opts = sorted(tmp[type_copub_col].dropna().unique())
        st.session_state.type_copub = st.multiselect(
            "Type de copublication",
            type_opts,
            default=[x for x in st.session_state.type_copub if x in type_opts]
        )
        if st.session_state.type_copub:
            tmp = tmp[tmp[type_copub_col].isin(st.session_state.type_copub)]

    # 7) Fonction auteur Inria (si dispo)
    if func_inria_col:
        finria_opts = sorted(tmp[func_inria_col].dropna().unique())
        st.session_state.fonctions_inria = st.multiselect(
            "Fonction auteur Inria",
            finria_opts,
            default=[x for x in st.session_state.fonctions_inria if x in finria_opts]
        )
        if st.session_state.fonctions_inria:
            tmp = tmp[tmp[func_inria_col].isin(st.session_state.fonctions_inria)]

    # 8) Fonction co-auteur (si dispo)
    if func_coauteur_col:
        fco_opts = sorted(tmp[func_coauteur_col].dropna().unique())
        st.session_state.fonctions_coauteur = st.multiselect(
            "Fonction co-auteur",
            fco_opts,
            default=[x for x in st.session_state.fonctions_coauteur if x in fco_opts]
        )
        if st.session_state.fonctions_coauteur:
            tmp = tmp[tmp[func_coauteur_col].isin(st.session_state.fonctions_coauteur)]

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(
        "Proposé par le groupe **DATALAKE** : Kumar Guha, Daniel Da Silva et Andréa Nebot  \n"
        "à la demande de Luigi Liquori et Maria Kazolea"
    )

# -------------------
# Filtrage final
# -------------------
def get_filtered_df() -> pd.DataFrame:
    tmp2 = df.copy()

    if centre_col and st.session_state.centres:
        tmp2 = tmp2[tmp2[centre_col].isin(st.session_state.centres)]

    if pays_col and st.session_state.pays:
        tmp2 = tmp2[tmp2[pays_col].isin(st.session_state.pays)]

    if org_col and st.session_state.organismes:
        tmp2 = tmp2[tmp2[org_col].isin(st.session_state.organismes)]

    if annee_col and st.session_state.annees:
        tmp2 = tmp2[tmp2[annee_col].isin(st.session_state.annees)]

    if equipe_col and st.session_state.equipes:
        tmp2 = tmp2[tmp2[equipe_col].isin(st.session_state.equipes)]

    if type_copub_col and st.session_state.type_copub:
        tmp2 = tmp2[tmp2[type_copub_col].isin(st.session_state.type_copub)]

    if func_inria_col and st.session_state.fonctions_inria:
        tmp2 = tmp2[tmp2[func_inria_col].isin(st.session_state.fonctions_inria)]

    if func_coauteur_col and st.session_state.fonctions_coauteur:
        tmp2 = tmp2[tmp2[func_coauteur_col].isin(st.session_state.fonctions_coauteur)]

    return tmp2


df_filtered = get_filtered_df()

# -------------------
# Fonctions utiles
# -------------------
@st.cache_data(ttl=300)
def compute_yearly(df_in: pd.DataFrame) -> pd.DataFrame:
    if annee_col is None or hal_col is None:
        return pd.DataFrame(columns=["Année", "Publications"])
    out = df_in.dropna(subset=[annee_col]).groupby(annee_col)[hal_col].nunique().reset_index()
    out.columns = [annee_col, "Publications"]
    return out.sort_values(annee_col)

@st.cache_data(ttl=300)
def compute_top(df_in: pd.DataFrame, col: str, n=10) -> pd.Series:
    if col is None or col not in df_in.columns:
        return pd.Series(dtype=int)
    return df_in[col].value_counts().nlargest(n)

@st.cache_data(ttl=300)
def build_graph_centres_pays(df_in: pd.DataFrame, max_edges=2000):
    """
    Réseau Centre ↔ Pays (sans villes).
    """
    if centre_col is None or pays_col is None:
        return None, None

    G = nx.Graph()
    sub = df_in.dropna(subset=[centre_col, pays_col]).head(max_edges)

    # poids = nombre de lignes (ou publications) par couple
    weights = sub.groupby([centre_col, pays_col]).size().reset_index(name="w")

    for _, r in weights.iterrows():
        c = r[centre_col]
        p = r[pays_col]
        w = int(r["w"])
        G.add_node(c, node_type="Centre")
        G.add_node(p, node_type="Pays")
        G.add_edge(c, p, weight=w)

    pos = nx.spring_layout(G, k=0.6, iterations=50, seed=42)
    return G, pos


# -------------------
# Titre principal
# -------------------
st.title("Copublications d'auteurs Inria")

# -------------------
# Tabs
# -------------------
tab1, tab2, tab3, tab4 = st.tabs(["Visualisation générale", "Réseau Centre ↔ Pays", "Carte du monde (Pays)", "Contact"])

# -------------------
# Onglet 1 : Dashboard
# -------------------
with tab1:
    st.subheader("Indicateurs clés")

    pubs_year = compute_yearly(df_filtered)
    total_pubs = int(pubs_year["Publications"].sum()) if not pubs_year.empty else 0

    total_centres = df_filtered[centre_col].nunique() if centre_col else 0
    total_pays = df_filtered[pays_col].nunique() if pays_col else 0
    total_orgs = df_filtered[org_col].nunique() if org_col else 0
    total_auteurs_inria = df_filtered[auteurs_inria_col].nunique() if auteurs_inria_col else 0
    total_coauteurs = df_filtered[coauteurs_col].nunique() if coauteurs_col else 0

    kpi_data = [
        ("Publications", total_pubs),
        ("Centres", total_centres),
        ("Pays", total_pays),
        ("Organismes", total_orgs),
        ("Auteurs Inria", total_auteurs_inria),
        ("Co-auteurs", total_coauteurs),
    ]

    cols = st.columns(len(kpi_data))
    for col, (label, value) in zip(cols, kpi_data):
        col.metric(label, int(value))

    st.markdown("---")

    st.subheader("Publications par années")

    if pubs_year.empty:
        st.info("Impossible d'afficher la série temporelle (colonnes Année/HalID manquantes).")
    else:
        fig_year = px.bar(
            pubs_year,
            x=annee_col,
            y="Publications",
            color="Publications",
            text_auto=True,
            color_continuous_scale=px.colors.sequential.Blues,
        )
        fig_year.update_traces(
            marker_line_width=0,
            hovertemplate="<b>Année</b>: %{x}<br><b>Publications</b>: %{y}",
            width=0.6,
        )
        fig_year.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            xaxis=dict(title="Année", showgrid=False, zeroline=False, tickangle=-30),
            yaxis=dict(title="Nombre de publications", showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
            font=dict(size=14),
            bargap=0.25,
        )

        # coins arrondis si plotly >= 5.20
        try:
            fig_year.update_traces(marker=dict(cornerradius=8))
        except Exception:
            pass

        st.plotly_chart(fig_year, use_container_width=True)

    st.subheader("TOP 10")

    top_pays = compute_top(df_filtered, pays_col, n=10)
    top_orgs = compute_top(df_filtered, org_col, n=10)
    top_centres = compute_top(df_filtered, centre_col, n=10)

    col1, col2, col3 = st.columns(3)

    if not top_centres.empty:
        fig_centres = go.Figure(go.Pie(
            labels=top_centres.index,
            values=top_centres.values,
            hole=0.4,
            textinfo="label+percent"
        ))
        fig_centres.update_layout(title="Centres", title_x=0.5)
        col1.plotly_chart(fig_centres, use_container_width=True)
    else:
        col1.info("Top centres indisponible.")

    if not top_pays.empty:
        fig_pays = go.Figure(go.Pie(
            labels=top_pays.index,
            values=top_pays.values,
            hole=0.4,
            textinfo="label+percent"
        ))
        fig_pays.update_layout(title="Pays", title_x=0.5)
        col2.plotly_chart(fig_pays, use_container_width=True)
    else:
        col2.info("Top pays indisponible.")

    if not top_orgs.empty:
        fig_orgs = go.Figure(go.Pie(
            labels=top_orgs.index,
            values=top_orgs.values,
            hole=0.4,
            textinfo="label+percent"
        ))
        fig_orgs.update_layout(title="Organismes copubliants", title_x=0.5)
        col3.plotly_chart(fig_orgs, use_container_width=True)
    else:
        col3.info("Top organismes indisponible.")

    st.markdown("---")
    st.subheader("Aperçu des données filtrées")
    st.dataframe(df_filtered, use_container_width=True)

# -------------------
# Onglet 2 : Réseau Centre ↔ Pays
# -------------------
with tab2:
    st.header("Réseau Centre ↔ Pays")

    if centre_col is None or pays_col is None:
        st.warning("Colonnes Centre/Pays absentes. Réseau indisponible.")
    else:
        if st.button("Générer le réseau"):
            G, pos = build_graph_centres_pays(df_filtered, max_edges=5000)
            if G is None or len(G.nodes) == 0:
                st.info("Pas assez de données pour construire le réseau.")
            else:
                # Arêtes
                edge_x, edge_y = [], []
                edge_w = []
                for u, v, data in G.edges(data=True):
                    x0, y0 = pos[u]
                    x1, y1 = pos[v]
                    edge_x += [x0, x1, None]
                    edge_y += [y0, y1, None]
                    edge_w.append(data.get("weight", 1))

                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=0.7, color="#888"),
                    hoverinfo="none",
                    mode="lines",
                    showlegend=False
                )

                # Nœuds
                node_x, node_y, node_text, node_size, node_labels = [], [], [], [], []
                node_color = []
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    ntype = G.nodes[node].get("node_type", "Other")
                    deg = G.degree(node)
                    node_size.append(10 + deg * 2)

                    node_text.append(f"{node} ({ntype}) - connexions: {deg}")
                    node_labels.append(node if ntype == "Centre" else "")  # labels uniquement pour centres

                    # couleurs simples selon type
                    node_color.append("#0484fc" if ntype == "Centre" else "#faa48a")

                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode="markers+text",
                    text=node_labels,
                    textposition="top center",
                    hovertext=node_text,
                    hoverinfo="text",
                    marker=dict(color=node_color, size=node_size, line_width=1),
                    showlegend=False
                )

                fig_net = go.Figure(
                    data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title="Réseau Centres ↔ Pays",
                        hovermode="closest",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=850
                    )
                )
                st.plotly_chart(fig_net, use_container_width=True)

# ----------------------
# Onglet 3 : Carte du monde (Pays) - Choropleth
# ----------------------
with tab3:
    st.header("Carte du monde (par pays)")

    if pays_col is None:
        st.warning("Colonne Pays absente. Carte indisponible.")
    else:
        counts = df_filtered[pays_col].dropna().value_counts().reset_index()
        counts.columns = ["Pays", "Nb_lignes"]

        # IMPORTANT : Plotly choropleth marche mieux avec codes ISO-3.
        # Si ton fichier contient des noms de pays en français, Plotly peut parfois échouer.
        # Dans ce cas, il est préférable d'avoir une colonne ISO-3 (ex: FRA, USA, DEU).
        #
        # Ici on tente:
        # - si Code_Pays existe et ressemble à ISO-3, on l'utilise
        use_iso = ("Code_Pays" in df_filtered.columns) and df_filtered["Code_Pays"].astype(str).str.len().dropna().isin([3]).any()

        if use_iso:
            iso_counts = df_filtered.dropna(subset=["Code_Pays"]).groupby("Code_Pays").size().reset_index(name="Nb_lignes")
            fig_map = px.choropleth(
                iso_counts,
                locations="Code_Pays",
                color="Nb_lignes",
                hover_name="Code_Pays",
                color_continuous_scale=px.colors.sequential.Blues,
            )
            fig_map.update_layout(
                geo=dict(showframe=False, showcoastlines=True),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig_map, use_container_width=True)
            st.caption("Carte basée sur Code_Pays (si ISO-3).")
        else:
            st.info(
                "Je n'ai pas détecté de codes ISO-3 fiables. "
                "J'affiche plutôt un TOP pays (bar chart). "
                "Si tu ajoutes une colonne ISO-3 (ex: FRA/USA/DEU), la choroplèthe s’activera."
            )
            top = counts.head(30)
            fig_bar = px.bar(top, x="Nb_lignes", y="Pays", orientation="h")
            fig_bar.update_layout(yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig_bar, use_container_width=True)

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