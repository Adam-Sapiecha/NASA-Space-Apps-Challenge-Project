import json
from pathlib import Path
from astropy.time import Time

def main():
    report = json.loads(Path("data/audit/coverage.json").read_text(encoding="utf-8"))
    lines = ["# Rzeczywisty audyt danych — 14 listopada 2026", "",
             "Wykonano zapytania SIA do IRSA, kolekcja `spherex_dr1`, promień wyszukiwania 2 minuty łuku wokół pozycji startowych. Surowe odpowiedzi: `data/audit/*.ecsv`; podsumowanie: `data/audit/coverage.json`. Te pliki są lokalnym cache i nie trafiają do repozytorium.", "",
             "| Pole wokół obiektu | Rekordy SIA | Pierwsza obserwacja UTC | Ostatnia obserwacja UTC |",
             "|---|---:|---|---|"]
    for item in report:
        if "count" in item and item["count"]:
            start = Time(item["mjd_min"],format="mjd").isot[:10]
            end = Time(item["mjd_max"],format="mjd").isot[:10]
            lines.append(f"| {item['name']} | {item['count']} | {start} | {end} |")
        else:
            lines.append(f"| {item['name']} | — | {item.get('error','Brak danych')} | — |")
    lines += ["", "## Co potwierdzono", "",
              "- Archiwum odpowiada i ma obrazy przecinające wszystkie pięć pól.",
              "- Odczytano rzeczywiste FITS IMAGE, FLAGS i WCS-WAVE. Wykonano reprojekcję i utworzono podglądy oraz manifesty.",
              "- OBSID może być wspólny dla różnych detektorów; produkty deduplikujemy po URL, nie po samym OBSID.",
              "- Archiwum okresowo zwraca HTTP 503 (Server busy). Pobieranie ma trzy próby, a pominięte produkty są jawnie zapisane.", "",
              "## Czego ten audyt nie potwierdza", "",
              "Liczby oznaczają rekordy obrazów pola, nie liczbę detekcji obiektu ani niezależnych epok. Różne detektory mogą obserwować równocześnie. Nie wykonano propagacji pozycji katalogowych ani niezależnej identyfikacji źródeł. Pokrycie pola nie dowodzi wykrywalnego ruchu lub zmienności. Końcowy raport pięciu obiektów wymaga jeszcze porównania zgodnych pasm, kontroli lokalnego pokrycia, identyfikacji źródeł i oceny wyniku.", ""]
    demo = Path("data/demo.json")
    if demo.exists():
        info = json.loads(demo.read_text(encoding="utf-8"))
        lines += ["## Lokalny przykład obrazowy", "",
                  f"Analiza `{info['id']}`: {len(info['frames'])} udanych klatek, {len(info['failures'])} nieudanych pobrań. Link: `http://127.0.0.1:8000/?analysis={info['id']}`.", "",
                  "Jest to przykład działania pipeline i interfejsu. Nie stanowi potwierdzenia wykrycia ruchu Barnard’s Star. Zgodność pasm należy odczytać w miejscu źródła.", ""]
    Path("RAPORT_DANYCH.md").write_text("\n".join(lines),encoding="utf-8")

if __name__ == "__main__":
    main()
