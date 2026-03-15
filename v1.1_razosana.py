"""
Razosanas uzskaites un prognozes sistema
Autors: Students
Apraksts: Programa, kas lauj ievadīt nepieciešamo produktu skaitu,
          gatavo produktu skaitu, darbu un pavadīto laiku,
          saglaba datos un izrēķina nākotnes prognozi.
"""

import sqlite3
import os
from datetime import datetime

# Datubāzes faila nosaukums
DB_FAILS = "razosana.db"

# ─────────────────────────────────────────────
# DATUBĀZES INICIALIZĀCIJA
# ─────────────────────────────────────────────

def inicializet_db():
    """Izveido datubāzes tabulas, ja tās vēl neeksistē."""
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()

    # Tabula "darbi" - glabā dažādu darbu veidus
    kursors.execute("""
        CREATE TABLE IF NOT EXISTS darbi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nosaukums TEXT NOT NULL UNIQUE,
            apraksts TEXT
        )
    """)

    # Tabula "ieraksti" - glabā katras sesijas datus
    # Saistīta ar "darbi" caur darbs_id (ārējā atslēga)
    kursors.execute("""
        CREATE TABLE IF NOT EXISTS ieraksti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            darbs_id INTEGER NOT NULL,
            nepieciesams_skaits INTEGER NOT NULL,
            gatavs_skaits INTEGER NOT NULL,
            laiks_stundas REAL NOT NULL,
            datums TEXT NOT NULL,
            FOREIGN KEY (darbs_id) REFERENCES darbi(id)
        )
    """)

    savienojums.commit()
    savienojums.close()


# ─────────────────────────────────────────────
# DARBU PĀRVALDĪBA
# ─────────────────────────────────────────────

def pievienot_darbu(nosaukums, apraksts=""):
    """Pievieno jaunu darba veidu datubāzē."""
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    try:
        kursors.execute(
            "INSERT INTO darbi (nosaukums, apraksts) VALUES (?, ?)",
            (nosaukums, apraksts)
        )
        savienojums.commit()
        print(f"  ✓ Darbs '{nosaukums}' veiksmīgi pievienots.")
    except sqlite3.IntegrityError:
        print(f"  ! Darbs '{nosaukums}' jau eksistē.")
    finally:
        savienojums.close()


def sanemت_visus_darbus():
    """Atgriež sarakstu ar visiem darbu veidiem."""
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    kursors.execute("SELECT id, nosaukums, apraksts FROM darbi ORDER BY nosaukums")
    darbi = kursors.fetchall()
    savienojums.close()
    return darbi


def sanemت_darbus():
    """Atgriež sarakstu ar visiem darbu veidiem."""
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    kursors.execute("SELECT id, nosaukums, apraksts FROM darbi ORDER BY nosaukums")
    darbi = kursors.fetchall()
    savienojums.close()
    return darbi


# ─────────────────────────────────────────────
# IERAKSTU PĀRVALDĪBA
# ─────────────────────────────────────────────

def pievienot_ierakstu(darbs_id, nepieciesams_skaits, gatavs_skaits, laiks_stundas):
    """
    Saglabā jaunu ražošanas sesijas ierakstu datubāzē.
    Parametri:
        darbs_id         - darba veida ID
        nepieciesams_skaits - cik produktu nepieciešams
        gatavs_skaits    - cik produktu pagatavoti
        laiks_stundas    - cik stundu pavadīts
    """
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    datums = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kursors.execute("""
        INSERT INTO ieraksti (darbs_id, nepieciesams_skaits, gatavs_skaits, laiks_stundas, datums)
        VALUES (?, ?, ?, ?, ?)
    """, (darbs_id, nepieciesams_skaits, gatavs_skaits, laiks_stundas, datums))
    savienojums.commit()
    savienojums.close()
    print(f"  ✓ Ieraksts saglabāts ({datums})")


