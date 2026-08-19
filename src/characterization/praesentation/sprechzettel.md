# Sprechzettel — Abschlusspräsentation Projekt I1

**Passive akustische Emissions-Überwachung von Pflanzenstress**
Christoph Bellmann · TH Augsburg · Systems Engineering

> Ein Abschnitt pro Folie. Fett = Kernaussage, die auf jeden Fall fallen muss.
> Zeitrichtwert gesamt: ~12–15 min (≈ 1 min/Folie, Kernfolien 7/8 etwas länger).

---

## Folie 1 — Titel

Begrüßung. Kurz vorstellen, Thema nennen.

> „Ich stelle heute die Frage: **Kann man mit kostengünstiger Hardware — einem Piezo, einem Standard-Operationsverstärker und einem Oszilloskop — akustische Emissionen von Pflanzen unter Wasserstress messen?** Ich zeige den Aufbau, wie ich das System charakterisiert habe, und das entscheidende Experiment dazu."

Nicht zu lange verweilen — direkt zur Motivation.

---

## Folie 2 — Motivation & Ziel

Warum überhaupt akustische Emissionen (AE) von Pflanzen?

- Pflanzen erzeugen winzige elastische Wellen — aus **Xylem-Kavitation** (Wassersäule reißt) und Zellwand-Mikrorissen.
- Diese AE **steigt unter Wasserstress** → wäre ein Echtzeit-Proxy für die Bewässerungssteuerung. Idee: „Trockenheit hörbar machen".
- Klassische Forschung nutzt dafür **teure resonante Ultraschallsensoren > 100 kHz**.

> **„Die Leitfrage dieser Arbeit: Reicht dafür auch billige Hardware — oder nicht?"**

Rechts die vier Beiträge kurz ankündigen (Charakterisierung, Laufzeit, Experiment, Rauschquellen) — das ist die Gliederung des Vortrags.

---

## Folie 3 — Aufbau: Das Messsystem

Der Schaltplan der Messkette.

- **CH1 = Boden-Piezo im Wurzelbereich** — das ist der eigentliche Pflanzenkanal.
- **CH3 / CH4 = zwei Referenz-Piezos an einem Stahlstab** — für Laufzeitmessung und Kalibrierung.
- CH2 ist defekt und wird ausgelassen.
- Verstärkung mit dem **LM358** (Cent-Verstärker), Aufnahme mit dem Rigol DS1104Z im Deep-Memory-Modus: 500 kSa/s, 300 000 Punkte pro Frame (0,6 s).

> **Kernaussage: „Bewusst kostengünstige Kette — und genau deren Grenzen will ich quantifizieren."**

---

## Folie 4 — Realer Messaufbau & Oszilloskop-Signal

Diese Folie macht den abstrakten Schaltplan greifbar.

- **Links:** Foto des realen Aufbaus — die Pflanze mit dem Boden-Piezo (CH1).
- **Rechts:** ein **tatsächlich aufgenommenes** Oszilloskop-Spektrum (aus dem Bewässerungsexperiment, Zustand nach dem Gießen).

> „So sieht das im Labor wirklich aus — links das Setup, rechts ein echtes Messsignal. Auf dieser Datenbasis beruht die gesamte folgende Charakterisierung."

Kurz halten — es ist eine Überleitungs-/Realitätsfolie.

---

## Folie 5 — Vorgehen: Messgrößen und Auswertung

Drei Spalten, je einen Satz:

- **Aufnahme:** Deep-Memory (500 kSa/s, 0,6 s/Frame); ein **Raspberry Pi Pico erzeugt einen bekannten 20–100 kHz-Chirp** — dadurch kenne ich das Eingangssignal und kann die Kette exakt vermessen.
- **Kennzahlen:** **Kohärenz γ²** (sehen zwei Kanäle dasselbe?), **MLE-Laufzeit τ̂** zwischen Sensoren, **Bandenergien** in 5-kHz-Bins.
- **Statistik:** Wilcoxon (gepaart prä/post), **FDR-Korrektur** gegen Mehrfachtests, Kendall τ für Trend + Mann–Whitney drift-korrigiert.

> Betonen: **„Die Statistik ist bewusst streng — inklusive Kontrolle auf Drift."** Das wird auf Folie 9 wichtig.

---

## Folie 6 — Systemcharakterisierung (1/3): Nutzbares Frequenzband

Ergebnis des Pico-Chirp-Sweeps (fig2).

- **Links:** Kohärenz nahe 1 bis ~35 kHz → beide Referenzsensoren sehen dasselbe, die Kette überträgt sauber.
- **Rechts:** oberhalb ~35 kHz fällt die Amplitude ab — das ist die **Grenze des LM358**. Die Peaks sind Eigenmoden des Stahlstabs.

> **Kernaussage: „Kalibriertes Band 5–35 kHz (γ² ≥ 0,95). Darüber bricht der Verstärker ein — das eigentliche Kavitationsband (100–500 kHz) ist mit dieser Hardware unerreichbar."**

Das ist bereits ein erstes hartes Limit.

---

## Folie 7 — Systemcharakterisierung (2/3): Sensorgeometrie über Laufzeit

Laufzeitmessung (fig3).

- **Links:** Im Nutzband liegt die Laufzeitdifferenz innerhalb **±0,3 µs** → die beiden Sensoren sind gleich weit entfernt (äquidistant). Bestätigt die Geometrie.
- **Rechts:** An der 9,17-kHz-Stahlresonanz ein **konstanter +1,95-µs-Versatz**, über alle Frames identisch.

