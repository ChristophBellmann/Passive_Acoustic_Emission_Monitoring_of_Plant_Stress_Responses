# Abgrenzungstabelle: Kamerafreie Richtung [LEGACY — Mai 2026]

> Diese Tabelle dokumentiert die ursprüngliche kamerafreie Richtung.
> Die aktuelle, PRISMA-validierte Abgrenzungstabelle zum akustischen
> Plant-in-the-Loop findet sich in `abgrenzungstabelle_akustisch_pil.md`
> und als Excel in `abgrenzungstabelle_29042026.xlsx`.

## Bewertungslogik

Diese Tabelle grenzt Quellen danach ab, ob sie die kamerafreie wissenschaftliche Hypothese direkt stützen.

| Einstufung | Bedeutung |
|---|---|
| Kernquelle | Direkt relevant für kamerafreie Diagnose, Sensorfusion, Plant-in-the-loop oder Hydroponik |
| Stützquelle | Methodisch oder konzeptionell nützlich, aber nicht exakt auf die Hypothese zugeschnitten |
| Gegenfolie | Fachlich interessant, aber bildgebend oder zu weit vom kamerafreien Ansatz entfernt |

## Optimierte Kerntabelle

Diese reduzierte Tabelle ist die Arbeitsfassung für die eigentliche Argumentation. Sie trennt Kernquellen, Stützquellen und Gegenfolien so, dass die wissenschaftliche Hypothese direkt begründet werden kann.

| Quelle | Pfad | Rolle | PDF | Nutzung | Abgrenzung |
|---|---|---|---:|---|---|
| Kernbach 2024 | Plant-in-the-loop, Biofeedback, CEA | Kernquelle | ja | Begründet Pflanze als aktiven Teil des Regelkreises | zentrale Konzeptquelle |
| Tran et al. 2024 | elektrophysiologische Signale, Nährstoffdefizite | Kernquelle | ja | direkter Beleg für kamerafreie Nährstoffdiagnose | stärker passend als Blattbildklassifikation |
| Ang et al. 2024 | H2O2, Salicylsäure, Nanosensorik | Kernquelle | ja | frühe physiologische Stresssignale | forschungsnah, aber fachlich stark |
| Teixeira et al. 2025 | Wearables, Ionen, pH, Feuchte | Kernquelle | ja | Sensoroptionen für direktes Pflanzenmonitoring | Review statt Einzelimplementierung |
| Yan et al. 2024 | flexible Pflanzensensorik | Kernquelle | ja | direkte Sensorik für Nährstoff-, Umwelt- und Pflanzensignale | breiter als Hydroponik |
| Stahl et al. 2020 | Wasseraufnahme, Transpiration | Kernquelle | nein | Wasserstress ohne Kamera | Volltext nicht frei abgelegt |
| Elvanidi & Katsoulas 2023 | Gewächshausstress, ML, Sensorfeatures | Kernquelle mit Einschränkung | ja | ML-Feature-Reduktion und Stressdiagnose | enthält optische Komponente |
| Ariesen-Verschuur et al. 2022 | Digital Twin, Gewächshaus | Kernquelle | ja | Systemarchitektur für Monitoring und prädiktive Steuerung | nicht spezifisch Nährstoffstress |
| Yu et al. 2025 | Gewächshausregelung, KI, plant-centric AI | Stützquelle | ja | Regelungs- und Modellierungskontext | Klima statt direkte Pflanzendiagnose |
| Mahmood et al. 2023 | robuste MPC, Energie, Unsicherheit | Stützquelle | nein | Unsicherheit in Regelung | kein Pflanzenstressdetektor |
| Langstroff et al. 2021 | kontrollierte Phänotypisierung | Stützquelle | ja | Grenzen kontrollierter Umgebungen | stützt biologische Unsicherheit |
| Massonnet et al. 2010 | Reproduzierbarkeit, biologische Streuung | Stützquelle | nein | zeigt Variabilität trotz Standardisierung | Volltext nicht frei verfügbar |
| van Eeuwijk et al. 2019 | Modellierung, Phänotypisierung | Stützquelle | nein | Messdaten brauchen Modelle | Download blockiert |
| Nagarajan et al. 2025 | Hydroponik, Hyperspektral, Ensemble ML | Gegenfolie | ja | starke Nährstoffdiagnose | bildgebend, daher nicht Kern |
| YOLOv8s Sojabohne | RGB-Bildmodell | Gegenfolie | ja | schnelle Bilddiagnose | kamerabasiert |

