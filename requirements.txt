# 📊 Copublications Inria-Italie

Application **Streamlit** interactive permettant d’explorer et de visualiser les **copublications scientifiques** entre **Inria Sophia Antipolis** et des organismes/équipes italiennes.  

L’interface propose des filtres, des indicateurs clés (KPI), des graphiques, un réseau de copublications et une carte interactive des collaborations.

---

## 🚀 Fonctionnalités

- **Tableau de bord interactif**
  - Nombre total de publications, villes, auteurs Inria, auteurs copubliants.
  - Publications par année (bar chart).
  - Répartition par villes et organismes (camemberts).
  - Génération d’un nuage de mots (WordCloud) à partir des mots-clés.

- **Réseau de copublications**
  - Graphe interactif représentant les liens entre auteurs Inria, copubliants italiens et villes.

- **Carte interactive**
  - Localisation des villes italiennes impliquées dans des copublications.
  - Arcs reliant Inria Sophia aux villes partenaires (épaisseur proportionnelle au nombre de publications).
  - Zoom et navigation sur la carte.

---

## 📂 Données attendues

Le script charge un fichier **Excel** (par défaut : `italy_full_completed_cities_translated_with_coords.xlsx`) contenant les colonnes suivantes :  

- `HalID` : identifiant de la publication  
- `Auteurs_FR` : auteur Inria  
- `Auteurs_copubliants` : auteur italien  
- `Ville_en_fr` : ville (en français)  
- `Organisme_copubliant` : organisme italien associé  
- `Année` : année de publication  
- `Equipe` : équipe de recherche Inria  
- `Latitude`, `Longitude` : coordonnées géographiques (pour la carte)  
- `Mots-cles` *(optionnel)* : mots-clés associés aux publications  

---

## 🛠️ Installation

1. **Cloner ce dépôt** (ou copier le script).  
2. Créer un environnement virtuel et installer les dépendances :  

```bash
pip install -r requirements.txt

