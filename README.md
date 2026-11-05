# 🌲 Canopy Analyzer

> **Moderní a rychlý nástroj pro hodnocení zápoje korun (Canopy Closure / Cover) a otevřenosti oblohy (Canopy Openness) z hemisférických fotografií („rybí oko“ / fisheye).**

### 🌐 [👉 SPUSTIT WEBOVOU APLIKACI (ONLINE V PROHLÍŽEČI)](https://adelasamuelova-a11y.github.io/canopy-analyzer/)
*Běží okamžitě na jakémkoliv počítači, mobilu i tabletu bez instalace a bez nutnosti mít Python!*

Tento program slouží jako moderní, jednoduchá a spolehlivá alternativa ke starým nástrojům (jako je např. *Gap Light Analyzer - GLA*), která nevyžaduje složité ruční nastavování, nezamrzá na moderních systémech a podporuje prohlížení jednotlivých fotografií i hromadné dávkové vyhodnocení celých složek.

---

## ✨ Klíčové funkce

* **Vkládání jednotlivých i hromadných fotografií:** Můžete vybrat jednu fotku, označit jich v dialogu desítky najednou, nebo načíst celou složku.
* **Prohlížení snímků krok za krokem:** Tlačítka `◀ Předchozí` a `Další ▶` umožňují pohodlně procházet fotku po fotce.
* **Výpočet obou klíčových parametrů:**
  * 🌲 **Zápoj korun (Canopy Cover / Closure %)** = černá plocha větví, kmenů a listoví.
  * ☁️ **Otevřenost oblohy (Canopy Openness %)** = bílá plocha oblohy a mezer.
* **Vědecká binarizace přes modrý kanál:** Používá modrý spektrální kanál (Blue channel), který zaručuje nejvyšší kontrast mezi oblohou a vegetací.
* **Automatické prahování (Otsu's thresholding):** Program sám spočítá matematicky optimální práh, který lze okamžitě doladit živým posuvníkem.
* **Automatická detekce kruhu objektivu:** Inteligentně detekuje a odřízne černý lem objektivu rybího oka (s možností jemného ručního doladění středu $X, Y$ a poloměru $R$).
* **Export do Excelu (CSV):** Tlačítko **„Spočítat vše v seznamu a exportovat do CSV“** projde všechny fotky ve frontě, vygeneruje přehlednou tabulku CSV (připravenou přímo pro český Excel s desetinnými čárkami) a uloží černobílé masky.

---

## 🚀 Rychlé spuštění (Instalace)

### Požadavky:
* Python 3.8 nebo novější
* Nainstalované knihovny: `opencv-python`, `pillow`, `numpy`

### 1. Klonování repozitáře
```bash
git clone https://github.com/vase-jmeno/canopy-analyzer.git
cd canopy-analyzer
```

### 2. Instalace závislostí
```bash
pip install -r requirements.txt
```

### 3. Spuštění aplikace
* **Ve Windows:** Stačí dvakrát kliknout na `Spustit_CanopyAnalyzer.bat` (nebo spustit `python CanopyAnalyzer.py`).
* **V Linuxu / macOS:**
  ```bash
  python3 CanopyAnalyzer.py
  ```

---

## 📖 Jak s aplikací pracovat

1. **Načtení fotografií:**
   * Klikněte na **„📂 Vložit fotografie“** a vyberte jednu nebo více fotek.
   * Nebo klikněte na **„📁 Načíst celou složku s fotkami“**.
2. **Prohlížení a kontrola:**
   * Pomocí tlačítek `◀ Předchozí` a `Další ▶` můžete procházet snímky.
   * Na obrazovce ihned vidíte:
     * Vlevo původní snímek se zeleným kruhem vymezení objektivu.
     * Vpravo výslednou černobílou masku.
     * V postranním panelu přesné hodnoty **Zápoje korun** a **Otevřenosti oblohy** v %.
3. **Doladění prahu (volitelné):**
   * Pokud chcete oblohu více prosvětlit nebo ztmavit, pohněte posuvníkem **Práh (0–255)**.
   * Tlačítko **„⚡ Nastavit optimální práh (Otsu)“** vrátí matematicky přesnou hodnotu.
4. **Hromadný export:**
   * Klikněte na **„📊 Spočítat vše v seznamu a exportovat do CSV“**.
   * Zvolte cílovou složku. Program během několika sekund zpracuje všechny fotografie, uloží černobílé obrázky a vytvoří soubor `vysledky_zapoj_batch.csv`.

---

## 🔬 Metodický podklad

Při vyhodnocování hemisférických fotografií platí základní vztah:

$$\text{Canopy Closure (\%)} + \text{Canopy Openness (\%)} = 100\,\%$$

* **Modrý kanál:** Vegetace silně absorbuje modré světlo (kolem 450 nm), zatímco rozptýlené světlo oblohy má v modrém spektru maximum. Použití modrého kanálu minimalizuje chyby způsobené chromatickou aberací na okrajích čoček rybího oka.
* **Otsuova binarizace:** Minimalizuje vnitrotřídní rozptyl jasu a maximalizuje mezitřídní rozptyl mezi oblohou a korunami stromů.

---

## 📄 Licence
Tento projekt je licencován pod licencí MIT - viz soubor [LICENSE](LICENSE).