def sanemت_ierakstus(darbs_id=None):
    """
    Atgriež ierakstus no datubāzes.
    Ja darbs_id ir norādīts, filtrē pēc darba veida.
    """
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    if darbs_id:
        kursors.execute("""
            SELECT i.id, d.nosaukums, i.nepieciesams_skaits, i.gatavs_skaits,
                   i.laiks_stundas, i.datums
            FROM ieraksti i
            JOIN darbi d ON i.darbs_id = d.id
            WHERE i.darbs_id = ?
            ORDER BY i.datums DESC
        """, (darbs_id,))
    else:
        kursors.execute("""
            SELECT i.id, d.nosaukums, i.nepieciesams_skaits, i.gatavs_skaits,
                   i.laiks_stundas, i.datums
            FROM ieraksti i
            JOIN darbi d ON i.darbs_id = d.id
            ORDER BY i.datums DESC
        """)
    ieraksti = kursors.fetchall()
    savienojums.close()
    return ieraksti


# ─────────────────────────────────────────────
# PROGNOZE
# ─────────────────────────────────────────────

def apreklinat_prognozi(darbs_id, vajadzigs_skaits):
    """
    Aprēķina prognozēto laiku, kas nepieciešams vajadzigs_skaits produktu izgatavošanai.
    Izmanto vidējo ražošanas ātrumu no visiem iepriekšējiem ierakstiem.

    Algoritms:
        1. Iegūst visus ierakstus dotajam darbam
        2. Aprēķina vidējo ātrumu (produkti/stunda)
        3. Izrēķina nepieciešamo laiku
    """
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()

    # Iegūst tikai tos ierakstus, kur gatavots > 0 un laiks > 0
    kursors.execute("""
        SELECT gatavs_skaits, laiks_stundas
        FROM ieraksti
        WHERE darbs_id = ? AND gatavs_skaits > 0 AND laiks_stundas > 0
    """, (darbs_id,))
    dati = kursors.fetchall()
    savienojums.close()

    if not dati:
        return None, "Nav pietiekami daudz vēsturisko datu prognozei."

    # Aprēķina vidējo ātrumu - produkti uz stundu katrā sesijā
    atruми_saraksts = [gatavs / laiks for gatavs, laiks in dati]
    videjais_atrums = sum(atruми_saraksts) / len(atruми_saraksts)

    if videjais_atrums <= 0:
        return None, "Nevar aprēķināt prognozi (ātrums ir nulle)."

    # Aprēķina prognozēto laiku stundās
    prognozes_laiks = vajadzigs_skaits / videjais_atrums

    ziнojums = (
        f"  Vidējais ātrums: {videjais_atrums:.2f} produkti/stundā\n"
        f"  Sesiju skaits datu bāzē: {len(dati)}\n"
        f"  Prognozētais laiks: {prognozes_laiks:.2f} stundas"
    )
    return prognozes_laiks, ziнojums


# ─────────────────────────────────────────────
# LIETOTĀJA SASKARNES PALĪGFUNKCIJAS
# ─────────────────────────────────────────────

def notiret_ekranu():
    """Notīra termināļa ekrānu."""
    os.system('cls' if os.name == 'nt' else 'clear')


def ievade_skaitlis(uzvedne, min_vertiba=None, max_vertiba=None, ir_realais=False):
    """
    Palīgfunkcija skaitliskas ievades apstrādei ar validāciju.
    Atgriež ievadīto skaitli vai None, ja ievade ir nederīga.
    """
    while True:
        try:
            teksts = input(uzvedne).strip()
            vertiba = float(teksts) if ir_realais else int(teksts)
            if min_vertiba is not None and vertiba < min_vertiba:
                print(f"  ! Vērtībai jābūt vismaz {min_vertiba}.")
                continue
            if max_vertiba is not None and vertiba > max_vertiba:
                print(f"  ! Vērtībai jābūt ne vairāk kā {max_vertiba}.")
                continue
            return vertiba
        except ValueError:
            print("  ! Lūdzu, ievadiet derīgu skaitli.")


def izvelet_darbu():
    """
    Rāda darbu sarakstu un ļauj lietotājam izvēlēties vienu.
    Atgriež izvēlētā darba ID vai None.
    """
    darbi = sanemت_darbus()
    if not darbi:
        print("  ! Nav neviena darba veida. Vispirms pievienojiet darbu.")
        return None

    print("\n  Pieejamie darbi:")
    for d in darbi:
        print(f"    [{d[0]}] {d[1]}" + (f" - {d[2]}" if d[2] else ""))

    darbs_id = ievade_skaitlis("  Ievadiet darba ID: ", min_vertiba=1)
    # Pārbaudām, vai ievadītais ID eksistē sarakstā
    esosie_id = [d[0] for d in darbi]
    if darbs_id not in esosie_id:
        print("  ! Šāds darba ID neeksistē.")
        return None
    return darbs_id