## Vollständige 50-Quellen-Tabelle

| Nr. | Quelle | Bereich | Kamerafrei | Relevanz | Nutzung für die Arbeit | Abgrenzung |
|---:|---|---|---|---|---|---|
| 1 | Kernbach 2024: Biofeedback-Based Closed-Loop Phytoactuation | Plant-in-the-loop, Biofeedback, CEA | Ja | Kernquelle | Begründet die Pflanze als aktiven Teil des Regelkreises | Nicht nur Monitoring, sondern Rückkopplung auf Aktorik |
| 2 | Tran et al. 2023: Advanced assessment of nutrient deficiencies with electrophysiological signals | Nährstoffmangel, elektrische Pflanzensignale | Ja | Kernquelle | Direkter Beleg für kamerafreie Nährstoffdiagnose | Besser passend als Blattbildklassifikation |
| 3 | Najdenovska et al. 2023: Universality of electrophysiological signals | elektrische Pflanzensignale, Generalisierung | Ja | Kernquelle | Stützt die Frage nach Übertragbarkeit zwischen Pflanzen | Zeigt Risiko individueller Pflanzenvariation |
| 4 | Buss, Aust & Hamann 2026: Early Detection of Water Stress by Plant Electrophysiology | Wasserstress, ML, Bewässerung | Ja | Kernquelle | Direkter Baustein für Wasserstresshypothese | Preprint, daher vorsichtig einordnen |
| 5 | Applying ML for classification of environmental conditions using plant electrical signals, 2025 | elektrische Signale, Umweltstress | Ja | Kernquelle | Methodik für Zeitreihenklassifikation | Nicht spezifisch Nährstoffmangel |
| 6 | Decoding canola and oat crop health with bioelectrical signals, 2025 | bioelektrische Signale, Dürre, Hitze | Ja | Kernquelle | Belegt nichtbildgebende Stressdiagnose | Feld-/Kulturabhängigkeit prüfen |
| 7 | ML for early detection of plant viruses using electrical signals, 2024 | elektrische Signale, Krankheit | Ja | Stützquelle | Zeigt, dass elektrische Signale Stressarten abbilden können | Biotischer Stress, nicht Kernfokus |
| 8 | Cross-individual electrophysiological signal recognition, 2025 | Domain Adaptation | Ja | Stützquelle | Wichtig für robuste Modelle über Pflanzenindividuen | Methodisch, nicht Hydroponik-spezifisch |
| 9 | Automated Phytosensing: Ozone Exposure Classification, 2024 | Umweltstress, elektrische Signale | Ja | Stützquelle | Beispiel für automatisierte Stressklassifikation | Ozon statt Nährstoff/Wasser |
| 10 | Classifying plant electrical signals using ML, 2025 | ML auf Pflanzensignalen | Ja | Stützquelle | Methodischer Anschluss für Signalverarbeitung | Breiter Stimulus-Fokus |
| 11 | Coatsworth et al. 2022/2023: Continuous Monitoring of Chemical Signals in Plants under Stress | chemische Pflanzensignale | Ja | Kernquelle | Stützt chemische Stressmarker ohne Kamera | Teilweise forschungsnahe Sensorik |
| 12 | Ang et al. 2024: Nanosensor Multiplexing | H2O2, Salicylsäure, frühe Stresswellen | Ja | Kernquelle | Belegt frühe physiologische Stresssignale | Experimentell aufwendiger als pH/EC |
| 13 | Teixeira et al. 2025: Sustainable Wearable Sensors | Wearables, Pflanzensensorik | Ja | Kernquelle | Überblick über tragbare Pflanzensensoren | Review, keine einzelne Implementierung |
| 14 | Yan et al. 2024: Flexible wearable sensors for crop monitoring | flexible Sensoren, Monitoring | Ja | Kernquelle | Ordnet direkte Pflanzensensorik ein | Breiter als Hydroponik |
| 15 | Lee, Wei & Zhu 2021: Emerging Wearable Sensors for Plant Health | Wearables, Plant Health | Ja | Stützquelle | Grundlagen für nichtdestruktives Monitoring | Kein spezifischer Regelungsansatz |
| 16 | Kuruppuarachchi et al. 2025: Advancements in plant wearable sensors | Wearables, Mikroklima | Ja | Kernquelle | Aktueller Überblick für Sensoroptionen | Review-Charakter |
| 17 | Lu et al. 2020: Multimodal Plant Healthcare Flexible Sensor System | flexible multimodale Sensorik | Ja | Kernquelle | Belegt Sensorfusion direkt an Pflanzen | Sensorik anspruchsvoll |
| 18 | Xu et al. 2024: Plant-friendly wearable sensor | Wachstumssensor, Sensorstress | Ja | Stützquelle | Wichtig für Messartefakte durch Sensorbefestigung | Fokus Wachstum, nicht Nährstoffdiagnose |
| 19 | Li et al. 2021: Leaf volatiles by wearable sensor | VOC, Stressdiagnose | Ja | Kernquelle | Nichtvisuelle Stressdiagnose über Blattvolatile | VOCs sind interpretativ mehrdeutig |
| 20 | Li et al. 2019: Smartphone-based fingerprinting of leaf volatiles | VOC, Krankheitsdiagnose | Teilweise | Stützquelle | Gegenmodell zu Bildern: chemische Fingerprints | Smartphone-System, Krankheit statt Nährstoff |
| 21 | Wearable Plant Sensor for VOC Emissions, 2022 | VOC-Sensorik | Ja | Stützquelle | In-situ-Messung nichtvisueller Stresssignale | Nicht zwingend Hydroponik |
| 22 | Wireless plant stress monitoring with chemiresistor gas sensor, 2023 | drahtlose Gassensorik | Ja | Stützquelle | Edge-/IoT-nahe Pflanzensensorik | Stressursache muss abgegrenzt werden |
| 23 | Sempionatto et al. 2022: Wearable chemical sensors | chemische Wearables | Ja | Stützquelle | Methodisches Fundament für kontinuierliche Sensorik | Nicht pflanzenspezifisch |
| 24 | Lew et al. 2020: Species-Independent Analytical Tools | Nanobionik, Sensorik | Ja | Stützquelle | Zeigt artenübergreifende analytische Werkzeuge | Stark forschungsnah |
| 25 | Shi et al. 2024: H2O2 and stomatal opening | H2O2, Physiologie | Ja | Stützquelle | Hintergrund für chemische Signalinterpretation | Kein Diagnosemodell |
| 26 | Next-Generation Ion Monitoring in Closed Hydroponics, 2024 | NO3-, NH4+, PO4, K+ | Ja | Kernquelle | Sehr passend für ionenspezifische Nährlösungssensorik | Fokus Sensorik, nicht ML |
| 27 | IoT-interfaced solid-contact ISEs in hydroponics, 2023 | Ionenselektive Elektroden, IoT | Ja | Kernquelle | Direkter technischer Baustein für Hydroponikmessung | Kalibrierung und Drift beachten |
| 28 | Ion-Specific Nutrient Management in Closed Systems, 2012 | ionenspezifische Nährstoffführung | Ja | Kernquelle | Grundlagenargument gegen bloßes EC-Monitoring | Älter, aber fachlich zentral |
| 29 | Unlocking All-Solid Ion Selective Electrodes, 2022 | ISE, Crop Nutrition | Ja | Stützquelle | Sensoroptionen für miniaturisierte Messung | Eher Sensorreview |
| 30 | Advanced monitoring of hydroponic solutions using ISE and IoT | Hydroponik, ISE, IoT | Ja | Kernquelle | Stützt kamerafreies Nährlösungsmonitoring | Review, Implementierungsdetails prüfen |
| 31 | Comprehensive review of sensing technologies for precision hydroponics, 2025 | Präzisionshydroponik | Ja | Kernquelle | Überblick über Sensorik in Hydroponik | Sehr breit |
| 32 | Automated Hydroponic Nutrient Dosing System, 2025 | pH, EC, Dosierung | Ja | Kernquelle | Stellt Verbindung von Diagnose zu Dosierung her | Häufig pH/EC statt Einzelionen |
| 33 | ML-based analysis of nutrient and water uptake in hydroponic soybeans, 2024 | Nährstoffaufnahme, Wasseraufnahme, ML | Ja | Kernquelle | Direkteste Quelle für kamerafreie ML-Zeitreihen in Hydroponik | Kulturabhängigkeit beachten |
| 34 | Machine learning in nutrient management, 2023 | ML, Nährstoffmanagement | Gemischt | Stützquelle | Breiter Kontext zu ML in Nährstoffmanagement | Nicht streng kamerafrei |
| 35 | Dynamically Controlled Environment Agriculture, 2021 | CEA, Modelle, Optimierung | Ja | Kernquelle | Verbindet dynamische Inputs, Pflanzenwachstum und Steuerung | Eher System-/Konzeptquelle |
| 36 | Reimann et al. 2018: Innovative CEA-basierte Pflanzenproduktion | CEA, Vertical Farming | Ja | Stützquelle | Deutschsprachiger Kontext für CEA-Systeme | Keine Diagnosemethode |
| 37 | Ohmayer et al. 2009: ProdIS-Plant | Datenmanagement, gärtnerische Produktion | Ja | Stützquelle | Kontext für Betriebs- und Sensordaten | Ältere Kontextquelle |
| 38 | Elvanidi & Katsoulas 2023: ML-Based Crop Stress Detection in Greenhouses | Mikroklima, Stress, ML | Teilweise | Kernquelle mit Einschränkung | Sehr guter ML-/Feature-Reduktionsbezug | Enthält optische/PRI-Komponente, daher nicht streng kamerafrei |
| 39 | Stahl et al. 2020: Water Uptake and Transpiration Efficiency | Wasseraufnahme, Transpiration | Ja | Kernquelle | Nichtbildgebende Wasserstressmerkmale | Digitale Phänotypisierung, kein direktes Regelsystem |
| 40 | Khait et al. 2023: Sounds emitted by plants under stress | Pflanzenakustik | Ja | Stützquelle | Belegt kamerafreien Stresskanal über Ultraschall | Forschungsnah, schwerer umzusetzen |
| 41 | Plant bioacoustics: The sound expression of stress, 2023 | Akustik, Einordnung | Ja | Stützquelle | Hilft bei realistischer Einordnung von Akustik | Kommentar statt Hauptstudie |
| 42 | Plants can talk: a new era in plant acoustics, 2023 | Akustik, Perspektive | Ja | Stützquelle | Kontext für akustische Stresssignale | Nicht Kernmethode |
| 43 | Chen et al. 2025: Environmental Control Strategies for Greenhouses | Klima, Regelung | Ja | Kernquelle | Regelungskontext für Temperatur, Feuchte, CO2 | Pflanzenzustand nur indirekt |
| 44 | Yu et al. 2025: Greenhouse temperature prediction and control | Temperaturregelung | Ja | Stützquelle | Modell- und Regelungsmethoden | Klimafokus statt Pflanzendiagnose |
| 45 | Mahmood et al. 2023: Robust MPC for greenhouse temperature | robuste MPC, Energie | Ja | Stützquelle | Unsicherheit und Energie in der Regelung | Kein direkter Pflanzenstressdetektor |
| 46 | Su 2018: Adaptive greenhouse climate control | adaptive Regelung | Ja | Stützquelle | Regelungstechnische Grundlage | Kein Sensorfusionsdiagnosemodell |
| 47 | Chapagain et al. 2022: Crop model uncertainty | Modellunsicherheit | Ja | Stützquelle | Begründet Umgang mit Modellfehlern | Crop-Modell statt Hydroponikdiagnose |
| 48 | van Eeuwijk et al. 2019: Modelling strategies for phenotyping | Phänotypisierung, Modellierung | Teilweise | Stützquelle | Hilft, Messdaten biologisch zu interpretieren | Nicht regelungsnah |
| 49 | Stock 2024: Plant science in the age of simulation intelligence | Simulation, KI, Pflanzenwissenschaft | Ja | Stützquelle | Konzeptioneller Rahmen für Modellkopplung | Breiter Überblick |
| 50 | Ariesen-Verschuur et al. 2022: Digital Twins in greenhouse horticulture | Digital Twin, Gewächshaus | Ja | Kernquelle | Systemarchitektur für Monitoring und prädiktive Steuerung | Digital Twin breiter als konkrete Stressdiagnose |

