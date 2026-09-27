#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trace_map.py — Vectorisation automatique de la carte dessinée de Limii.

Segmente l'image par couleur (prototypes RVB), extrait les contours réels
de chaque zone (marching squares + Douglas-Peucker) et régénère map-data.js.

Pour MODIFIER les noms, la légende ou le découpage des zones : éditez la
configuration GROUPS / SPLIT_* ci-dessous, puis relancez :
    python tools/trace_map.py Limii_map.jpg map-data.js

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
MIN_CANAL = 150     # surface minimale d'un canal conservé (px)

# ----------------------------------------------------------------------------
# Prototypes de classification (couleurs réelles du dessin).
# Ce sont des noms INTERNES ; les noms wiki sont dans GROUPS plus bas.
# ----------------------------------------------------------------------------
CLASSES = [
    ("eau",        (54, 58, 254)),   # océan + canaux (Sil-Eron)
    ("lagune",     (6, 247, 186)),   # reg (désert de pierre)
    ("lagune_c",   (33, 255, 198)),  # dunes (désert de sable)
    ("herbiers",   (41, 186, 155)),  # monticules (nord) / vestiges (sud)
    ("foret",      (54, 148, 72)),   # forêt équatoriale
    ("olive",      (161, 162, 76)),  # zones résidentielles & commerçantes
    ("beige",      (180, 150, 146)),  # habitations & commerces
    ("brun",       (162, 118, 81)),   # espaces verts & campus
    ("jaune",      (233, 254, 93)),   # quartier bourgeois
    ("centre",     (59, 62, 51)),     # La Galerie
    ("quartier",   (117, 122, 101)),  # la muraille (remparts)
    ("massif",     (67, 66, 82)),     # zone militaire & docks
    ("axe",        (22, 103, 83)),    # muraille ouest (ligne & bastions)
    ("autoroute",  (238, 40, 177)),   # autoroute de ceinture
]
NAMES = [c[0] for c in CLASSES]
PROTOS = np.array([c[1] for c in CLASSES], float)

# ----------------------------------------------------------------------------
# Groupes de sortie : id -> affichage (couleur, nom wiki, type, popup).
# types : eau | desert | foret | habitation | parc | monument |
#         fortification | vestige | relief | militaire | route
# ----------------------------------------------------------------------------
GROUPS = {
    "oceane":          ("#363afe", "Océan Silvaïc", "eau",
                        "L'Océan Silvaïc borde Limii à l'est et au sud."),
    "fleuve":          ("#363afe", "Le Sil-Eron (fleuve & estuaire)", "eau",
                        "Le fleuve Sil-Eron rejoint la mer après avoir traversé la ville en canaux."),
    "canaux":          ("#363afe", "Canaux du Sil-Eron", "eau",
                        "Canaux creusés dans la ville — leur tracé dessine un presque parfait carré."),
    "reg":             ("#06f7ba", "Désert de pierre (reg)", "desert",
                        "Reg : désert de pierre à l'ouest et au nord de la ville-forteresse."),
    "dunes":           ("#21ffc6", "Désert de sable & dunes", "desert",
                        "Dunes de sable ondulant autour de la ville."),
    "monticules":      ("#29ba9b", "Monticules rocheux", "relief",
                        "Buttes rocheuses isolées, comme dans le Nevada."),
    "vestiges":        ("#29ba9b", "Vestiges de l'ancienne muraille", "vestige",
                        "Ruines des anciens remparts, rongées par le désert."),
    "foret":           ("#369448", "Forêt équatoriale", "foret",
                        "La seule forêt équatoriale de la région (à nommer précisément)."),
    "olive":           ("#a1a547", "Zones résidentielles & commerçantes", "habitation",
                        "Quartiers résidentiels et quartiers des commerçans, proches du port de pêche manghan."),
    "beige":           ("#b49692", "Habitations & Commerces", "habitation",
                        "Le quartier ouest, simple mais vivant (nom provisoire)."),
    "brun":            ("#a27651", "Espaces verts & campus universitaire", "parc",
                        "Parcs, jardins et campus de l'université de Limii."),
    "jaune":           ("#e9fe5d", "Quartier Bourgeois", "habitation",
                        "Le quartier chic de Limii."),
    "galerie":         ("#3b3e33", "La Galerie", "monument",
                        "Le cœur culturel de Limii (à développer)."),
    "ancienne_muraille": ("#757a65", "Ancienne muraille", "fortification",
                        "Les restes du premier rempart, le long de l'autoroute de ceinture."),
    "muraille":        ("#757a65", "La Muraille", "fortification",
                        "Le quartier des remparts. Limii est une énorme forteresse qui combat "
                        "les forces du désert et les brigands. Au nord se trouve la Cité des "
                        "Songes (CBD), au sud le centre techno-industriel."),
    "militaire":       ("#434254", "Zone militaire & docks", "militaire",
                        "Zone militaire fortifiée ; les docks servent la marine près de la mer."),
    "autoroute":       ("#ee28b1", "Autoroute de ceinture (6×6 voies)", "route",
                        "Autoroute périurbaine en boucle fermée, environ 6×6 voies."),
    "muraille_ouest":  ("#166753", "La Muraille — remparts ouest", "fortification",
                        "Ligne de remparts avec bastions, à l'ouest de la ville (l'« axe sombre » du dessin)."),
}

