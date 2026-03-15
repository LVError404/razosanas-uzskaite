"""
Razosanas uzskaites un prognozes sistema
Autors: Ivo Ģipters
Apraksts: Flask tīmekļa serveris ar SQLite datubāzi.
        
Versija: 1.2
"""

import sqlite3
import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

# ─────────────────────────────────────────────
# LIETOJUMPROGRAMMAS UN DATUBĀZES IESTATĪJUMI
# ─────────────────────────────────────────────

# Mapes ceļš kur atrodas šis fails — darbojas neatkarīgi no tā,
# no kuras mapes serveris tiek palaists
MAPE = os.path.dirname(os.path.abspath(__file__))

# Izveido Flask lietojumprogrammu ar absolūtu ceļu uz statiskajiem failiem
lietotne = Flask(__name__, static_folder=MAPE)

# Datubāzes faila absolūtais ceļš (tajā pašā mapē kā serveris)
DB_FAILS = os.path.join(MAPE, "razosana.db")


# ─────────────────────────────────────────────
# DATUBĀZES INICIALIZĀCIJA
# ─────────────────────────────────────────────

def inicializet_db():
    """
    Izveido datubāzes tabulas, ja tās vēl neeksistē.
    Tabula 'darbi' glabā darbu veidus.
    Tabula 'ieraksti' glabā ražošanas sesiju datus,
    saistīta ar 'darbi' caur ārējo atslēgu darbs_id.
    """
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()

    # Tabula darbu veidu glabāšanai
    kursors.execute("""
        CREATE TABLE IF NOT EXISTS darbi (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nosaukums TEXT NOT NULL UNIQUE,
            apraksts  TEXT
        )
    """)

    # Tabula ražošanas sesiju ierakstiem
    # darbs_id ir ārējā atslēga uz tabulu 'darbi'
    kursors.execute("""
        CREATE TABLE IF NOT EXISTS ieraksti (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            darbs_id           INTEGER NOT NULL,
            nepieciesams_skaits INTEGER NOT NULL,
            gatavs_skaits      INTEGER NOT NULL,
            laiks_stundas      REAL    NOT NULL,
            datums             TEXT    NOT NULL,
            FOREIGN KEY (darbs_id) REFERENCES darbi(id)
        )
    """)

    savienojums.commit()
    savienojums.close()


def savienot_db():
    """Atver un atgriež savienojumu ar datubāzi."""
    savienojums = sqlite3.connect(DB_FAILS)
    # Atgriež rindas kā vārdnīcas, lai JSON serializācija būtu vieglāka
    savienojums.row_factory = sqlite3.Row
    return savienojums


# ─────────────────────────────────────────────
# MARŠRUTS: GALVENĀ LAPA
# ─────────────────────────────────────────────

@lietotne.route("/")
def galvena_lapa():
    """Atgriež galveno HTML failu."""
    return send_from_directory(MAPE, "v1.2_index.html")


# ─────────────────────────────────────────────
# MARŠRUTI: DARBI
# ─────────────────────────────────────────────

@lietotne.route("/api/darbi", methods=["GET"])
def api_darbi_saraksts():
    """
    GET /api/darbi
    Atgriež visus darbu veidus kā JSON masīvu.
    """
    savienojums = savienot_db()
    kursors = savienojums.cursor()
    kursors.execute("SELECT id, nosaukums, apraksts FROM darbi ORDER BY nosaukums")
    darbi = [dict(r) for r in kursors.fetchall()]
    savienojums.close()
    return jsonify(darbi)


@lietotne.route("/api/darbi", methods=["POST"])
def api_darbs_pievienot():
    """
    POST /api/darbi
    Pievieno jaunu darba veidu.
    Sagaida JSON: { nosaukums: "...", apraksts: "..." }
    """
    dati = request.get_json()

    # Pārbaudām, vai nosaukums ir norādīts
    nosaukums = (dati.get("nosaukums") or "").strip()
    if not nosaukums:
        return jsonify({"klauda": "Nosaukums ir obligāts."}), 400

    apraksts = (dati.get("apraksts") or "").strip()

    savienojums = savienot_db()
    kursors = savienojums.cursor()
    try:
        kursors.execute(
            "INSERT INTO darbi (nosaukums, apraksts) VALUES (?, ?)",
            (nosaukums, apraksts)
        )
        savienojums.commit()
        jaunais_id = kursors.lastrowid
        savienojums.close()
        return jsonify({"id": jaunais_id, "nosaukums": nosaukums, "apraksts": apraksts}), 201
    except sqlite3.IntegrityError:
        savienojums.close()
        return jsonify({"klauda": f"Darbs '{nosaukums}' jau eksistē."}), 409


# ─────────────────────────────────────────────
# MARŠRUTI: IERAKSTI
# ─────────────────────────────────────────────

