#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trace_map.py — Vectorisation automatique de la carte dessinée de Limii.

Segmente l'image par couleur (k-means/prototypes), extrait les contours
réels de chaque zone (marching squares + Douglas-Peucker) et régénère
map-data.js. Les formes produites respectent le dessin d'origine.

Usage :
    python tools/trace_map.py [Limii_map.jpg] [map-data.js]

Dépendances : numpy, scipy, scikit-image, Pillow.
"""

import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure, morphology

# ----------------------------------------------------------------------------
# Réglages
# ----------------------------------------------------------------------------
IMG_PATH = sys.argv[1] if len(sys.argv) > 1 else "Limii_map.jpg"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "map-data.js"
MEDIAN = 7          # lissage médian (détruit la texture/anticrénelage)
TOL = 1.8           # tolérance Douglas-Peucker (px) — fidélité des formes
MIN_AREA = 40       # surface minimale d'une zone conservée (px)
MIN_ARTERE = 150    # surface minimale d'un bras bleu conservé (px)

# ----------------------------------------------------------------------------
# Classes : nom_interne -> (couleur affichée, prototype RGB, libellé, type)
#   - "eau" est ensuite scindée en océan (composante bordure) / artères.
#   - lagune_c est rendue avec la couleur de lagune (variante de texture).
# ----------------------------------------------------------------------------
CLASSES = [
    # nom          couleur      prototype        libellé wiki                         type
    ("eau",        "#363afe",  (54, 58, 254),   "Océan & estuaire",                  "eau"),
    ("lagune",     "#06f7ba",  (6, 247, 186),   "Lagune turquoise",                  "lagune"),
    ("lagune_c",   "#06f7ba",  (33, 255, 198),  "Lagune (eaux claires)",             "lagune"),
    ("herbiers",   "#29ba9b",  (41, 186, 155),  "Herbiers / bas-fonds",              "basfonds"),
    ("foret",      "#369448",  (54, 148, 72),   "Forêt du nord-est",                 "foret"),
    ("olive",      "#a1a547",  (161, 162, 76),  "Presqu'île d'olive (terres sèches)","desert"),
    ("beige",      "#b49692",  (180, 150, 146), "Quartiers ouest",                   "habitation"),
    ("brun",       "#a27651",  (162, 118, 81),  "Plateau brun",                      "habitation"),
    ("jaune",      "#e9fe5d",  (233, 254, 93),  "Croissant jaune (terres claires)",  "desert"),
    ("centre",     "#3b3e33",  (59, 62, 51),    "Centre sombre",                     "indefini"),
    ("quartier",   "#757a65",  (117, 122, 101), "Quartier gris du sud-ouest",        "indefini"),
    ("massif",     "#434254",  (67, 66, 82),    "Massif du sud",                     "indefini"),
    ("axe",        "#166753",  (22, 103, 83),   "Axe sombre de l'ouest",             "route"),
    ("autoroute",  "#ee28b1",  (238, 40, 177),  "Autoroute de ceinture (6x6 voies)", "route"),
]
NAMES = [c[0] for c in CLASSES]
COLORS = {c[0]: c[1] for c in CLASSES}
COLORS["arteres"] = "#363afe"
LABELS = {c[0]: c[3] for c in CLASSES}
LABELS["arteres"] = "Artères urbaines (bras bleus)"
TYPES = {c[0]: c[4] for c in CLASSES}
TYPES["arteres"] = "route"
PROTOS = np.array([c[2] for c in CLASSES], float)

# Ordre de dessin (le 1er est le plus bas)
DRAW_ORDER = [
    "eau", "lagune", "lagune_c", "herbiers", "foret", "olive",
    "beige", "brun", "jaune", "centre", "quartier", "massif",
    "autoroute", "arteres", "axe",
]

POPUPS = {
    "eau":       "Eaux profondes (océan et estuaire du bras de mer).",
    "lagune":    "Eaux peu profondes ceignant la ville au nord et à l'ouest.",
    "lagune_c":  "Variante claire de la lagune (bancs de sable ?).",
    "herbiers":  "Taches sombres dans la lagune : herbiers, bas-fonds ou îlots (à identifier).",
    "foret":     "Grande masse forestière côtière (à nommer).",
    "olive":     "Terres sèches prolongeant la ville vers l'est (à nommer).",
    "beige":     "Vaste zone d'habitations à l'intérieur de la ceinture autoroutière.",
    "brun":      "Zone construite du nord (à identifier / nommer).",
    "jaune":     "Bande de terres claires entre le centre et la presqu'île (à identifier).",
    "centre":    "Zone centrale dense — centre-ville ? parc ? (à identifier).",
    "quartier":  "Zone du sud-ouest intérieur, traversée par les artères (à identifier).",
    "massif":    "Grand massif sombre au sud de la ville — montagne ? zone industrielle ? (à identifier).",
    "autoroute": "Autoroute périurbaine rose, environ 6x6 voies, en boucle fermée.",
    "arteres":   "Réseau de bras bleus (artères ou cours d'eau) arrivant dans la ville.",
    "axe":       "Ligne sombre courbe avec bornes, le long de la côte ouest. Métro ? Voie ferrée ? Conduite ? (à déterminer).",
}

# Points d'intérêt ajoutés en plus des zones (coordonnées calculées
# automatiquement où c'est possible, sinon pixels de l'image d'origine).
POI_FIXES = [
    {"name": "Embarcadère (à identifier)", "xy": [708, 692],
     "popup": "Petit appontement sombre à la pointe sud de la presqu'île."},
]

LEGEND = [
    {"label": "Océan & estuaire", "color": "#363afe"},
    {"label": "Lagune / eaux turquoises", "color": "#06f7ba"},
    {"label": "Herbiers / bas-fonds", "color": "#29ba9b"},
    {"label": "Forêts", "color": "#369448"},
    {"label": "Terres sèches / désert", "color": "#e9fe5d"},
    {"label": "Habitations", "color": "#b49692"},
    {"label": "Zones à identifier", "color": "#434254"},
    {"label": "Autoroute (6x6 voies)", "color": "#ee28b1"},
    {"label": "Artères urbaines (bras bleus)", "color": "#363afe"},
    {"label": "Axe sombre de l'ouest", "color": "#166753"},
]

STRUCT8 = np.ones((3, 3), int)


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------
def classify(smooth):
    """Chaque pixel -> indice de classe (prototype RVB le plus proche)."""
    pix = smooth.reshape(-1, 3).astype(float)
    d = ((pix[:, None, :] - PROTOS[None, :, :]) ** 2).sum(axis=2)
    return d.argmin(axis=1).reshape(smooth.shape[:2])


def split_water(blue):
    """Scinde le masque bleu : océan (composante touchant le bord) / artères."""
    lab, _ = ndi.label(blue, structure=STRUCT8)
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    border.discard(0)
    ocean_ids = {i for i in border if (lab == i).sum() >= MIN_AREA}
    ocean = np.isin(lab, list(ocean_ids))
    arteres = blue & ~ocean
    arteres = morphology.remove_small_objects(arteres, min_size=MIN_ARTERE)
    return ocean, arteres


def clean(mask):
    return morphology.remove_small_objects(mask, min_size=MIN_AREA)


def contour_of(mask, tol):
    """Contour principal (marching squares) simplifié, en coordonnées [x, y]."""
    padded = np.pad(mask, 1).astype(float)
    cs = measure.find_contours(padded, 0.5)
    if not cs:
        return None
    c = max(cs, key=len)
    c = measure.approximate_polygon(c, tolerance=tol)
    pts = [[int(round(x - 1)), int(round(y - 1))] for y, x in c]  # (row,col)->(x,y)
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    return pts if len(pts) >= 3 else None


def polygonize(mask, tol=TOL):
    """Tous les polygones (extérieur + trous) d'un masque de classe."""
    lab, n = ndi.label(mask, structure=STRUCT8)
    out = []
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() < MIN_AREA:
            continue
        filled = ndi.binary_fill_holes(comp)
        outer = contour_of(filled, tol)
        if not outer:
            continue
        holes = []
        hole_mask = filled & ~comp
        if hole_mask.any():
            hlab, hn = ndi.label(hole_mask, structure=STRUCT8)
            for j in range(1, hn + 1):
                h = hlab == j
                if h.sum() < MIN_AREA:
                    continue
                hc = contour_of(h, tol)
                if hc:
                    holes.append(hc)
        out.append({"coords": outer, "holes": holes})
    return out