# ─────────────────────────────────────────────
# GALVENĀ IZVĒLNE
# ─────────────────────────────────────────────

def izvelt_ievadīt_datus():
    """Apstrādā jauna ieraksta ievadīšanu."""
    print("\n─── Jauna ieraksta pievienošana ───")
    darbs_id = izvelet_darbu()
    if darbs_id is None:
        return

    nepieciesams = ievade_skaitlis("  Nepieciešamo produktu skaits: ", min_vertiba=1)
    gatavs = ievade_skaitlis("  Gatavo produktu skaits: ", min_vertiba=0)
    laiks = ievade_skaitlis("  Pavadītais laiks (stundas): ", min_vertiba=0.01, ir_realais=True)

    pievienot_ierakstu(darbs_id, nepieciesams, gatavs, laiks)


def izvelt_skatit_vesturi():
    """Parāda vēsturiskos ierakstus."""
    print("\n─── Vēsturiskie ieraksti ───")
    darbi = sanemت_darbus()
    if not darbi:
        print("  Nav datu.")
        return

    print("  Filtrēt pēc darba? (0 = visi)")
    for d in darbi:
        print(f"    [{d[0]}] {d[1]}")
    izvele = ievade_skaitlis("  Izvēle: ", min_vertiba=0)

    ieraksti = sanemت_ierakstus(darbs_id=izvele if izvele > 0 else None)
    if not ieraksti:
        print("  Nav ierakstu.")
        return

    print(f"\n  {'ID':<5} {'Darbs':<20} {'Nepiec.':<10} {'Gatavs':<10} {'Laiks':<10} {'Datums'}")
    print("  " + "─" * 70)
    for i in ieraksti:
        print(f"  {i[0]:<5} {i[1]:<20} {i[2]:<10} {i[3]:<10} {i[4]:<10.2f} {i[5]}")


def izvelt_prognozi():
    """Apstrādā prognozes aprēķinu."""
    print("\n─── Ražošanas laika prognoze ───")
    darbs_id = izvelet_darbu()
    if darbs_id is None:
        return

    vajadzigs = ievade_skaitlis("  Cik produktu nepieciešams izgatavot? ", min_vertiba=1)
    laiks, zinojums = apreklinat_prognozi(darbs_id, vajadzigs)

    print()
    if laiks is not None:
        print(f"  Produktu skaits: {vajadzigs}")
        print(zinojums)
    else:
        print(f"  Kļūda: {zinojums}")


def izvelt_pievienot_darbu():
    """Apstrādā jauna darba veida pievienošanu."""
    print("\n─── Jauna darba pievienošana ───")
    nosaukums = input("  Darba nosaukums: ").strip()
    if not nosaukums:
        print("  ! Nosaukums nedrīkst būt tukšs.")
        return
    apraksts = input("  Apraksts (neobligāts): ").strip()
    pievienot_darbu(nosaukums, apraksts)


def galvena_izvele():
    """Galvenā programmas cilpa ar izvēlnes attēlošanu."""
    inicializet_db()

    while True:
        notiret_ekranu()
        print("╔══════════════════════════════════════╗")
        print("║   RAŽOŠANAS UZSKAITES SISTĒMA        ║")
        print("╠══════════════════════════════════════╣")
        print("║  1. Pievienot jaunu ierakstu         ║")
        print("║  2. Skatīt vēstures ierakstus        ║")
        print("║  3. Aprēķināt laika prognozi         ║")
        print("║  4. Pievienot darba veidu            ║")
        print("║  0. Iziet                            ║")
        print("╚══════════════════════════════════════╝")

        izvele = input("  Izvēle: ").strip()

        if izvele == "1":
            izvelt_ievadīt_datus()
        elif izvele == "2":
            izvelt_skatit_vesturi()
        elif izvele == "3":
            izvelt_prognozi()
        elif izvele == "4":
            izvelt_pievienot_darbu()
        elif izvele == "0":
            print("\n  Uz redzēšanos!")
            break
        else:
            print("  ! Nederīga izvēle.")

        input("\n  Nospiediet Enter, lai turpinātu...")


# ─────────────────────────────────────────────
# PROGRAMMAS IEEJAS PUNKTS
# ─────────────────────────────────────────────

if __name__ == "__main__":
    galvena_izvele()