# Ordre de dessin (le 1er est le plus bas)
DRAW_ORDER = [
    "oceane", "fleuve", "reg", "dunes", "monticules", "vestiges", "foret",
    "olive", "beige", "brun", "jaune", "galerie",
    "ancienne_muraille", "muraille", "militaire",
    "autoroute", "canaux", "muraille_ouest",
]

LEGEND = [
    {"label": "Océan Silvaïc", "color": "#363afe"},
    {"label": "Sil-Eron : fleuve, estuaire & canaux", "color": "#363afe"},
    {"label": "Désert de sable & dunes", "color": "#21ffc6"},
    {"label": "Désert de pierre (reg)", "color": "#06f7ba"},
    {"label": "Monticules rocheux", "color": "#29ba9b"},
    {"label": "Vestiges de l'ancienne muraille", "color": "#29ba9b"},
    {"label": "Forêt équatoriale", "color": "#369448"},
    {"label": "Zones résidentielles & commerçantes", "color": "#a1a547"},
    {"label": "Habitations & Commerces", "color": "#b49692"},
    {"label": "Espaces verts & campus universitaire", "color": "#a27651"},
    {"label": "Quartier Bourgeois", "color": "#e9fe5d"},
    {"label": "La Galerie", "color": "#3b3e33"},
    {"label": "La Muraille & l'ancienne muraille", "color": "#757a65"},
    {"label": "Zone militaire & docks", "color": "#434254"},
    {"label": "Autoroute de ceinture", "color": "#ee28b1"},
    {"label": "Remparts ouest (ligne & bastions)", "color": "#166753"},
]

STRUCT8 = np.ones((3, 3), int)


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------
def classify(smooth):
    pix = smooth.reshape(-1, 3).astype(float)
    d = ((pix[:, None, :] - PROTOS[None, :, :]) ** 2).sum(axis=2)
    return d.argmin(axis=1).reshape(smooth.shape[:2])


def clean(mask):
    return morphology.remove_small_objects(mask, min_size=MIN_AREA)


def split_water(blue):
    """Scinde le bleu : océan (composante touchant le bord) / canaux intérieurs."""
    lab, _ = ndi.label(blue, structure=STRUCT8)
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    border.discard(0)
    ocean_ids = {i for i in border if (lab == i).sum() >= MIN_AREA}
    ocean = np.isin(lab, list(ocean_ids))
    canaux = blue & ~ocean
    canaux = morphology.remove_small_objects(canaux, min_size=MIN_CANAL)
    return ocean, canaux


def split_river(ocean, H, W):
    """Isole le Sil-Eron : partie du bleu océanique dans le couloir sud."""
    Y, X = np.mgrid[0:H, 0:W]
    region = (X >= 430) & (X <= 745) & (Y >= 620)
    cand = ocean & region
    lab, n = ndi.label(cand, structure=STRUCT8)
    fleuve = np.zeros_like(ocean)
    for i in range(1, n + 1):
        if (lab == i).sum() >= 800:
            fleuve |= lab == i
    return fleuve, ocean & ~fleuve


def split_herbiers(herbiers, y_cut=450):
    """Nord = monticules rocheux ; sud = vestiges de l'ancienne muraille."""
    north = herbiers.copy()
    north[y_cut:, :] = False
    south = herbiers & ~north
    return north, south