def main():
    img = np.asarray(Image.open(IMG_PATH).convert("RGB")).astype(np.uint8)
    H, W = img.shape[:2]
    smooth = ndi.median_filter(img, size=(MEDIAN, MEDIAN, 1))
    cls = classify(smooth)

    masks = {name: clean(cls == i) for i, name in enumerate(NAMES)}
    ocean, arteres = split_water(masks["eau"])
    masks["eau"] = ocean

    # débogage : carte classifiée
    debug = np.zeros((H, W, 3), np.uint8)
    order_debug = ["eau", "lagune", "lagune_c", "herbiers", "foret", "olive",
                   "beige", "brun", "jaune", "centre", "quartier", "massif",
                   "autoroute", "axe"]
    rgb = {n: np.array(CLASSES[i][2], np.uint8) for i, n in enumerate(NAMES)}
    for name in order_debug:
        debug[masks[name]] = rgb[name]
    debug[arteres] = rgb["eau"]
    Image.fromarray(debug).save(OUT_PATH + ".classif.png")

    # zones -> polygones
    zones = []
    for name in DRAW_ORDER:
        mask = arteres if name == "arteres" else masks.get(name)
        if mask is None or not mask.any():
            continue
        for k, poly in enumerate(polygonize(mask)):
            zid = name if k == 0 else f"{name}-{k+1}"
            zones.append({
                "id": zid,
                "name": LABELS[name],
                "type": TYPES[name],
                "color": COLORS[name],
                "stroke": COLORS[name],
                "strokeWidth": 0 if TYPES[name] == "route" else 1,
                "popup": POPUPS[name] + (f" (fragment n° {k+1})" if k else ""),
                "coords": poly["coords"],
                "holes": poly["holes"],
            })

    # points d'intérêt calculés
    points = list(POI_FIXES)
    if masks["centre"].any():
        cy, cx = ndi.center_of_mass(masks["centre"])
        points.append({"name": "Centre-ville (à identifier)",
                       "xy": [int(round(cx)), int(round(cy))],
                       "popup": "Cœur de la zone sombre centrale."})
    # embouchure : point le plus au nord de l'océan dans le chenal sud
    zone = np.zeros_like(ocean)
    zone[680:900, 500:720] = ocean[680:900, 500:720]
    if zone.any():
        ys, xs = np.where(zone)
        top = ys.argmin()
        points.append({"name": "Embouchure du bras de mer",
                       "xy": [int(xs[top]), int(ys[top])],
                       "popup": "Là où le bras bleu rejoint l'océan."})

    data = {
        "meta": {"name": "Limii des Sables", "width": W, "height": H,
                 "pixelsPerKm": round(H / 50, 4), "trace": {"median": MEDIAN,
                 "tolerance": TOL, "minArea": MIN_AREA, "source": IMG_PATH}},
        "zones": zones,
        "points": points,
        "legend": LEGEND,
    }

    header = """/* ============================================================
   LIMII DES SABLES — Données de la carte interactive
   ------------------------------------------------------------
   FICHIER GÉNÉRÉ AUTOMATIQUEMENT — ne pas éditer à la main.
   Regénération après modification de Limii_map.jpg :
       python tools/trace_map.py Limii_map.jpg map-data.js
   ------------------------------------------------------------
   COORDONNÉES : pixels de l'image d'origine (origine en haut à
   gauche, x → droite, y → bas). Échelle : {hauteur} px ≈ 50 km
   de hauteur ⇒ {ppk} px = 1 km.
   Chaque zone : "coords" = contour extérieur, "holes" = trous
   éventuels (anneaux). Les fragments (zones déconnectées du même
   type) portent un suffixe -2, -3…
   ============================================================ */

const LIMII_DATA =
""".format(hauteur=H, ppk=round(H / 50, 4))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        f.write(";\n")

    n_pts = sum(len(z["coords"]) + sum(len(h) for h in z["holes"]) for z in zones)
    print(f"OK — {len(zones)} polygones, {n_pts} points, "
          f"{len(points)} POI -> {OUT_PATH}")
    print(f"     (carte classifiée de contrôle : {OUT_PATH}.classif.png)")


if __name__ == "__main__":
    main()
