import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# -------------------
# Page config
# -------------------
st.set_page_config(page_title="Copublications IES Médiation scientifique", layout="wide")

st.markdown(
    """
    <style>
      /* =========
         PALETTE
         ========= */
      :root{
        --dl-sidebar-bg: #dff9fb;   /* ta couleur demandée */
        --dl-primary: #0484fc;
        --dl-primary-2: #00a8ff;
        --dl-accent: #4cada3;
        --dl-text: #0b2239;
        --dl-muted: rgba(11,34,57,.65);
        --dl-card: rgba(255,255,255,.70);
        --dl-border: rgba(4,132,252,.18);
        --dl-shadow: 0 12px 30px rgba(4, 132, 252, .18);
        --dl-radius: 18px;
      }

      /* =========================
         SIDEBAR: fond
         ========================= */
      section[data-testid="stSidebar"]{
        background: var(--dl-sidebar-bg);
        border-right: 1px solid var(--dl-border);
      }

      /* ✅ IMPORTANT: ne pas casser le scroll
         - On supprime overflow:hidden
         - On n’utilise pas margin sur le wrapper principal
      */
      section[data-testid="stSidebar"] > div{
        height: 100%;
        padding: 12px;
        box-sizing: border-box;
      }

      /* ✅ Carte interne (arrondi + ombre) qui scrolle si nécessaire */
      section[data-testid="stSidebar"] .stSidebarContent{
        border-radius: var(--dl-radius);
        box-shadow: var(--dl-shadow);
        background: linear-gradient(180deg, rgba(255,255,255,.65), rgba(255,255,255,.35));
        border: 1px solid rgba(255,255,255,.55);
        padding: 10px 10px 16px 10px;

        /* ✅ clé pour voir tous les filtres */
        overflow-y: auto;
        max-height: calc(100vh - 24px);
      }

      /* Un peu d’air dans la sidebar */
      section[data-testid="stSidebar"] .stMarkdown,
      section[data-testid="stSidebar"] .stText,
      section[data-testid="stSidebar"] label,
      section[data-testid="stSidebar"] p,
      section[data-testid="stSidebar"] span{
        color: var(--dl-text) !important;
      }

      section[data-testid="stSidebar"] hr{
        border: none;
        border-top: 1px solid rgba(11,34,57,.12);
      }

      /* =========================
         TITRES / HEADERS
         ========================= */
      h1, h2, h3, h4{
        color: var(--dl-text);
      }

      /* =========================
         BOUTONS (st.button)
         ========================= */
      div.stButton > button{
        width: 100%;
        border-radius: 14px !important;
        border: 1px solid rgba(4,132,252,.25) !important;
        background: linear-gradient(135deg, var(--dl-primary), var(--dl-primary-2)) !important;
        color: white !important;
        font-weight: 700 !important;
        padding: .65rem .9rem !important;
        box-shadow: 0 10px 18px rgba(4,132,252,.22) !important;
        transition: transform .08s ease-in-out, box-shadow .12s ease-in-out, filter .12s ease-in-out;
      }
      div.stButton > button:hover{
        filter: brightness(1.03);
        transform: translateY(-1px);
        box-shadow: 0 14px 28px rgba(4,132,252,.28) !important;
      }
      div.stButton > button:active{
        transform: translateY(0px);
        box-shadow: 0 8px 16px rgba(4,132,252,.20) !important;
      }

      /* =========================
         INPUTS (selectbox/multiselect/slider)
         ========================= */
      section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
      section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
      section[data-testid="stSidebar"] div[data-baseweb="textarea"] > div{
        border-radius: 14px !important;
        border: 1px solid rgba(4,132,252,.18) !important;
        background: rgba(255,255,255,.75) !important;
        box-shadow: 0 8px 18px rgba(4,132,252,.10);
      }

      section[data-testid="stSidebar"] label{
        font-weight: 650 !important;
        color: var(--dl-text) !important;
      }

      section[data-testid="stSidebar"] span[data-baseweb="tag"]{
        background: rgba(4,132,252,.12) !important;
        border: 1px solid rgba(4,132,252,.18) !important;
        color: var(--dl-text) !important;
        border-radius: 999px !important;
      }

      section[data-testid="stSidebar"] div[data-testid="stSlider"] [data-baseweb="slider"] > div{
        color: var(--dl-primary);
      }

      /* =========================
         METRICS (KPI cards)
         ========================= */
      div[data-testid="stMetric"]{
        border-radius: 16px;
        padding: 12px 14px;
        border: 1px solid rgba(4,132,252,.14);
        background: rgba(255,255,255,.65);
        box-shadow: 0 10px 22px rgba(4,132,252,.10);
      }

      /* =========================
         DATAFRAME (table)
         ========================= */
      div[data-testid="stDataFrame"]{
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(4,132,252,.14);
        box-shadow: 0 14px 28px rgba(4,132,252,.08);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------
# Détection du thème actuel
# -------------------
theme = st.get_option("theme.base")  # 'light' ou 'dark'
is_dark = theme == "dark"

# -------------------
# Helpers robustes
# -------------------
def safe_series(df: pd.DataFrame, col: str) -> pd.Series | None:
    """
    Retourne une Series df[col] même si:
    - il y a des colonnes en doublon (df[col] => DataFrame)
    - col n'existe pas
    """
    if col is None or col not in df.columns:
        return None

    x = df[col]
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    return x


def make_unique_columns(cols) -> list[str]:
    """
    Rend les noms de colonnes uniques en ajoutant _2, _3, ... si nécessaire.
    Indispensable pour éviter l'erreur pyarrow/streamlit "Duplicate column names found".
    """
    seen = {}
    new_cols = []
    for c in cols:
        c = str(c)
        if c not in seen:
            seen[c] = 1
            new_cols.append(c)
        else:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
    return new_cols


def as_int(x, default=0) -> int:
    """
    Convertit proprement en int même si x est Series/DataFrame/NaN.
    Utile pour éviter: TypeError: cannot convert the series to int
    """
    try:
        if x is None:
            return default
        if isinstance(x, pd.Series):
            x = x.sum()
        if isinstance(x, pd.DataFrame):
            x = x.to_numpy().sum()
        if pd.isna(x):
            return default
        return int(x)
    except Exception:
        return default


@st.cache_data(ttl=300)
def make_wordcloud(text: str, is_dark: bool):
    return WordCloud(
        width=1200,
        height=600,
        background_color="#004280" if is_dark else "white",
        collocations=False
    ).generate(text)


# -------------------
# Load data
# -------------------
@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath)

    # Nettoyage de noms de colonnes
    df.columns = [str(c).strip().replace("\xa0", "").replace(" ", "_") for c in df.columns]
    df.columns = make_unique_columns(df.columns)  # ✅ unique après nettoyage

    # Harmonisation vers des colonnes "dashboard" stables
    mapping = {
        # Identifiants / année
        "Hal_ID": "HalID",
        "Annee": "Année",
        "year_halinria": "Année",
        "year": "Année",

        # Centres / équipes
        "Centre_inria": "Centre",
        "Centre_halinria": "Centre",
        "Equipe_inria": "Equipe",
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
        "Nom_Pays_org_copubliant": "Pays",
        "Code_Pays_orgs_copubliant": "Code_Pays",

        # Nouvelles colonnes
        "Copub_scope_int": "Type_copublication",
        "Copub_scope": "Type_copublication",
        "authQuality_s_halinria": "Fonction_auteur_inria",
        "authQuality_s_int": "Fonction_coauteur",
    }

    # Renommage prudent (évite collisions)
    for src, tgt in mapping.items():
        if src in df.columns and tgt not in df.columns:
            df = df.rename(columns={src: tgt})

    # ✅ unique après renommages (évite collisions)
    df.columns = make_unique_columns(df.columns)

    # Normalisations utiles
    if "Année" in df.columns:
        df["Année"] = pd.to_numeric(df["Année"], errors="coerce")

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

# Détection robuste de la colonne Résumé
resume_candidates = ["Resume", "Résumé", "abstract_halinria", "Resume_halinria", "Résumé_halinria"]
resume_col = next((c for c in resume_candidates if c in df.columns), None)
if resume_col is None:
    starts = [c for c in df.columns if str(c).startswith("Resume") or str(c).startswith("Résumé")]
    if starts:
        resume_col = starts[0]

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
        st.image("datalake_image_IA.png", use_container_width=True)
        st.markdown(
    "<div style='height:8px'></div>",
    unsafe_allow_html=True
)
   
    except Exception:
        st.caption("Logo manquant")

 
    for key in [
        "centres", "pays", "organismes", "annees", "equipes",
        "type_copub", "fonctions_inria", "fonctions_coauteur"
    ]:
        if key not in st.session_state:
            st.session_state[key] = []

    tmp = df.copy()

    # 1) Centres
    if centre_col:
        s_centre = safe_series(tmp, centre_col)
        centres_opts = sorted(s_centre.dropna().astype(str).unique()) if s_centre is not None else []
        st.session_state.centres = st.multiselect(
            "Centre",
            centres_opts,
            default=[x for x in st.session_state.centres if x in centres_opts]
        )
        if st.session_state.centres and s_centre is not None:
            tmp = tmp[safe_series(tmp, centre_col).isin(st.session_state.centres)]

    # 2) Pays
    if pays_col:
        s_pays = safe_series(tmp, pays_col)
        pays_opts = sorted(s_pays.dropna().astype(str).unique()) if s_pays is not None else []
        st.session_state.pays = st.multiselect(
            "Pays",
            pays_opts,
            default=[x for x in st.session_state.pays if x in pays_opts]
        )
        if st.session_state.pays and s_pays is not None:
            tmp = tmp[safe_series(tmp, pays_col).isin(st.session_state.pays)]

    # 3) Organismes copubliants
    if org_col:
        s_org = safe_series(tmp, org_col)
        orgs_opts = sorted(s_org.dropna().astype(str).unique()) if s_org is not None else []
        st.session_state.organismes = st.multiselect(
            "Organismes copubliants",
            orgs_opts,
            default=[x for x in st.session_state.organismes if x in orgs_opts]
        )
        if st.session_state.organismes and s_org is not None:
            tmp = tmp[safe_series(tmp, org_col).isin(st.session_state.organismes)]

    # 4) Années
    if annee_col:
        s_annee = safe_series(tmp, annee_col)
        if s_annee is not None:
            annees_vals = pd.to_numeric(s_annee, errors="coerce").dropna()
            annees_opts = sorted([int(x) for x in annees_vals.unique()])
        else:
            annees_opts = []
        st.session_state.annees = st.multiselect(
            "Années",
            annees_opts,
            default=[x for x in st.session_state.annees if x in annees_opts]
        )
        if st.session_state.annees and s_annee is not None:
            tmp = tmp[safe_series(tmp, annee_col).isin(st.session_state.annees)]

    # 5) Équipes
    if equipe_col:
        s_eq = safe_series(tmp, equipe_col)
        equipes_opts = sorted(s_eq.dropna().astype(str).unique()) if s_eq is not None else []
        st.session_state.equipes = st.multiselect(
            "Équipes",
            equipes_opts,
            default=[x for x in st.session_state.equipes if x in equipes_opts]
        )
        if st.session_state.equipes and s_eq is not None:
            tmp = tmp[safe_series(tmp, equipe_col).isin(st.session_state.equipes)]

    # 6) Type copublication
    if type_copub_col:
        s_tc = safe_series(tmp, type_copub_col)
        type_opts = sorted(s_tc.dropna().astype(str).unique()) if s_tc is not None else []
        st.session_state.type_copub = st.multiselect(
            "Type de copublication",
            type_opts,
            default=[x for x in st.session_state.type_copub if x in type_opts]
        )
        if st.session_state.type_copub and s_tc is not None:
            tmp = tmp[safe_series(tmp, type_copub_col).isin(st.session_state.type_copub)]

    # 7) Fonction auteur Inria
    if func_inria_col:
        s_fi = safe_series(tmp, func_inria_col)
        finria_opts = sorted(s_fi.dropna().astype(str).unique()) if s_fi is not None else []
        st.session_state.fonctions_inria = st.multiselect(
            "Fonction auteur Inria",
            finria_opts,
            default=[x for x in st.session_state.fonctions_inria if x in finria_opts]
        )
        if st.session_state.fonctions_inria and s_fi is not None:
            tmp = tmp[safe_series(tmp, func_inria_col).isin(st.session_state.fonctions_inria)]

    # 8) Fonction co-auteur
    if func_coauteur_col:
        s_fc = safe_series(tmp, func_coauteur_col)
        fco_opts = sorted(s_fc.dropna().astype(str).unique()) if s_fc is not None else []
        st.session_state.fonctions_coauteur = st.multiselect(
            "Fonction co-auteur",
            fco_opts,
            default=[x for x in st.session_state.fonctions_coauteur if x in fco_opts]
        )
        if st.session_state.fonctions_coauteur and s_fc is not None:
            tmp = tmp[safe_series(tmp, func_coauteur_col).isin(st.session_state.fonctions_coauteur)]

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(
        "Proposé par le groupe **DATALAKE** "
    )

# -------------------
# Filtrage final
# -------------------
def get_filtered_df() -> pd.DataFrame:
    tmp2 = df.copy()

    if centre_col and st.session_state.centres:
        tmp2 = tmp2[safe_series(tmp2, centre_col).isin(st.session_state.centres)]

    if pays_col and st.session_state.pays:
        tmp2 = tmp2[safe_series(tmp2, pays_col).isin(st.session_state.pays)]

    if org_col and st.session_state.organismes:
        tmp2 = tmp2[safe_series(tmp2, org_col).isin(st.session_state.organismes)]

    if annee_col and st.session_state.annees:
        tmp2 = tmp2[safe_series(tmp2, annee_col).isin(st.session_state.annees)]

    if equipe_col and st.session_state.equipes:
        tmp2 = tmp2[safe_series(tmp2, equipe_col).isin(st.session_state.equipes)]

    if type_copub_col and st.session_state.type_copub:
        tmp2 = tmp2[safe_series(tmp2, type_copub_col).isin(st.session_state.type_copub)]

    if func_inria_col and st.session_state.fonctions_inria:
        tmp2 = tmp2[safe_series(tmp2, func_inria_col).isin(st.session_state.fonctions_inria)]

    if func_coauteur_col and st.session_state.fonctions_coauteur:
        tmp2 = tmp2[safe_series(tmp2, func_coauteur_col).isin(st.session_state.fonctions_coauteur)]

    return tmp2


df_filtered = get_filtered_df()

# ✅ Streamlit/pyarrow refuse les colonnes dupliquées -> on sécurise l'affichage
df_view = df_filtered.copy()
df_view.columns = make_unique_columns(df_view.columns)

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
    s = safe_series(df_in, col)
    if s is None:
        return pd.Series(dtype=int)
    return s.value_counts().nlargest(n)


@st.cache_data(ttl=300)
def build_graph_centres_pays(df_in: pd.DataFrame, max_edges=2000):
    if centre_col is None or pays_col is None:
        return None, None

    G = nx.Graph()
    sub = df_in.dropna(subset=[centre_col, pays_col]).head(max_edges)

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
st.title("Copublications IES - Médiation Scientifique")
# -------------------
# Custom CSS - Sidebar color
# -------------------
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            background-color: #dff9fb;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Tabs
# -------------------
tab1, tab2, tab3, tab_wc, tab4 = st.tabs(
    [
        "Visualisation générale",
        "Réseau Centre ↔ Pays",
        "Carte du monde (Pays)",
        "Wordcloud (Résumé)",
        "Contact",
    ]
)
st.write("DEBUG: tabs OK ✅")
# -------------------
# Onglet 1 : Dashboard
# -------------------
with tab1:
    st.subheader("Indicateurs clés")

    pubs_year = compute_yearly(df_filtered)
    total_pubs = as_int(pubs_year["Publications"].sum()) if not pubs_year.empty else 0

    total_centres = as_int(safe_series(df_filtered, centre_col).nunique()) if centre_col else 0
    total_pays = as_int(safe_series(df_filtered, pays_col).nunique()) if pays_col else 0
    total_orgs = as_int(safe_series(df_filtered, org_col).nunique()) if org_col else 0
    total_auteurs_inria = as_int(safe_series(df_filtered, auteurs_inria_col).nunique()) if auteurs_inria_col else 0
    total_coauteurs = as_int(safe_series(df_filtered, coauteurs_col).nunique()) if coauteurs_col else 0

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
        col.metric(label, as_int(value))

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
    st.dataframe(df_view, use_container_width=True)

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
                edge_x, edge_y = [], []
                for u, v in G.edges():
                    x0, y0 = pos[u]
                    x1, y1 = pos[v]
                    edge_x += [x0, x1, None]
                    edge_y += [y0, y1, None]

                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=0.7, color="#888"),
                    hoverinfo="none",
                    mode="lines",
                    showlegend=False
                )

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
                    node_labels.append(node if ntype == "Centre" else "")
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
# Onglet 3 : Carte du monde (Pays)
# ----------------------
# ----------------------
# Onglet 3 : Carte du monde (Pays) - Nouvelle API Maplibre
# ----------------------
with tab3:
    st.header("Carte du monde (par pays)")

    if pays_col is None:
        st.warning("Colonne Pays absente. Carte indisponible.")
    else:
        s_pays = safe_series(df_filtered, pays_col)

        if s_pays is None:
            st.info("Aucune donnée pays à afficher.")
        else:
            # Comptage par pays
            counts = s_pays.dropna().value_counts().reset_index()
            counts.columns = ["Pays", "Nb_publications"]

            # --- CAS 1 : Si Code_Pays ISO-3 disponible ---
            if "Code_Pays" in df_filtered.columns:

                iso_series = safe_series(df_filtered, "Code_Pays")

                if iso_series is not None:
                    iso_counts = (
                        df_filtered
                        .dropna(subset=["Code_Pays"])
                        .groupby("Code_Pays")
                        .size()
                        .reset_index(name="Nb_publications")
                    )

                    if not iso_counts.empty:

                        fig_map = px.scatter_map(
                            iso_counts,
                            locations="Code_Pays",
                            color="Nb_publications",
                            size="Nb_publications",
                            hover_name="Code_Pays",
                            color_continuous_scale=px.colors.sequential.Blues,
                            zoom=1,
                            height=650,
                        )

                        fig_map.update_layout(
                            map_style="carto-positron",
                            margin=dict(l=0, r=0, t=0, b=0),
                            coloraxis_showscale=True
                        )

                        st.plotly_chart(fig_map, use_container_width=True)
                        st.caption("Carte basée sur Code_Pays (ISO-3) avec Maplibre.")
                    else:
                        st.info("Aucun code ISO exploitable trouvé.")
                else:
                    st.info("Colonne Code_Pays vide ou invalide.")

            # --- CAS 2 : Pas de code ISO -> fallback graphique ---
            else:
                st.info(
                    "Pas de codes ISO-3 détectés. "
                    "Affichage du TOP pays en graphique horizontal."
                )

                top = counts.head(30)

                fig_bar = px.bar(
                    top,
                    x="Nb_publications",
                    y="Pays",
                    orientation="h",
                    color="Nb_publications",
                    color_continuous_scale=px.colors.sequential.Blues,
                    height=650
                )

                fig_bar.update_layout(
                    yaxis=dict(categoryorder="total ascending")
                )

                st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------
# Onglet Wordcloud : Nuage de mots (Résumé)
# ----------------------
with tab_wc:
    st.header("Nuage de mots à partir des résumés")

    if resume_col is None:
        st.warning("Aucune colonne de résumé détectée (Resume/Résumé/...).")
    else:
        max_docs = st.slider("Nombre max de résumés à utiliser", 100, 5000, 1500, step=100)
        min_len = st.slider("Longueur minimale d’un résumé", 20, 500, 60, step=10)

        s = safe_series(df_filtered, resume_col)

        if s is None:
            st.info("Aucun résumé disponible.")
        else:
            s = s.dropna().astype(str)
            s = s[s.str.len() >= min_len]

            if s.empty:
                st.info("Aucun résumé ne respecte les critères (vides ou trop courts).")
            else:
                s = s.head(max_docs)

                text = " ".join(
                    s.str.replace(r"\s+", " ", regex=True)
                     .str.replace(r"[\(\)\[\]\{\}\|_]", " ", regex=True)
                     .tolist()
                )

                if len(text.strip()) < 50:
                    st.info("Pas assez de texte après nettoyage pour générer un nuage de mots.")
                else:
                    wc = make_wordcloud(text, is_dark)

                    fig, ax = plt.subplots(figsize=(14, 7))
                    ax.imshow(wc, interpolation="bilinear")
                    ax.axis("off")
                    st.pyplot(fig)

                    st.caption(f"Le nuage de mots est généré à partir de la colonne **{resume_col}** (après filtres).")

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