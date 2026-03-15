# Ražošanas uzskaites un prognozes sistēma
**Programmēšana II – Projekta arhīvs**

---

## Failu struktūra

```
razosanas-uzskaite/
│
├── README.md                  ← šis fails
│
├── v1.0_razosana.py           ← pamata kods (bez komentāriem, konsoles saskarne)
├── v1.1_razosana.py           ← ar detalizētiem komentāriem latviešu valodā
│
├── v1.2_serveris.py           ← Flask web serveris (REST API)
├── v1.2_index.html            ← HTML/CSS/JS tīmekļa saskarne
│
└── dokumentacija.docx         ← pilna projekta dokumentācija
```

---

## Versiju vēsture

### v1.0 – Pamata konsoles kods
Pirmā darbojoša versija ar konsoles saskarni.
- Datubāze ar 2 saistītām tabulām (`darbi` ↔ `ieraksti`)
- Darbu veidu pievienošana
- Ražošanas sesiju ierakstīšana
- Vēstures skatīšana ar filtrēšanu
- Prognozes aprēķins pēc vidējā tempa
- **Nav** komentāru

---

### v1.1 – Ar komentāriem
Balstīta uz v1.0, kods nav mainīts.
- Katrai funkcijai pievienots `docstring` latviešu valodā
- Komentāri pie datubāzes vaicājumiem un loģikas blokiem
- Sadaļu atdalītāji labākai lasāmībai

---

### v1.2 – Tīmekļa saskarne (HTML + Flask)
Pilna versija ar grafisku interfeisu pārlūkprogrammā.

**Jaunie faili:**
- `v1.2_serveris.py` — Flask REST API serveris (aizvieto konsolei)
- `v1.2_index.html` — pilna tīmekļa saskarne ar 4 skatiem:
  - **Ievade** – jaunu ierakstu pievienošana + pēdējo 5 ierakstu tabula
  - **Vēsture** – visi ieraksti ar filtrēšanu, ātrumu un izpildes % aprēķinu
  - **Prognoze** – laika prognoze ar vizuālu rezultātu paneli
  - **Darbi** – darbu veidu pārvaldība

---

## Palaišana

### v1.0 / v1.1 (konsoles versija)
Nepieciešams: **Python 3.8+**
```bash
python v1.1_razosana.py
```

### v1.2 (tīmekļa versija) — IETEICAMA
Nepieciešams: **Python 3.8+** un **Flask**
```bash
pip install flask
python v1.2_serveris.py
```
Atver pārlūkprogrammā: **http://localhost:5000**

