import sqlite3
import os
from datetime import datetime

DB_FAILS = "razosana.db"

def inicializet_db():
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    kursors.execute("""
        CREATE TABLE IF NOT EXISTS darbi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nosaukums TEXT NOT NULL UNIQUE,
            apraksts TEXT
        )
    """)
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

def pievienot_darbu(nosaukums, apraksts=""):
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    try:
        kursors.execute("INSERT INTO darbi (nosaukums, apraksts) VALUES (?, ?)", (nosaukums, apraksts))
        savienojums.commit()
        print(f"  ✓ Darbs '{nosaukums}' pievienots.")
    except sqlite3.IntegrityError:
        print(f"  ! Darbs '{nosaukums}' jau eksistē.")
    finally:
        savienojums.close()

def sanemت_darbus():
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    kursors.execute("SELECT id, nosaukums, apraksts FROM darbi ORDER BY nosaukums")
    darbi = kursors.fetchall()
    savienojums.close()
    return darbi

def pievienot_ierakstu(darbs_id, nepieciesams_skaits, gatavs_skaits, laiks_stundas):
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
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    if darbs_id:
        kursors.execute("""
            SELECT i.id, d.nosaukums, i.nepieciesams_skaits, i.gatavs_skaits, i.laiks_stundas, i.datums
            FROM ieraksti i JOIN darbi d ON i.darbs_id = d.id
            WHERE i.darbs_id = ? ORDER BY i.datums DESC
        """, (darbs_id,))
    else:
        kursors.execute("""
            SELECT i.id, d.nosaukums, i.nepieciesams_skaits, i.gatavs_skaits, i.laiks_stundas, i.datums
            FROM ieraksti i JOIN darbi d ON i.darbs_id = d.id ORDER BY i.datums DESC
        """)
    ieraksti = kursors.fetchall()
    savienojums.close()
    return ieraksti

def apreklinat_prognozi(darbs_id, vajadzigs_skaits):
    savienojums = sqlite3.connect(DB_FAILS)
    kursors = savienojums.cursor()
    kursors.execute("""
        SELECT gatavs_skaits, laiks_stundas FROM ieraksti
        WHERE darbs_id = ? AND gatavs_skaits > 0 AND laiks_stundas > 0
    """, (darbs_id,))
    dati = kursors.fetchall()
    savienojums.close()
    if not dati:
        return None, "Nav pietiekami daudz datu."
    atruми = [g / l for g, l in dati]
    videjais = sum(atruми) / len(atruми)
    if videjais <= 0:
        return None, "Atrums ir nulle."
    laiks = vajadzigs_skaits / videjais
    return laiks, f"  Atrums: {videjais:.2f} gab/h | Laiks: {laiks:.2f} h | Sesijas: {len(dati)}"

def ievade_skaitlis(uzvedne, min_vertiba=None, max_vertiba=None, ir_realais=False):
    while True:
        try:
            v = float(input(uzvedne)) if ir_realais else int(input(uzvedne))
            if min_vertiba is not None and v < min_vertiba:
                print(f"  ! Minimums: {min_vertiba}")
                continue
            if max_vertiba is not None and v > max_vertiba:
                print(f"  ! Maksimums: {max_vertiba}")
                continue
            return v
        except ValueError:
            print("  ! Ievadiet skaitli.")

def izvelet_darbu():
    darbi = sanemت_darbus()
    if not darbi:
        print("  ! Nav darbu. Pievienojiet darbu ar izveli 4.")
        return None
    print("\n  Darbi:")
    for d in darbi:
        print(f"    [{d[0]}] {d[1]}" + (f" - {d[2]}" if d[2] else ""))
    darbs_id = ievade_skaitlis("  Darba ID: ", min_vertiba=1)
    if darbs_id not in [d[0] for d in darbi]:
        print("  ! Nav sada ID.")
        return None
    return darbs_id

def galvena_izvele():
    inicializet_db()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("╔══════════════════════════════════════╗")
        print("║   RAZOSANAS UZSKAITES SISTEMA        ║")
        print("╠══════════════════════════════════════╣")
        print("║  1. Pievienot ierakstu               ║")
        print("║  2. Skatit vesturi                   ║")
        print("║  3. Prognoze                         ║")
        print("║  4. Pievienot darba veidu            ║")
        print("║  0. Iziet                            ║")
        print("╚══════════════════════════════════════╝")
        izvele = input("  Izvele: ").strip()
        if izvele == "1":
            darbs_id = izvelet_darbu()
            if darbs_id:
                n = ievade_skaitlis("  Nepieciesams: ", min_vertiba=1)
                g = ievade_skaitlis("  Gatavs: ", min_vertiba=0)
                l = ievade_skaitlis("  Laiks (h): ", min_vertiba=0.01, ir_realais=True)
                pievienot_ierakstu(darbs_id, n, g, l)
        elif izvele == "2":
            darbi = sanemت_darbus()
            print("  0 = visi")
            for d in darbi:
                print(f"    [{d[0]}] {d[1]}")
            f = ievade_skaitlis("  Filtret: ", min_vertiba=0)
            for i in sanemت_ierakstus(f if f > 0 else None):
                print(f"  [{i[0]}] {i[1]} | nep:{i[2]} gat:{i[3]} laiks:{i[4]:.2f}h | {i[5]}")
        elif izvele == "3":
            darbs_id = izvelet_darbu()
            if darbs_id:
                v = ievade_skaitlis("  Cik produktu? ", min_vertiba=1)
                _, msg = apreklinat_prognozi(darbs_id, v)
                print(msg)
        elif izvele == "4":
            n = input("  Nosaukums: ").strip()
            if n:
                a = input("  Apraksts: ").strip()
                pievienot_darbu(n, a)
        elif izvele == "0":
            break
        input("\n  Enter - turpinat...")

if __name__ == "__main__":
    galvena_izvele()
