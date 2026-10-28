# Yuki Radar

Snöprognos, lavinläge, liftar, onsen/bastu, toaletter och parkering för skidresor med husbil i **Japan** och **Skandinavien** (Sverige, Norge, Finland).

- **Startsidan** har ett val mellan Japan och Skandinavien och rankar orterna efter hur mycket snö som fallit de senaste 3 dygnen, eller hur mycket som väntas de kommande 3 dygnen.
- **Varje ort** har en detaljerad prognos (topp och dal, timme för timme, nollgradersgräns) och en karta med liftar, onsen, toaletter, michi-no-eki och andra ställplatser, med vägbeskrivning i Google Maps.

Allt ligger i `index.html`. Öppna filen i en webbläsare, eller publicera repot med GitHub Pages för att använda appen i mobilen.

## Datakällor

- Väder: [Open-Meteo](https://open-meteo.com/), hämtas live när sidan öppnas.
- Lavinprognos Norge: [Varsom](https://www.varsom.no/) (NVE), hämtas live i appen.
- Lavinprognos Sverige: [lavinprognoser.se](https://www.lavinprognoser.se/) (Naturvårdsverket), hämtas varje morgon tillsammans med JAN.
- Lavinprognos Japan: [Japan Avalanche Network](https://data.nadare.jp/avalanche_informations?locale=en). Hämtas varje morgon av GitHub Actions (`.github/workflows/avalanche.yml`) och byggs in i `index.html`.
- Liftar, onsen, toaletter och parkering: [OpenStreetMap](https://www.openstreetmap.org/copyright) via Overpass API. Datan är inbyggd i `index.html` så att den fungerar utan täckning.
- Karta: [OpenFreeMap](https://openfreemap.org/), eller Google Maps om du lägger in en egen API-nyckel under "Kartinställning" längst ner på sidan.

## Lägga till orter

Nya orter läggs i en JSON-fil med ungefärliga koordinater och placeras sedan exakt utifrån liftarna:

```bash
python3 tools/refine_resorts.py data/scandinavia_approx.json data/scandinavia.json
```

## Uppdatera platsdatan

```bash
python3 tools/fetch_pois.py index.html data/pois.json
python3 tools/inject.py index.html data/pois.json
python3 tools/fetch_lifts.py index.html data/lifts.json
python3 tools/inject_lifts.py index.html data/lifts.json
python3 tools/fetch_avalanche.py data/avalanche.json
python3 tools/inject_avalanche.py index.html data/avalanche.json
```

`fetch_pois.py` hoppar över orter som redan finns i `data/pois.json`. Ta bort filen för att hämta allt på nytt. Overpass-servrarna är ofta överbelastade, så räkna med att det tar en stund.
