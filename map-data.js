/* ============================================================
   LIMII DES SABLES — Données de la carte interactive (1er jet)
   ------------------------------------------------------------
   COORDONNÉES : pixels de l'image d'origine « Limii_map.jpg »
   (1200 × 900, origine en HAUT À GAUCHE, x → droite, y → bas).

   ÉCHELLE : 900 px ≈ 50 km de hauteur  ⇒  18 px = 1 km
             (1 px ≈ 55,6 m)

   ORDRE D'AFFICHAGE : les zones sont dessinées dans l'ordre du
   tableau (le 1er bloc est le calque le plus BAS). Les
   recouvrements sont résolus par cet ordre, comme dans un
   logiciel de dessin.

   POUR RAJOUTER UN ÉLÉMENT :
     • zone  : copiez/collez un bloc « { id, name, ... } » du
               tableau `zones` avec vos coordonnées.
     • route : copiez un bloc du tableau `roads`.
     • point : copiez un bloc du tableau `points`.
   Rechargez ensuite map.html. Les coordonnées se lisent
   directement sur l'image d'origine.
   ============================================================ */

const LIMII_DATA = {
  meta: {
    name: "Limii des Sables",
    width: 1200,        // largeur de la carte d'origine (px)
    height: 900,        // hauteur de la carte d'origine (px)
    pixelsPerKm: 18     // 900 px ≈ 50 km
  },

  /* ----------------------------------------------------------
     ZONES (aplats de couleur)
     types : eau | lagune | foret | desert | habitation | indefini
     ---------------------------------------------------------- */
  zones: [
    {
      id: "ocean",
      name: "Océan",
      type: "eau",
      color: "#363afe", stroke: "#2a2ecc",
      popup: "Eaux profondes à l'est et au sud de la presqu'île.",
      coords: [
        [975, 0], [1200, 0], [1200, 900], [618, 900], [613, 856],
        [634, 802], [666, 780], [692, 770], [716, 748], [744, 744],
        [784, 730], [827, 703], [877, 643], [907, 563], [917, 483],
        [907, 403], [908, 344], [922, 321], [958, 262], [988, 208],
        [1022, 148], [1058, 88], [1012, 42]
      ]
    },
    {
      id: "lagune",
      name: "Lagune turquoise",
      type: "lagune",
      color: "#05f7ba", stroke: "#0bbf96",
      popup: "Eaux peu profondes ceignant la ville au nord et à l'ouest.",
      coords: [
        [0, 0], [672, 0], [706, 14], [762, 42], [818, 92], [852, 150],
        [880, 220], [898, 295], [894, 352], [862, 425], [850, 498],
        [858, 570], [838, 640], [797, 700], [748, 736], [708, 756],
        [676, 771], [648, 796], [623, 838], [618, 900], [0, 900]
      ]
    },
    {
      id: "terres",
      name: "Terres (sous-couche)",
      type: "terre",
      color: "#b5a48e", stroke: "#b5a48e", strokeWidth: 0,
      fillOpacity: 1,
      popup: "Sous-couche technique absorbant les interstices entre zones terrestres.",
      coords: [
        [672, 2], [742, 36], [802, 78], [846, 134], [873, 200], [888, 268],
        [886, 336], [892, 318], [900, 326], [906, 340], [914, 430], [914, 500],
        [894, 580], [864, 650], [820, 700], [760, 735], [708, 744], [676, 772],
        [666, 782], [634, 804], [614, 858], [618, 900], [245, 900], [238, 840],
        [252, 792], [292, 762], [352, 748], [318, 738], [252, 706], [198, 652],
        [162, 582], [142, 504], [138, 424], [154, 348], [190, 282], [242, 226],
        [304, 182], [366, 148], [420, 136], [480, 130], [556, 148], [612, 150],
        [668, 168], [716, 196], [742, 212], [800, 220], [848, 258], [878, 290],
        [892, 300], [868, 196], [836, 128], [796, 72], [738, 32], [697, 14]
      ]
    },
    {
      id: "foret-nord-est",
      name: "Forêt du nord-est",
      type: "foret",
      color: "#379547", stroke: "#2a7a38",
      popup: "Grande masse forestière côtière (à nommer).",
      coords: [
        [672, 0], [975, 0], [1012, 42], [1058, 88], [1022, 148],
        [988, 208], [958, 262], [930, 318], [908, 342], [886, 336],
        [888, 268], [873, 200], [846, 134], [802, 78], [742, 36]
      ]
    },
    {
      id: "presquile-olive",
      name: "Presqu'île d'olive",
      type: "desert",
      color: "#a1a547", stroke: "#8a8e3c",
      popup: "Terres sèches / badlands prolongeant la ville vers l'est (à nommer).",
      coords: [
        [742, 212], [790, 220], [848, 258], [878, 318], [898, 398],
        [908, 478], [898, 558], [868, 638], [818, 698], [758, 732],
        [706, 742], [686, 712], [706, 652], [736, 582], [756, 512],
        [758, 442], [750, 345], [748, 320], [740, 286], [734, 246]
      ]
    },
    {
      id: "quartiers-ouest",
      name: "Quartiers ouest",
      type: "habitation",
      color: "#b49791", stroke: "#a0807a",
      popup: "Vaste zone d'habitations à l'intérieur de la ceinture autoroutière.",
      coords: [
        [420, 136], [480, 130], [545, 140], [600, 162], [615, 200],
        [608, 246], [596, 294], [580, 342], [560, 388], [536, 430],
        [506, 464], [468, 486], [426, 496], [384, 488], [346, 468],
        [316, 438], [298, 400], [290, 362], [270, 336], [240, 316],
        [210, 298], [184, 272], [168, 242], [150, 240], [140, 234],
        [112, 256], [98, 336], [80, 352], [68, 340], [64, 314],
        [82, 284], [100, 328], [92, 378], [90, 420], [100, 462],
        [118, 502], [144, 540], [176, 574], [214, 604], [258, 630],
        [306, 650], [356, 664], [408, 672], [460, 672], [510, 662],
        [550, 640], [574, 606], [586, 566], [592, 616], [584, 662],
        [558, 700], [516, 722], [462, 734], [404, 740], [346, 736],
        [292, 722], [242, 696], [200, 658], [170, 612], [150, 562],
        [138, 510], [132, 458], [136, 406], [150, 356], [174, 308],
        [208, 266], [250, 230], [298, 200], [350, 174], [392, 152]
      ]
    },
    {
      id: "plateau-brun",
      name: "Plateau brun",
      type: "habitation",
      color: "#a27651", stroke: "#8a6444",
      popup: "Zone construite du nord (à identifier / nommer).",
      coords: [
        [556, 148], [612, 150], [668, 168], [720, 200], [748, 246],
        [744, 300], [716, 338], [672, 362], [624, 358], [588, 330],
        [564, 286], [552, 232], [548, 186]
      ]
    },
    {
      id: "croissant-jaune",
      name: "Croissant jaune",
      type: "desert",
      color: "#e9ff5c", stroke: "#d3e63f",
      popup: "Bande de terres claires entre le centre et la presqu'île (à identifier).",
      coords: [
        [626, 356], [668, 330], [712, 318], [736, 344], [720, 404],
        [688, 462], [640, 516], [584, 562], [522, 594], [458, 606],
        [432, 584], [456, 528], [500, 470], [552, 412]
      ]
    },
    {
      id: "centre-sombre",
      name: "Centre sombre",
      type: "indefini",
      color: "#393f33", stroke: "#2c3126",
      popup: "Zone centrale dense — centre-ville ? parc ? (à identifier).",
      coords: [
        [430, 292], [492, 272], [542, 296], [560, 344], [552, 396],
        [514, 436], [458, 450], [408, 428], [384, 380], [392, 328]
      ]
    },
    {
      id: "quartier-gris",
      name: "Quartier gris du sud-ouest",
      type: "indefini",
      color: "#757a64", stroke: "#62664f",
      popup: "Zone du sud-ouest intérieur, traversée par les artères (à identifier).",
      coords: [
        [315, 495], [375, 482], [425, 495], [450, 532], [438, 575],
        [470, 560], [500, 600], [520, 650], [500, 690], [440, 706],
        [370, 706], [310, 685], [262, 648], [238, 600], [246, 548],
        [272, 512]
      ]
    },
    {
      id: "massif-sud",
      name: "Massif du sud",
      type: "indefini",
      color: "#434254", stroke: "#373643",
      popup: "Grand massif sombre au sud de la ville — montagne ? zone industrielle ? (à identifier).",
      coords: [
        [430, 742], [520, 750], [585, 764], [612, 798], [622, 852],
        [618, 900], [245, 900], [238, 840], [252, 792], [292, 762],
        [352, 748]
      ]
    }
  ],

  /* ----------------------------------------------------------
     ROUTES
     kinds : autoroute | artere | axe
     ---------------------------------------------------------- */
  roads: [
    {
      id: "autoroute-ceinture",
      name: "Autoroute de ceinture",
      kind: "autoroute",
      color: "#f324b2", weight: 8, opacity: 0.95,
      popup: "Autoroute périurbaine rose, environ 6×6 voies. Tracé approximatif (le trait d'origine n'est pas net).",
      coords: [
        [432, 124], [520, 126], [596, 144], [656, 176], [706, 220],
        [742, 278], [764, 346], [770, 420], [760, 494], [732, 564],
        [688, 626], [628, 676], [556, 712], [476, 734], [394, 744],
        [318, 738], [252, 706], [198, 652], [162, 582], [142, 504],
        [138, 424], [154, 348], [190, 282], [242, 226], [304, 182],
        [366, 148]
      ],
      stations: []
    },
    {
      id: "artere-principale",
      name: "Artère principale (embouchure → centre)",
      kind: "artere",
      color: "#363afe", casing: "#22278f", weight: 8,
      popup: "Gros bras bleu remontant du bras de mer vers le centre-ville. Fleuve / estuaire ou grande artère — à trancher.",
      coords: [
        [700, 790], [668, 768], [638, 752], [608, 732], [582, 706],
        [560, 676], [546, 646], [538, 638]
      ],
      stations: []
    },
    {
      id: "artere-ouest",
      name: "Artère ouest",
      kind: "artere",
      color: "#363afe", casing: "#22278f", weight: 5,
      popup: "Ramification vers les quartiers ouest.",
      coords: [
        [538, 638], [498, 618], [454, 612], [408, 616], [362, 628],
        [318, 646], [282, 668], [260, 692], [252, 712]
      ],
      stations: []
    },
    {
      id: "artere-nord",
      name: "Artère nord",
      kind: "artere",
      color: "#363afe", casing: "#22278f", weight: 5,
      popup: "Ramification remontant vers le plateau brun.",
      coords: [
        [538, 638], [524, 600], [514, 558], [506, 514], [500, 470],
        [496, 428], [494, 388], [494, 348], [494, 310], [493, 272],
        [492, 234], [491, 196], [490, 164]
      ],
      stations: []
    },
    {
      id: "artere-est",
      name: "Artère est",
      kind: "artere",
      color: "#363afe", casing: "#22278f", weight: 5,
      popup: "Ramification vers le croissant jaune et la presqu'île.",
      coords: [
        [538, 638], [560, 600], [584, 560], [604, 516], [616, 474],
        [620, 436]
      ],
      stations: []
    },
    {
      id: "artere-nord-ouest",
      name: "Artère nord-ouest",
      kind: "artere",
      color: "#363afe", casing: "#22278f", weight: 4,
      popup: "Courte branche vers les quartiers ouest.",
      coords: [ [506, 514], [472, 506], [442, 490] ],
      stations: []
    },
    {
      id: "axe-sombre-ouest",
      name: "Axe sombre de l'ouest",
      kind: "axe",
      color: "#1c5a33", weight: 6,
      popup: "Ligne sombre courbe avec bornes, de l'axe nord à l'axe sud, le long de la côte ouest. Nature à déterminer (métro ? voie ferrée ? conduite ?).",
      coords: [
        [392, 0], [362, 28], [336, 58], [310, 90], [286, 124],
        [264, 158], [240, 194], [214, 232], [188, 272], [162, 314],
        [138, 360], [118, 408], [102, 458], [90, 510], [80, 564],
        [72, 620], [66, 678], [66, 738], [74, 796], [88, 846], [102, 890]
      ],
      stations: [
        [362, 28], [310, 90], [264, 158], [214, 232], [162, 314],
        [118, 408], [90, 510], [72, 620], [66, 738], [88, 846]
      ]
    }
  ],

  /* ----------------------------------------------------------
     POINTS D'INTÉRÊT
     ---------------------------------------------------------- */
  points: [
    { name: "Centre-ville (à identifier)", kind: "poi", xy: [480, 365],
      popup: "Cœur de la zone sombre centrale." },
    { name: "Embarcadère (à identifier)", kind: "poi", xy: [708, 692],
      popup: "Petit appontement sombre à la pointe sud de la presqu'île." },
    { name: "Embouchure du bras de mer", kind: "poi", xy: [668, 772],
      popup: "Là où l'artère principale bleue rejoint l'océan." }
  ],

  /* ----------------------------------------------------------
     LÉGENDE
     ---------------------------------------------------------- */
  legend: [
    { label: "Eaux profondes", color: "#363afe" },
    { label: "Lagune / eaux turquoises", color: "#05f7ba" },
    { label: "Forêts", color: "#379547" },
    { label: "Déserts / terres sèches", color: "#e9ff5c" },
    { label: "Habitations / quartiers", color: "#b49791" },
    { label: "Zones à identifier", color: "#434254" },
    { label: "Autoroute (6×6 voies)", color: "#f324b2" },
    { label: "Artères urbaines", color: "#363afe" },
    { label: "Axe sombre de l'ouest", color: "#1c5a33" }
  ]
};