@lietotne.route("/api/ieraksti", methods=["GET"])
def api_ieraksti_saraksts():
    """
    GET /api/ieraksti?darbs_id=N
    Atgriež ierakstus. Ja darbs_id norādīts – filtrē pēc tā.
    Katrai rindai pievieno aprēķināto ātrumu (produkti/stunda).
    """
    darbs_id = request.args.get("darbs_id", type=int)
    savienojums = savienot_db()
    kursors = savienojums.cursor()

    if darbs_id:
        kursors.execute("""
            SELECT i.id, d.nosaukums AS darbs, i.nepieciesams_skaits,
                   i.gatavs_skaits, i.laiks_stundas, i.datums
            FROM ieraksti i
            JOIN darbi d ON i.darbs_id = d.id
            WHERE i.darbs_id = ?
            ORDER BY i.datums DESC
        """, (darbs_id,))
    else:
        kursors.execute("""
            SELECT i.id, d.nosaukums AS darbs, i.nepieciesams_skaits,
                   i.gatavs_skaits, i.laiks_stundas, i.datums
            FROM ieraksti i
            JOIN darbi d ON i.darbs_id = d.id
            ORDER BY i.datums DESC
        """)

    # Pārvērš par vārdnīcu sarakstu un pievieno ātruma lauku
    ieraksti = []
    for rinda in kursors.fetchall():
        ieraksts = dict(rinda)
        # Aprēķina ātrumu tikai tad, ja laiks > 0
        if ieraksts["laiks_stundas"] > 0:
            ieraksts["atrums"] = round(
                ieraksts["gatavs_skaits"] / ieraksts["laiks_stundas"], 2
            )
        else:
            ieraksts["atrums"] = 0
        ieraksti.append(ieraksts)

    savienojums.close()
    return jsonify(ieraksti)


@lietotne.route("/api/ieraksti", methods=["POST"])
def api_ieraksts_pievienot():
    """
    POST /api/ieraksti
    Saglabā jaunu ražošanas sesijas ierakstu.
    Sagaida JSON: { darbs_id, nepieciesams_skaits, gatavs_skaits, laiks_stundas }
    """
    dati = request.get_json()

    # Izgūst un validē visus nepieciešamos laukus
    try:
        darbs_id           = int(dati["darbs_id"])
        nepieciesams_skaits = int(dati["nepieciesams_skaits"])
        gatavs_skaits      = int(dati["gatavs_skaits"])
        laiks_stundas      = float(dati["laiks_stundas"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"klauda": "Nepareizi vai trūkstoši lauki."}), 400

    # Pārbauda, vai vērtības ir loģiski pareizas
    if nepieciesams_skaits < 1:
        return jsonify({"klauda": "Nepieciešamajam skaitam jābūt vismaz 1."}), 400
    if gatavs_skaits < 0:
        return jsonify({"klauda": "Gatavo skaits nevar būt negatīvs."}), 400
    if laiks_stundas <= 0:
        return jsonify({"klauda": "Laikam jābūt lielākam par nulli."}), 400

    datums = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    savienojums = savienot_db()
    kursors = savienojums.cursor()
    kursors.execute("""
        INSERT INTO ieraksti
            (darbs_id, nepieciesams_skaits, gatavs_skaits, laiks_stundas, datums)
        VALUES (?, ?, ?, ?, ?)
    """, (darbs_id, nepieciesams_skaits, gatavs_skaits, laiks_stundas, datums))
    savienojums.commit()
    jaunais_id = kursors.lastrowid
    savienojums.close()

    return jsonify({"id": jaunais_id, "datums": datums}), 201


# ─────────────────────────────────────────────
# MARŠRUTS: PROGNOZE
# ─────────────────────────────────────────────

@lietotne.route("/api/prognoze", methods=["GET"])
def api_prognoze():
    """
    GET /api/prognoze?darbs_id=N&skaits=M
    Aprēķina prognozēto laiku M produktu izgatavošanai,
    balstoties uz vidējo ātrumu no iepriekšējiem ierakstiem.

    Algoritms:
        1. Iegūst visus derīgos ierakstus (gatavs > 0, laiks > 0)
        2. Aprēķina ātrumu katrai sesijai (produkti / stunda)
        3. Aprēķina vidējo ātrumu
        4. Iegūst prognozēto laiku: skaits / videjais_atrums
    """
    darbs_id = request.args.get("darbs_id", type=int)
    skaits   = request.args.get("skaits",   type=int)

    if not darbs_id or not skaits or skaits < 1:
        return jsonify({"klauda": "Nepieciešams darbs_id un skaits >= 1."}), 400

    savienojums = savienot_db()
    kursors = savienojums.cursor()

    # Iegūst tikai derīgus ierakstus
    kursors.execute("""
        SELECT gatavs_skaits, laiks_stundas FROM ieraksti
        WHERE darbs_id = ? AND gatavs_skaits > 0 AND laiks_stundas > 0
    """, (darbs_id,))
    dati = kursors.fetchall()
    savienojums.close()

    if not dati:
        return jsonify({"klauda": "Nav pietiekami daudz vēsturisko datu prognozei."}), 404

    # Aprēķina vidējo ātrumu no visiem ierakstiem
    atrumu_saraksts = [dict(r)["gatavs_skaits"] / dict(r)["laiks_stundas"] for r in dati]
    videjais_atrums = sum(atrumu_saraksts) / len(atrumu_saraksts)

    if videjais_atrums <= 0:
        return jsonify({"klauda": "Nevar aprēķināt prognozi."}), 400

    # Galvenais aprēķins
    prognozes_laiks = skaits / videjais_atrums

    return jsonify({
        "skaits":          skaits,
        "videjais_atrums": round(videjais_atrums, 3),
        "prognozes_laiks": round(prognozes_laiks, 2),
        "sesiju_skaits":   len(dati)
    })


# ─────────────────────────────────────────────
# PROGRAMMAS IEEJAS PUNKTS
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Inicializē datubāzi pirms servera palaišanas
    inicializet_db()
    print("=" * 45)
    print("  Ražošanas uzskaites sistēma")
    print("  Atver pārlūkprogrammā: http://localhost:5000")
    print("=" * 45)
    # debug=False ražošanas vidē; debug=True izstrādei
    lietotne.run(debug=True, port=5000)