def split_quartier(quartier, autoroute):
    """Fragment collé à l'autoroute = ancienne muraille ; le reste = la muraille."""
    dist = ndi.distance_transform_edt(~autoroute)
    lab, n = ndi.label(quartier, structure=STRUCT8)
    ancienne, muraille = np.zeros_like(quartier), np.zeros_like(quartier)
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() < MIN_AREA:
            continue
        if dist[comp].min() < 15:
            ancienne |= comp
        else:
            muraille |= comp
    return ancienne, muraille


def contour_of(mask, tol):
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

    ocean, canaux = split_water(masks["eau"])
    fleuve, oceane = split_river(ocean, H, W)
    monticules, vestiges = split_herbiers(masks["herbiers"])
    ancienne, muraille = split_quartier(masks["quartier"], masks["autoroute"])

    groups = {
        "oceane": oceane, "fleuve": fleuve, "canaux": canaux,
        "reg": masks["lagune"], "dunes": masks["lagune_c"],
        "monticules": monticules, "vestiges": vestiges,
        "foret": masks["foret"], "olive": masks["olive"],
        "beige": masks["beige"], "brun": masks["brun"], "jaune": masks["jaune"],
        "galerie": masks["centre"],
        "ancienne_muraille": ancienne, "muraille": muraille,
        "militaire": masks["massif"],
        "autoroute": masks["autoroute"], "muraille_ouest": masks["axe"],
    }

    # débogage : carte classifiée avec les couleurs finales
    debug = np.full((H, W, 3), 255, np.uint8)
    for gid in DRAW_ORDER:
        color = np.array([int(GROUPS[gid][0][i:i+2], 16) for i in (1, 3, 5)], np.uint8)
        debug[groups[gid]] = color
    Image.fromarray(debug).save(OUT_PATH + ".classif.png")

    # zones -> polygones
    zones = []
    for gid in DRAW_ORDER:
        color, label, ztype, popup = GROUPS[gid]
        for k, poly in enumerate(polygonize(groups[gid])):
            zid = gid if k == 0 else f"{gid}-{k+1}"
            zones.append({
                "id": zid,
                "name": label,
                "type": ztype,
                "color": color,
                "stroke": color,
                "strokeWidth": 0 if ztype in ("route", "eau") else 1,
                "popup": popup + (f" (fragment n° {k+1})" if k else ""),
                "coords": poly["coords"],
                "holes": poly["holes"],
            })

    # ----- points d'intérêt -----
    points = [{
        "name": "Port de pêche (peuple Manghans)", "xy": [708, 692],
        "popup": "Port de pêche tenu par le peuple Manghans, à proximité "
                 "des quartiers des commerçans (presqu'île).",
    }]
    # CBD & centre techno-industriel : centroids des deux grands fragments de la muraille
    qlab, qn = ndi.label(muraille, structure=STRUCT8)
    big = []
    for i in range(1, qn + 1):
        comp = qlab == i
        if comp.sum() >= 2000:
            cy, cx = ndi.center_of_mass(comp)
            big.append((cy, cx))
    big.sort()
    if big:
        cy, cx = big[0]
        points.append({"name": "La Cité des Songes (CBD)",
                       "xy": [int(round(cx)), int(round(cy))],
                       "popup": "Centre-ville de Limii, au cœur de la Muraille, "
                                "juste au sud de La Galerie."})
    if len(big) > 1:
        cy, cx = big[-1]
        points.append({"name": "Centre techno-industriel",
                       "xy": [int(round(cx)), int(round(cy))],
                       "popup": "Pôle technique et industriel de Limii, au sud "
                                "de la Cité des Songes."})
    # embouchure du Sil-Eron
    zone = np.zeros_like(fleuve)
    zone[640:900, 480:720] = fleuve[640:900, 480:720]
    if zone.any():
        ys, xs = np.where(zone)
        top = ys.argmin()
        points.append({"name": "Embouchure du Sil-Eron",
                       "xy": [int(xs[top]), int(ys[top])],
                       "popup": "Là où le fleuve Sil-Eron rejoint l'Océan Silvaïc."})

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
   Les noms et le découpage des zones se modifient dans
   tools/trace_map.py (config GROUPS), puis :
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
    print(f"OK — {len(zones)} polygones, {n_pts} points, {len(points)} POI -> {OUT_PATH}")
    print(f"     (carte classifiée de contrôle : {OUT_PATH}.classif.png)")


if __name__ == "__main__":
    main()