## Quellen, die bewusst nicht als Kern der kamerafreien Richtung zählen

| Quelle | Warum nicht Kernquelle? | Trotzdem nutzbar als |
|---|---|---|
| Early and accurate nutrient deficiency detection in hydroponic crops using ensemble ML and hyperspectral imaging | Hyperspektralbildgebung ist bildgebend | Gegenfolie für Nährstoffdiagnose mit Kamera |
| Rapid detection of soybean nutrient deficiencies with YOLOv8s | Kamera-/Bildmodell | Abgrenzung zu CNN-Ansätzen |
| Machine and deep learning for prediction of nutrient deficiency in wheat leaf images | Blattbilder | Abgrenzung zu Symptomerkennung |
| Machine/deep learning techniques for disease and nutrient deficiency disorder diagnosis in rice crops | Überwiegend bildbasierte Diagnose | Review-Gegenfolie |
| Deep Learning in Multimodal Fusion for Sustainable Plant Care | Enthält viele Bildsensoren | Methodische Gegenfolie für Sensorfusion |
| A review on ML/DL techniques for plant leaf disease detection | Blattkrankheiten und Bilder | Zeigt, warum Disease-CNN nicht Ziel ist |

## Ergebnis der Abgrenzung

Die stärkste wissenschaftliche Linie ist nicht `Kamera gegen Sensor`, sondern:

**Kamerafreie Sensorfusion für regelungsnahe Pflanzenzustandsdiagnose.**

Damit wird die Arbeit klar abgegrenzt:

- nicht visuelle Symptomklassifikation,
- nicht reine Gewächshausklimaregelung,
- nicht nur pH/EC-Grenzwertüberwachung,
- sondern frühe Erkennung physiologischer Abweichungen aus Nährlösung, Pflanze und Umgebung.

Die Kernquellen für die Hypothese sind vor allem: Kernbach 2024, Tran et al. 2023, Buss et al. 2026, Coatsworth et al. 2022/2023, Ang et al. 2024, Teixeira et al. 2025, Yan et al. 2024, Next-Generation Ion Monitoring 2024, IoT-interfaced ISEs 2023, Ion-Specific Nutrient Management 2012, ML-based nutrient and water uptake 2024, Dynamically Controlled Environment Agriculture 2021 und Ariesen-Verschuur et al. 2022.