> Wichtig richtig einordnen: **„Dieser Versatz ist ein Resonanz-Phasenartefakt — kein Weglaufunterschied."** Zeigt, dass ich das Signal physikalisch verstehe und Artefakte von echten Effekten trenne.

---

## Folie 8 — Systemcharakterisierung (3/3): Die Rauschgrenze *(Kernfolie)*

Das ist der entscheidende Punkt — hier Zeit lassen (fig4).

- Ohne anliegendes Signal aufgenommen → das ist das **reine Eigenrauschen** jedes Kanals.
- CH4 ist am leisesten (reines Verstärker-Grundrauschen, ~26 mV RMS — das physikalische Limit).
- **CH1, der Pflanzenkanal, ist mit 137 mV RMS am lautesten** — dominiert durch 1/f-Rauschen und Netzeinkopplung.

> **Kernaussage (rot): „Jedes Pflanzensignal müsste diese Kurve erst überschreiten. Genau das ist die Nachweisschwelle."**

Diese Folie erklärt später, *warum* das Experiment negativ ausfällt.

---

## Folie 9 — Experiment: Bewässerung

Das eigentliche Experiment (fig5): Ficus benjamina, ein einzelnes Bewässerungsereignis.

- Das Signal **driftet nur langsam nach oben** — der Verstärker erwärmt sich. **Kein Sprung** beim Gießen.
- Wichtig: Der **naive Test wäre fälschlich signifikant** geworden (p = 0,002). Erst die **Drift-Kontrolle** deckt auf, dass das reine thermische Verstärker-Drift ist (Kendall τ = +0,69).

> **Kernaussage: „Nach Drift-Korrektur kein Effekt (p = 0,86). Der scheinbare Befund war ein Artefakt."**

Das ist der methodische Kern der Arbeit — sauber gegen ein Scheinergebnis abgesichert.

---

## Folie 10 — Kontrolle: Positivkontrolle

Die Gegenprobe (fig7) — beugt dem Einwand „vielleicht ist nur die Auswertung blind?" vor.

- Ich speise ein **bekanntes Signal** in CH1 ein.
- Die Auswertung trennt es mit **+52,6 dB Abstand** klar vom stillen Kanal (p < 10⁻¹²).

> **Kernaussage (grün): „Findet die Pipeline nichts, ist wirklich nichts da. Das Negativergebnis ist echt — kein Pipeline-Fehler."**

---

## Folie 11 — Fazit

Ehrliche Zusammenfassung.

- Messband 5–35 kHz charakterisiert, Sensorgeometrie über Laufzeit bestätigt.
- **Kein Pflanzen-AE detektierbar** im Bewässerungsexperiment — nach strenger Drift-Korrektur (p = 0,86).
- Positivkontrolle belegt: Auswertung funktioniert, Negativergebnis ist belastbar.

> **Kernaussage (rot): „Das Hauptlimit ist die LM358-Rauschgrenze — 137 mV RMS, rund 20–40 dB über erwarteten AE-Amplituden. Zusätzlich schließt die Bandbreite < 35 kHz das eigentliche Kavitationsband aus."**

Framing: **„Mit dieser Hardware kein Nachweis — aber wir wissen jetzt genau, warum. Und das ist verwertbar."**

---

## Folie 12 — Ausblick: Weg zur Nachweisbarkeit

Konkrete, priorisierte Hardware-Maßnahmen mit geschätztem Gewinn:

1. Rauscharmer Vorverstärker (z. B. OPA2134) → ≈ 18 dB
2. Hardware-Hochpass 1 kHz am Eingang (gegen 1/f + Netz) → ≈ 20 dB
3. Resonanter 150-kHz-Piezo + 5-MSa/s-ADC → erschließt das Kavitationsband
4. Mechanische Isolation → weniger Störungen

> **Kernaussage: „Schritt 1 und 2 zusammen bringen CH1 unter 5 mV RMS — in Reichweite starker AE-Ereignisse."** Die ersten beiden sind billig und wirksam.

---

## Folie 13 — Abschluss / Dank

Zusammenfassung in drei Sätzen, dann Dank.

> „Zusammengefasst: **Das System ist charakterisiert** (Band 5–35 kHz, äquidistante Sensoren). **Kein Pflanzen-AE nachweisbar — begründet durch die Rauschgrenze, nicht durch die Auswertung.** Und: **ein klarer, priorisierter Weg zur Nachweisbarkeit** ist aufgezeigt. Vielen Dank — ich beantworte gern Ihre Fragen."

Hinweis: Daten, Code und Paper liegen unter `src/characterization/`.

---

### Mögliche Rückfragen (Backup)

- **„Warum kein resonanter Ultraschallsensor von Anfang an?"** → Ziel war explizit, die Grenzen kostengünstiger Standardhardware zu quantifizieren — nicht, bekannte teure Sensoren zu bestätigen.
- **„Ist ein einzelnes Bewässerungsereignis aussagekräftig?"** → Für die Nachweisgrenze ja: die Rauschanalyse (Folie 8) ist vom Experiment unabhängig und limitiert grundsätzlich. Mehr Ereignisse würden das SNR nicht ändern.
- **„Woher kommt die thermische Drift?"** → Erwärmung der LM358-Stufe nach Einschalten/Umgebung; monotoner Trend, kein Ereignisbezug (Kendall τ = +0,69).
