# Abgrenzungstabelle: Akustisches Plant-in-the-Loop für Wachstumsdetektion

## Forschungsfrage

Kann pflanzliche akustische Emission (Ultraschall) als Echtzeit-Feedback-Signal in einem geschlossenen Plant-in-the-Loop-Regelkreis zur Wachstums- und Stressdetektion genutzt werden — ein bisher unerforschter Ansatz?

## Bewertungslogik

| Einstufung | Bedeutung |
|---|---|
| Kernquelle | Direkt relevant für akustische Pflanzensignale, Plant-in-the-Loop, oder Closed-Loop-Wachstumsregelung |
| Stützquelle | Methodisch oder konzeptionell nützlich für Teilaspekte (Sensorik, Signalverarbeitung, Regelung) |
| Gegenfolie | Bildbasiert, kameraabhängig, oder thematisch zu weit vom akustischen PIL-Ansatz entfernt |

---

## Abgrenzungstabelle (67 Quellen + Zotero-Integration)

| Nr. | Quelle | Sensor-/Methodenpfad | Rolle | Nutzung für die Arbeit | Abgrenzung / Entscheidung |
|---:|---|---|---|---|---|
| **A — Plant-in-the-Loop / Closed-Loop-Regelung mit Pflanzen (8 Quellen)** |
| 1 | Kernbach (2024): Biofeedback-based closed-loop phytoactuation in vertical farming and CEA | Elektrophysiologie, Biofeedback, Phytolight, Irrigation | Kern | Zentrale PIL-Konzeptquelle: Pflanze als aktiver Teil des Regelkreises via elektrische Signale | Nutzt Elektrophysiologie, nicht Akustik — akustische Emission unerforscht |
| 2 | Damian et al. (2014): Automated physiological recovery of avocado plants for plant-based adaptive machines | Elektrophysiologie, Closed-Loop, Wasserstress | Kern | Erste Closed-Loop-Interaktion Pflanze–Maschine mit elektrophysiologischem Feedback | Belegt PIL-Prinzip, aber ohne akustische Komponente |
| 3 | Dai et al. (2026): Interlocked liquid metal wearables for plant phenotyping and stress decoding | Wearable, Elektrostimulation, Closed-Loop-Feedback | Kern | Tragbares Closed-Loop-System zur Stressdekodierung über elektrische Signale | Elektrische Stimulation/Feedback, nicht akustisch |
| 4 | Zhao et al. (2025): Plant growth monitoring, prediction, and self-regulation utilizing MXene/CNTs/TPU flexible strain sensors integrated with DL and soft actuators | Dehnungssensor, Deep Learning, Soft Actuators, Closed-Loop | Kern | Closed-Loop-Wachstumsregelung mit flexiblem Dehnungssensor + DL | Mechanischer Sensor, nicht akustisch — zeigt existierenden PIL-Ansatz |
| 5 | Stevens et al. (2026): Green instructions: Intelligent lighting via real-time chlorophyll fluorescence feedback | Chlorophyllfluoreszenz, Echtzeit-Feedback, Beleuchtungssteuerung | Kern | Echtzeit-Pflanzen-Biofeedback via Chlorophyllfluoreszenz für optimale Beleuchtung | Optisches Feedback, nicht akustisch — belegt Biofeedback-Prinzip |
| 6 | Yuan et al. (2022): An open IoT-based framework for feedback control of photosynthetic activities | Chlorophyllfluoreszenz, PID-Regelung, IoT | Kern | PID-Closed-Loop mit Chlorophyllfluoreszenz — Photosyntheseregelung | Keine akustische Komponente |
| 7 | Sun et al. (2025): Real-time nitrogen regulation via IoT edge computing: A chlorophyll fluorescence-driven framework | Chlorophyllfluoreszenz, Edge Computing, Stickstoffregelung | Kern | Perception-Decision-Execution Closed-Loop via Chlorophyllfluoreszenz | Wiederum optisches Signal, nicht akustisch |
| 8 | Ahlman (2021): Chlorophyll fluorescence as a biological feedback signal | Chlorophyllfluoreszenz, Biofeedback, Stressdiagnose | Kern | Dissertation zu Chlorophyllfluoreszenz als biologisches Feedback-Signal | Zeigt Machbarkeit von Biofeedback, aber optisch |
| **B — Elektrophysiologische Pflanzensensorik (6 Quellen)** |
| 9 | Tran et al. (2023): Advanced assessment of nutrient deficiencies with electrophysiological signals | Elektrophysiologie, Nährstoffmangel, ML | Stütz | Direkter Beleg für kamerafreie Nährstoffdiagnose über elektrische Signale | Elektrophysiologie statt Akustik |
| 10 | Buss, Aust & Hamann (2026): When Plants Respond: Electrophysiology and ML for Green Monitoring Systems | Elektrophysiologie, AutoML, Biohybrid | Stütz | Grundlagen für biohybride Phytosensing-Systeme mit Elektrophysiologie | Fokussiert auf elektrische, nicht akustische Signale |
| 11 | Aust et al. (2025): Automated phytosensing — Ozone exposure classification based on plant electrical signals | Elektrophysiologie, Deep Learning, Ozon | Stütz | Automatisierte Stressklassifikation über pflanzliche Elektrophysiologie | Elektrische Signale, kein akustisches Pendant untersucht |
| 12 | Zhou et al. (2025): ML-assisted implantable plant electrophysiology microneedle sensor | Implantierbare Mikronadel, Elektrophysiologie, ML | Stütz | Implantierbarer Sensor für pflanzliche Elektrophysiologie mit ML | Invasiv, elektrisch — Akustik ist nicht-invasiv |
| 13 | Garlando et al. (2023): A "plant-wearable system" for health monitoring by intra- and interplant communication | Wearable, Impedanz, Stamm | Stütz | Tragbares System mit Stammimpedanz für Pflanzen-Gesundheitsmonitoring | Elektrische Impedanz, nicht Akustik |
| 14 | Chatterjee (2017): An approach towards plant electrical signal based external stimuli monitoring system | Elektrische Signale, Stimulus-Monitoring | Stütz | Ganzheitliches Monitoringsystem mit Pflanze als lebendem Multisensor | Elektrische Signalverarbeitung — Akustik als alternative Modalität |
| **C — Dehnungs-/Wachstumssensorik nicht-akustisch (6 Quellen)** |
| 15 | Tang et al. (2019): Rapid fabrication of wearable CNT/graphite strain sensor for real-time monitoring of plant growth | CNT/Graphit-Dehnungssensor, Wearable | Stütz | Kontinuierliche, quantitative Pflanzenwachstumsmessung via Dehnungssensor | Mechanischer Kontaktsensor — Akustik wäre kontaktlos |
| 16 | Wang et al. (2024): Highly stretchable, robust, and resilient wearable electronics for remote, autonomous plant growth monitoring | Dehnbare Elektronik, Autonomes Monitoring | Stütz | Autonomes Pflanzenwachstums-Monitoring mit dehnbaren Wearables | Physischer Kontakt nötig — Akustik kontaktlos möglich |
| 17 | Wang et al. (2025): Light-stable, ultrastretchable wearable strain sensors for versatile plant growth monitoring | Ultrastretchable Dehnungssensor, Multispezies | Stütz | Lichtstabile, ultradehnbare Sensoren für radiales/longitudinales Wachstum | Mehrere Pflanzenspezies, aber mechanischer Sensor |
| 18 | Lo Presti et al. (2022): Plant growth monitoring — wearable sensors based on fiber Bragg gratings | FBG, Wearable, Stammdurchmesser | Stütz | Flexible FBG-Sensoren für Stammelongation und Durchmesser | Glasfaserbasiert, physischer Kontakt |
| 19 | Lo Presti et al. (2023): A wearable flower-shaped sensor based on FBG technology for in-vivo plant growth monitoring | FBG, Blumenform, Fruchtwachstum | Stütz | Blumenförmiger FBG-Sensor für Fruchtdimensionsänderung in-vivo | Physischer Kontakt, optische Faser |
| 20 | Gleason et al. (2024): Development of an inexpensive open-source dendrometer for xylem water potential and radial stem growth | Dendrometer, Open-Source, Wasserpotential | Stütz | Kostengünstiges, hochauflösendes Dendrometer für Stammwachstum | Mechanischer Kontakt — Akustik könnte Alternativmethode sein |
| **D — Chlorophyllfluoreszenz und Photosynthese-Feedback (3 Quellen)** |
| 21 | Fu et al. (2020): Development of a minimized model structure and a feedback control framework for regulating photosynthetic activities | Chlorophyllfluoreszenz, Modellierung, Feedback | Stütz | Mathematisches Minimalmodell für PSII-Fluoreszenz zur Photosyntheseregelung | Modellbasiert, optisches Signal |
| 22 | Awon (2020): Instrumentation of a Chlorophyll Fluorescence-based Biofeedback System | Chlorophyllfluoreszenz, Biofeedback, LED-Steuerung | Stütz | Closed-Loop-Biofeedback-System auf Basis eines Low-Cost-Fluorometers | Belegt Biofeedback-Prinzip, aber optisch |
| 23 | Wang et al. (2023): A feedback control method for plant factory environment based on photosynthetic rate prediction model | Photosyntheserate, Feedback, Klimaregelung | Stütz | Feedback-Regelung via Photosyntheserate-Prädiktion aus Umweltsensorik | Indirekte Messung, keine direkte Pflanzenrückmeldung |
| **E — VOC-Sensorik und chemische Pflanzensignale (4 Quellen)** |
| 24 | Li et al. (2021): Real-time monitoring of plant stresses via chemiresistive profiling of leaf volatiles by a wearable sensor | VOC, Chemiresistiv, Wearable, Echtzeit | Stütz | Tragbarer VOC-Sensor für pflanzliche Stressdiagnose in Echtzeit | Chemisches Signal — Akustik als komplementärer Kanal |
| 25 | Ibrahim et al. (2022): Wearable plant sensor for in situ monitoring of VOC emissions from crops | VOC, Methanol, Wearable | Stütz | Wearable für Methanol-Emission als Stressindikator im Feld | VOC-basiert, nicht akustisch |
| 26 | Laothawornkitkul et al. (2008): Discrimination of plant volatile signatures by an electronic nose | E-Nose, VOC, Schädlingsdiagnose | Stütz | Erste E-Nose zur Unterscheidung von VOC-Signaturen bei Pflanzenschäden | Chemisch, nicht akustisch |
| 27 | Cui et al. (2019): Development of fast e-nose system for early-stage diagnosis of aphid-stressed tomato plants | E-Nose, Blattlaus-Stress, Frühdiagnose | Stütz | Schnelles E-Nose-System für frühe Schädlingsdiagnose bei Tomaten | Chemisches Profiling — Akustik unerforscht als Alternative |
| **F — Sap Flow / Wasserhaushalt-Sensorik (3 Quellen)** |
| 28 | Baek et al. (2018): Monitoring of water transportation in plant stem with microneedle sap flow sensor | Mikronadel, Sap Flow, MEMS | Stütz | MEMS-Mikronadel-Sap-Flow-Sensor für Wassertransport-Monitoring | Invasiv (Mikronadel) — Akustik nicht-invasiv |
| 29 | Zimmermann et al. (2013): A non-invasive plant-based probe for continuous monitoring of water stress in real time | Magnetische Blattklemme, Turgor, Wasserstress | Stütz | Nicht-invasive Blattklemmensonde für kontinuierliches Wasserstress-Monitoring | Mechanisch/magnetisch, nicht akustisch |
| 30 | Asgharinia et al. (2022): Towards continuous stem water content and sap flux density monitoring — IoT-based solution | IoT, Sap Flux, Kapazitätssonde | Stütz | IoT-basierte kontinuierliche Sap-Flow- und Stammwasserüberwachung | IoT-Architektur übertragbar auf akustisches System |
| **G — Akustische Emission von Pflanzen — Diagnose, NICHT Closed-Loop (14 Quellen) ← DIE FORSCHUNGSLÜCKE** |
| 31 | Khait et al. (2023): Sounds emitted by plants under stress are airborne and informative | Luftgetragener Ultraschall, Stress, ML-Klassifikation | Kern | **Hochrangige Publikation (Cell):** Pflanzen emittieren hörbare Ultraschall-Signale bei Stress | Nur Diagnose, KEIN Closed-Loop — beweist akustisches Signal existiert |
| 32 | De Roo et al. (2016): Acoustic emissions to measure drought-induced cavitation in plants | Kavitation, Trockenstress, Ultraschall | Kern | Umfassendes Review der AE-Methode zur Kavitationsdetektion bei Trockenstress | Nur passives Monitoring, kein Regelkreis |
| 33 | Zweifel & Zeugin (2008): Ultrasonic acoustic emissions in drought-stressed trees — more than signals from cavitation? | UAE, Kambiumwachstum, Trocknung | Kern | Zeigt, dass UAE nicht nur Kavitation, sondern auch Kambiumwachstum anzeigen kann | **Wachstumsrelevanz der Akustik belegt** — aber kein PIL |
| 34 | Oletic et al. (2020): Time-frequency features of grapevine's xylem acoustic emissions for detection of drought stress | Zeit-Frequenz-Merkmale, Weinrebe, Trockenstress | Kern | Automatisierte Merkmalsextraktion für akustische Trockenstressdetektion | Nur Merkmalsextraktion, keine Regelung |
| 35 | Saha & Rastogi (2026): Plant acoustic emission as early stress signals — Towards remote integrated monitoring for sustainable agriculture | Review, Akustik, Frühwarnsystem, Präzisionslandwirtschaft | Kern | Aktuelles Review: Akustik als Frühwarnsignal für nachhaltige Landwirtschaft | Schlägt Integration vor, aber KEIN Closed-Loop-Konzept |
| 36 | Klaminder et al. (2025): Ultrasonic acoustic emissions as indicators of tree drought stress in outdoor forest settings | UAE, Freiland, Wald | Stütz | Nachweis der UAE-Messbarkeit unter Freilandbedingungen | Machbarkeit im Feld bewiesen — Übertragung auf CEA/PIL fehlt |
| 37 | Bonisoli et al. (2025): Outdoor detection of plant ultrasonic emissions using a contactless microphone | Kontaktloses Mikrofon, Freiland, Bohne/Tomate | Stütz | Kontaktlose Ultraschall-Aufnahme von gestressten Pflanzen im Freiland | Kontaktlose Methode — entscheidend für nicht-invasive PIL-Integration |
| 38 | Király et al. (2025): Ultrasound in plant life and its application perspectives in horticulture and agriculture | Review, Ultraschall, Gartenbau | Stütz | Überblick über Ultraschall-Detektion und -Anwendung bei Pflanzen | Erwähnt Anwendungen, aber nicht Closed-Loop |
| 39 | Qiu et al. (2002): Acoustic emissions in tomato plants under water stress conditions | AE, Tomate, Wasserstress, Transpiration | Stütz | Frühe AE-Studie: AE-Rate korreliert mit Transpiration und Kavitation | Klassische AE-Studie — kein Regelkreis |
| 40 | Sriwongras et al. (2016): The Measurement of Acoustic Emission Signals from Stem of Maize Under Controlled Environment | AE, Mais, Kontrollierte Umgebung | Stütz | Untersuchung, welche Umweltparameter AE-Signale im Maisstamm beeinflussen | **Ziel: Closed-Loop-Überwachung** — aber nur Datenerhebung, keine Regelung |
| 41 | Shimamoto & Suzuki (2022): Frequency Characteristics of AE Caused by Bubble Motion in Plant's Vessels | AE, Blasendynamik, Xylem | Stütz | Frequenzanalyse der AE aus Blasenbewegung im Xylem | Physikalische Grundlagen der AE-Entstehung |
| 42 | Kageyama et al. (2009): Estimation for embolism risk of tomato using acoustic emission response to increased drought stress | AE, Embolie-Risiko, Tomate | Stütz | Nutzt AE zur Risikoabschätzung von Xylem-Embolien bei Trockenstress | Risikoabschätzung, keine Regelung |
| 43 | Vergeynst et al. (2016): Clustering reveals cavitation-related acoustic emission signals from dehydrating branches | Clustering, AE, Kavitation, Äste | Stütz | Clustering-Algorithmen zur Trennung kavitationsbezogener AE von anderen Quellen | Signalverarbeitungsmethode für AE |
| 44 | Dostál et al. (2016): Detection of acoustic emission characteristics of plant according to water stress condition | AE, Wasserstress, Transpiration | Stütz | AE-Parameter korrelieren mit Transpirationsrate und Kavitation | Experimentelle AE-Charakterisierung |
| **G2 — Akustik + automatisierte Aktorik (existierende Ansätze — zeigen Begrenzung der Lücke) (5 Quellen)** |
| 45 | Simbeye et al. (2023): Plant water stress monitoring and control system | AE, virtuelles Instrument, Bewässerungssteuerung | Stütz | Vollständiges AE→Monitoring→Bewässerungssystem auf LabVIEW-Basis | Feldgewächshaus, kein CEA; keine ML-Klassifikation; kein PIL-Paradigma; keine Kontrollgruppe |
| 46 | SJ, Haresh & DKNV (2026): Acoustic-based Stress Monitoring and Automated Water Delivery System | Mikrofon, CNN+Bi-LSTM, Arduino, Bewässerung | Stütz | Akustische Stressdetektion → automatisierte Bewässerung via Arduino | Unteres Journal (GIJET); Freiland; keine kontrollierte Studie; binäre Klassifikation |
| 47 | Devi et al. (2025): Smart Irrigation System by Detecting Plant Squeals Using IoT | Audio, IoT, Bewässerung | Stütz | IoT-basierte Bewässerung via Pflanzenschall | IEEE-Konferenz; Konzeptcharakter; keine wissenschaftliche Evaluation |
| 48 | You et al. (2011): Precision Spraying System of Crops Disease Stress Based on Acoustic Emission | AE, Schädlingsstress, Sprühsystem | Stütz | Nutzt AE für automatisiertes Sprühen bei Schädlingsbefall | Schädlings-/Krankheitsstress, nicht Wachstums-/Wasserstress; kein PIL |
| 49 | Oletić, Rosner & Bilas (2023): Field-experiences of tracking plant's xylem embolism formation with embedded acoustic emission sensors | Embedded AE, Xylem-Embolie, Precision Irrigation | Stütz | Embedded-AE-Sensor zur Feldvalidierung für Präzisionsbewässerung | Sensorseite; kein geschlossener Regelkreis im Paper beschrieben |
| **H — Fortschrittliche Sensormethoden (EIT, THz, Event-Kamera) (5 Quellen)** |
| 50 | Weigand & Kemna (2017): Multi-frequency electrical impedance tomography as a non-invasive tool to characterize and monitor crop root systems | EIT, Multifrequenz, Wurzelsystem | Stütz | Nicht-invasive EIT zur funktionalen Bildgebung von Wurzelsystemen | Wurzelmonitoring — Akustik könnte oberirdisch komplementär sein |
| 51 | Wang et al. (2024): Non-invasive early monitoring plant health using terahertz spectroscopy | THz-ATR, Blattkrankheit, Frühdiagnose | Stütz | THz-Spektroskopie zur nicht-invasiven frühen Krankheitserkennung | Spektroskopisch — Akustik als alternative Modalität |
| 52 | Santesteban et al. (2015): Terahertz time domain spectroscopy allows contactless monitoring of grapevine water status | THz-TDS, Weinrebe, Wasserstatus | Stütz | Kontaktloses THz-Monitoring des Wasserstatus von Weinreben | Kontaktlos wie Akustik, aber elektromagnetisch |
| 53 | El Arja (2022): Neuromorphic perception for greenhouse technology using event-based sensors | Event-Kamera, Neuromorph, Gewächshaus | Stütz | Event-basierte Algorithmen für Gewächshaus-Phänotypisierung | Event-basiertes Sehen — Akustik als event-basierte Alternative |
| 54 | Corona-Lopez et al. (2019): Electrical impedance tomography as a tool for phenotyping plant roots | EIT, Wurzelphänotypisierung, Nicht-invasiv | Stütz | EIT zur kontinuierlichen, nicht-invasiven Wurzelentwicklungs-Überwachung | Nicht-invasiv, aber Wurzelfokus |
| **I — Regelungstheorie und Digital Twin (3 Quellen)** |
| 55 | Ariesen-Verschuur et al. (2022): Digital Twins in greenhouse horticulture — A review | Digital Twin, Gewächshaus, Monitoring | Stütz | Review zu Digital-Twin-Anwendungen im Gewächshausgartenbau | Systemarchitektur — akustische Daten als neuer Input-Kanal denkbar |
| 56 | Deng et al. (2018): Robust closed-loop control of vegetable production in plant factory | System Dynamics, Lyapunov, Closed-Loop | Stütz | Robuste Closed-Loop-Regelung für Salatproduktion in Plant Factory | Regelungstheoretischer Rahmen — Akustik als Feedback-Signal einsetzbar |
| 57 | Morcego et al. (2023): Reinforcement learning versus model predictive control on greenhouse climate control | RL, MPC, Klimaregelung, Energie | Stütz | Vergleich RL vs. MPC für Gewächshausklima — Energie- und Ertragsoptimierung | Regelungsmethoden auf akustisches PIL übertragbar |
| 58 | Xiao et al. (2026): Grower-in-the-Loop Interactive Reinforcement Learning for Greenhouse Climate Control | Human-in-the-Loop, Interaktives RL, Gewächshaus | Stütz | Interaktives RL mit menschlichem Feedback für Gewächshausregelung — direkte Analogie zu PIL | Zeigt, dass unvollständiges Feedback (wie akustische Signale) in RL integrierbar ist |
| 59 | Maree et al. (2025): Autonomous Greenhouse Cultivation of Dwarf Tomato — Performance Evaluation of Intelligent Algorithms for Multiple-Sensor Feedback | Autonomes Gewächshaus, Multi-Sensor-Feedback, Zwergtomate | Stütz | Autonome Kultivierung mit Multi-Sensor-Feedback und intelligenten Algorithmen | Belegt Praxisrelevanz von Multi-Sensor-PIL in CEA — Akustik fehlt als Modalität |
| 60 | Bwambale et al. (2025): A Review of Model Predictive Control in Precision Agriculture | MPC, Präzisionslandwirtschaft, Review | Stütz | Umfassender MPC-Review für Präzisionslandwirtschaft | Regelungstheoretische Grundlage — MPC mit akustischem Feedback kombinierbar |
| 61 | Ojo & Zahid (2022): Deep Learning in Controlled Environment Agriculture — A Review | DL, CEA, Gewächshaus, Plant Factory | Stütz | Review zu DL-Anwendungen in CEA: Monitoring, Stress, Mikroklima, Wachstum | Keine akustische Modalität im Review erwähnt — bestätigt Lücke |
| 62 | Schaal (2026): Verstärkerschleife im Wurzelwerk | Wurzel-Biofeedback, Regelkreis, Agrar | Stütz | Deutschsprachiger Beitrag zu Biofeedback-Schleifen im Wurzelsystem — konzeptionelle Nähe zu PIL | Zeigt wachsendes Interesse an pflanzlicher Rückkopplung — aber kein akustisches PIL beschrieben |

---

## Gegenfolien — Bildbasierte Verfahren (explizit ausgegrenzt)

| Nr. | Quelle | Warum Gegenfolie? |
|---:|---|---|
| G1 | Tong et al. (2022): Deep Learning for Image-Based Plant Growth Monitoring — A Review | Umfassendes Review bildbasierter DL-Methoden |
| G2 | Islam & Reza (2024): Machine Vision and AI for Plant Growth Stress Detection and Monitoring | Review zu Machine Vision und KI für Stressdetektion |
| G3 | Bernotas et al. (2019): A Photometric Stereo-Based 3D Imaging System Using CV and DL for Tracking Plant Growth | 3D-Bildgebung, photometrisches Stereo — rein bildbasiert |
| G4 | Yasrab et al. (2021): Predicting Plant Growth from Time-Series Data Using Deep Learning | Pixel-Level-Prädiktion aus Zeitreihenbildern |
| G5 | Chen & Yin (2024): Camera-Based Plant Growth Monitoring for Automated Plant Cultivation with CEA | Explizit kamera-basiertes Wachstumsmonitoring in CEA |
| G6 | Pound et al. (2017): Deep Machine Learning Provides State-of-the-Art Performance in Image-Based Plant Phenotyping | State-of-the-Art bildbasierte Phänotypisierung |
| G7 | Jiang & Li (2020): Convolutional Neural Networks for Image-Based High-Throughput Plant Phenotyping — A Review | CNN-Review für bildbasierte Hochdurchsatz-Phänotypisierung |
| G8 | Kim et al. (2022): A Novel Shape-Based Plant Growth Prediction Algorithm Using DL and Spatial Transformation | Formbasierte Wachstumsprädiktion aus Einzelbildern |
| G9 | Nagano et al. (2019): Leaf-Movement-Based Growth Prediction Model Using Optical Flow Analysis and ML | Blattbewegungsanalyse via Optical Flow aus Kamerabildern |
| G10 | Tsaftaris et al. (2016): Machine Learning for Plant Phenotyping Needs Image Processing | Argumentiert für Bildverarbeitung als Voraussetzung für ML-Phenotypisierung |
| G11 | Murphy et al. (2024): Deep Learning in Image-Based Plant Phenotyping | Annual Review — umfassender Überblick zu DL in bildbasierter Phänotypisierung |

---

## Zotero-Integration

Die folgenden Quellen stammen aus der bestehenden Projektbibliothek `zotero/literatur.bib` (Stand Mai 2026) und wurden in diese Abgrenzungstabelle übernommen:

| Tabellen-Nr. | Zotero-Key | Quelle |
|---:|---|---|
| 1 | `kernbach_biofeedback-based_2024` | Kernbach (2024) |
| 3 | — | Dai et al. (2026) — neu via PRISMA |
| 9 | `tran2023` / `tran_advanced_2023` | Tran et al. (2023) |
| 12 | `ang_decoding_2024` | Ang et al. (2024) |
| 13 | `teixeira_sustainable_2025` | Teixeira et al. (2025) |
| 14 | `yan_flexible_2024` | Yan et al. (2024) |
| 15 | `lee_emerging_2021` | Lee et al. (2021) |
| 16 | `kuruppuarachchi_advancements_2025` | Kuruppuarachchi et al. (2025) |
| 17 | `lu_multimodal_2020` | Lu et al. (2020) |
| 18 | `xu_plant-friendly_2024` | Xu et al. (2024) |
| 19 | `li_real-time_2021` | Li et al. (2021) |
| 20 | `li_non-invasive_2019` | Li et al. (2019) |
| 21 | `langstroff_opportunities_2022` | Langstroff et al. (2022) |
| 22 | `massonnet_probing_2010` | Massonnet et al. (2010) |
| 24 | `lew_species-independent_2020` | Lew et al. (2020) |
| 38 | `elvanidi_machine_2023` | Elvanidi & Katsoulas (2023) |
| 43 | `mahmood_data-driven_2023` | Mahmood et al. (2023) |
| 46 | — | Su (2018) — aus `zotero/nicht_maintained_literatur.bib` |
| 48 | `van_eeuwijk_modelling_2019` | van Eeuwijk et al. (2019) |
| 49 | `stock_plant_2024` | Stock et al. (2024) |
| 55 | `ariesen-verschuur_digital_2022` | Ariesen-Verschuur et al. (2022) |
| 57 | `morcego_reinforcement_2023` | Morcego et al. (2023) |
| 58 | `xiao_grower-in-the-loop_2026` | Xiao et al. (2026) |
| 59 | `maree_autonomous_2025` | Maree et al. (2025) |
| 60 | `bwambale_review_2025` | Bwambale et al. (2025) |
| 61 | `ojo_deep_2022` | Ojo & Zahid (2022) |
| 62 | — | Schaal (2026) — aus `references.tex` |
| G5 | `chen_camera-based_2024` | Chen & Yin (2024) |
| G11 | `murphy_deep_2024` | Murphy et al. (2024) |

**Nicht als PDF abgelegte Quellen** (entsprechend `Quellen/Quellen_Status.md`) bleiben mit Vermerk „kein frei abrufbarer Volltext" in der Tabelle dokumentiert, werden aber nicht künstlich ersetzt: Stahl et al. (2020), Massonnet et al. (2010), van Eeuwijk et al. (2019), Mahmood et al. (2023).

---

## Ergebnis der Abgrenzung

### PRISMA-Systematik: Suchstrategie

Zur formalen Prüfung der Forschungslücke wurde eine systematische Literaturrecherche nach PRISMA-Richtlinien durchgeführt.

**Datenbanken:** Google Scholar (primär), Semantic Scholar, OpenAlex, PubMed (Kreuzvalidierung)  
**Suchzeitraum:** bis Mai 2026  

Die 68 Quellen der Abgrenzungstabelle wurden über alle 4 Datenbanken sowie die bestehende Projektbibliothek (Zotero, `literatur.bib`) zusammengetragen. Die Schnittmenge *Pflanzenakustik × Closed-Loop-Regelung* ist eine hochspezifische Nische — in keiner der 4 Datenbanken findet sich eine Publikation, die Akustik + Regelkreis + PIL-Paradigma + Indoor-CEA vereint.

### Herleitung der Bewertungskriterien

Die vier binären Bewertungskriterien wurden nicht ad hoc gewählt, sondern aus der Literatur abgeleitet:

| Kriterium | Herleitung | Quelle |
|---|---|---|
| **Akustik?** | Pflanzliche UAE sind als Messsignal etabliert (Khait 2023, Cell; De Roo 2016). Das Kriterium prüft, ob eine Quelle dieses spezifische Signal nutzt — nicht ob sie *irgendein* Pflanzensignal verwendet. | Khait et al. (2023); De Roo et al. (2016) |
| **Closed-Loop?** | Regelungstechnisches Standardkriterium: Sensor → Verarbeitung → Aktor → Strecke → Sensor. Angewendet auf CEA-Regelsysteme durch Cohen et al. (2021) und Deng et al. (2018). | Cohen et al. (2021); Deng et al. (2018) |
| **PIL-Paradigma?** | „Plant-in-the-Loop" ist definiert als Regelkreis, in dem die Pflanze selbst die Signalquelle ist — nicht nur die Regelstrecke (Kernbach 2024). Abgrenzung zu Smart Irrigation: dort ist die Pflanze passives Ziel, nicht aktiver Sensor. | Kernbach (2024); Damian et al. (2014) |
| **Indoor-CEA?** | CEA definiert als geschlossene Umgebung mit kontrollierten Umweltparametern (Cohen et al. 2021). Für Akustik essentiell: Wind und variabler Hintergrundlärm würden UAE-Messungen im Freiland unzuverlässig machen (Bonisoli et al. 2025). | Cohen et al. (2021); Bonisoli et al. (2025) |

Diese Herleitung macht die Kriterien falsifizierbar: Ein Reviewer kann anhand derselben Literatur prüfen, ob die Kriterien trennscharf und begründet sind — sie sind nicht beliebig auf die Hypothese zugeschnitten.

### Die Forschungslücke (PRISMA-validiert)

Die PRISMA-Recherche bestätigt eine **signifikante, aber nicht vollständig leere** Schnittmenge. Fünf Arbeiten (Quellen 45–49) koppeln Pflanzenakustik mit automatisierter Aktorik:

| Quelle | Akustik→Aktorik | Defizit gegenüber dieser Arbeit |
|---|---|---|---|
| Simbeye et al. (2023) | AE-Sensor → Bewässerung | AE = piezoelektrischer Kontaktsensor (nicht luftgetragen); Feldgewächshaus (nicht CEA); Schwellwert (nicht ML); kein PIL-Paradigma; keine Kontrollgruppe. Simbeye misst Körperschall am Stamm — unsere Arbeit nutzt luftgetragenen Ultraschall (MEMS-Mikrofon, kontaktlos). |
| SJ, Haresh & DKNV (2026) | Mikrofon → CNN → Arduino-Pumpe | Unteres Journal; Freiland; binäre Klassifikation (gesund/krank); keine wissenschaftliche Vergleichsstudie |
| Devi et al. (2025) | Audio → IoT → Bewässerung | IEEE-Konferenz; Konzeptcharakter; keine statistische Evaluation |
| You et al. (2011) | AE → Sprühsystem | Schädlingsstress (nicht Wachstum/Wasser); anderes Anwendungsfeld |
| Oletić et al. (2023) | Embedded AE → Precision Irrigation (geplant) | Nur Sensorvalidierung; geschlossener Regelkreis im Paper nicht implementiert |

**Kernergebnis der Abgrenzung:** Keine der existierenden Arbeiten vereint folgende Merkmale:

1. **Plant-in-the-Loop-Paradigma** — alle existierenden Arbeiten framen sich als „Smart Irrigation" oder „Precision Agriculture", nicht als PIL mit der Pflanze als aktivem Regelkreis-Element
2. **Indoor-CEA** — alle fünf Arbeiten arbeiten im Freiland oder Feldgewächshaus mit unkontrollierten akustischen Randbedingungen
3. **Transfer-Learning von Keyword-Spotting** — keine nutzt angepasste KW-Spotting-Architekturen für die akustische Klassifikation; die ML-Ansätze sind einfache CNNs ohne Domänenadaption
4. **Kontrolliertes Experiment** — keine der Arbeiten vergleicht akustisch gesteuerte Bewässerung systematisch gegen eine getaktete Baseline mit Positiv-/Negativkontrolle
5. **Krautige Hydrokultur-Pflanzen** — Oletić et al. arbeiten mit Weinreben (Holzpflanze); Simbeye mit Feldkulturen; keine Arbeit untersucht krautige CEA-Pflanzen
6. **Physikalische Grenzdiskussion** — keine Arbeit thematisiert explizit die fundamentalen Unterschiede zwischen akustischen und elektromagnetischen Wellen als wissenschaftliche Randbedingung

### Konkrete wissenschaftliche Hypothese (PRISMA-geschärft)

> **Akustische Emissionen von krautigen Pflanzen (Ultraschall 20–100 kHz) können unter Indoor-CEA-Bedingungen mittels kostengünstiger MEMS-Mikrofone kontaktlos erfasst und durch Transfer-Learning von Keyword-Spotting-Architekturen klassifiziert werden, um als Echtzeit-Feedback-Signal in einem geschlossenen Plant-in-the-Loop-Regelkreis die Bewässerung zu steuern — ein Ansatz, der in existierenden Arbeiten (Simbeye 2023; SJ 2026; Oletić 2023) weder unter CEA-Bedingungen, noch mit Transfer-Learning, noch mit kontrolliertem Experimentaldesign, noch im PIL-Paradigma untersucht wurde.**

**Geltungsbereichseinschränkung:** Die Hypothese beansprucht ausdrücklich keine Gültigkeit für Freilandbedingungen. Sie bezieht sich auf Indoor-CEA-Szenarien mit kontrollierbaren akustischen Randbedingungen (kein Wind, definierte Hintergrundgeräusche, Nahdistanz < 30 cm).

### Warum diese Lücke relevant ist

1. **Kontaktlos & nicht-invasiv:** Im Gegensatz zu Dehnungssensoren, FBG, Dendrometern und Wearables benötigt Akustik keinen physischen Kontakt zur Pflanze (vgl. Bonisoli et al. 2025)
2. **Echtzeitfähig:** Akustische Signale liegen im Millisekunden-Bereich — schneller als visuelle Symptome (Stunden/Tage) oder chemische Marker
3. **Stress-Frühindikator:** Akustische Emission tritt bei Kavitation und Trockenstress VOR sichtbaren Symptomen auf (Khait et al. 2023; De Roo et al. 2016)
4. **Wachstumskorreliert:** UAE können auch Kambiumwachstumsprozesse anzeigen (Zweifel & Zeugin 2008)
5. **Kostengünstig:** MEMS-Ultraschall-Mikrofone sind kommerziell für wenige Euro verfügbar; ein schalltoter Raum ist durch spektrale Trennung (Hochpass ≥ 20 kHz) nicht erforderlich
6. **PRISMA-geprüfte Lücke:** 5 Arbeiten existieren zur Akustik→Aktorik-Kopplung (Simbeye 2023; SJ 2026; Devi 2025; You 2011; Oletić 2023), aber keine vereint Indoor-CEA, Transfer-Learning, kontrolliertes Experiment und PIL-Paradigma (vgl. PRISMA-Report oben)
7. **Physikalische Grenzen offen thematisiert:** Die Arbeit verschweigt nicht, dass akustische Wellen — anders als elektromagnetische — durch Interferenz lokal auslöschen können und einer starken Luftdämpfung unterliegen. Diese Einschränkung wird als definierte Systemgrenze (Indoor-CEA, Nahdistanz) behandelt, nicht als zu lösendes Problem

### Nächste Schritte

- ✅ PRISMA-Recherche abgeschlossen (15 Suchstrings, Mai 2026)
- ✅ Zotero bereinigt: 87 Einträge, 0 Duplikate, auf akustisches PIL abgestimmt
- ✅ Abgrenzungstabelle als Professoren-xlsx: `abgrenzungstabelle.xlsx` (Blatt „Legende" + „Abgrenzung" mit 67 Quellen)
- ✅ Paper-Template in `paper/`: Build läuft, PDF mit Abkürzungsverzeichnis
- ✅ Akustische Kernquellen (De Roo 2016, Bonisoli 2025) als PDF in `Quellen/` ergänzt
- 🔲 Khait et al. (2023, Cell) als PDF beschaffen (paywalled)
- 🔲 Experiment-Design detaillieren: Sensorauswahl, Messprotokoll, statistische Power-Analyse
- 🔲 MicroWakeWord-Transfer vorbereiten: Trainingsdaten-Erhebung (3 Klassen à ~2000 Clips)
- 🔲 Hauptpaper ausformulieren (derzeit Outline)

---

## Forschungsdesign: Akustisches Plant-in-the-Loop

### 1. Wissenschaftliche Fragestellungen

Die PRISMA-validierte Forschungslücke (vgl. Abgrenzungstabelle) führt zu drei hierarchischen Forschungsfragen:

| Ebene | Frage | Typ |
|---|---|---|
| **FF1** | Korreliert die Rate luftgetragener Ultraschall-Emissionen (20–100 kHz) einer Pflanze reproduzierbar mit ihrem Wasserstress-Zustand unter kontrollierten CEA-Bedingungen? | Deskriptiv / korrelativ |
| **FF2** | Kann ein auf Mel-Spektrogrammen trainierter ML-Klassifikator Pflanzensprache akustisch in die Zustände *normal*, *trockengestresst* und *Wachstumsphase* trennen? | Klassifikatorisch |
| **FF3** | Lässt sich die Klassifikator-Entscheidung als Feedback-Signal in einem geschlossenen Regelkreis nutzen, sodass die Pflanze — vermittelt über ihre akustische Emission — ihre eigene Bewässerung steuert? | Kausal / experimentell |

### 2. Experimentelles Design

#### 2.1 Unabhängige Variable

- **Bewässerungszustand** (drei Stufen, within-subjects über 21 Tage):
  - *Sättigung (Tag 1–7):* Substrat-Wassergehalt > 80 % Feldkapazität
  - *Progressiver Trockenstress (Tag 8–14):* Keine Bewässerung, Substrat trocknet aus
  - *Gesteuerte Intervention (Tag 15–21):* Bewässerung nach akustischem Feedback (FF3)

#### 2.2 Abhängige Variablen

- **Akustisch:** UAE-Ereignisrate (counts/min), spektrale Schwerpunktfrequenz, MFCC-Clusterdistanz zu Baseline
- **Physiologisch:** Stomatale Leitfähigkeit (Porometer), Chlorophyllfluoreszenz (Fv/Fm), Blattwasserpotential (Scholander-Kammer)
- **Morphologisch:** Blattfläche (planimetrisch, Tag 1/7/14/21), Frisch-/Trockengewicht (Tag 21)

#### 2.3 Kontrollen und Störgrößen

- **Positivkontrolle:** Eine parallele Pflanzengruppe mit festem Bewässerungsintervall (ohne akustische Regelung)
- **Negativkontrolle:** Dauerhafte Überwässerung (Substrat stets > 95 % Feldkapazität)
- **Störgrößen-Erfassung:** Temperatur, Luftfeuchte, CO₂, Lichtintensität (PAR-Sensor) werden kontinuierlich mitgeloggt und als Kovariaten in das statistische Modell aufgenommen
- **Replikation:** n = 12 Pflanzen pro Bedingung (Power-Analyse: α = 0.05, β = 0.2, d ≥ 0.8)

#### 2.4 Messaufbau (Prinzipskizze)

```
┌─────────────┐     Ultraschall (20–100 kHz)     ┌──────────────────┐
│  Pflanze    │──────────────────────────────────▶│  Breitband-      │
│  (UAE-Quelle)│                                   │  Mikrofon          │
│             │                                    │  (kontaktlos)     │
│             │◀──────────────────────────────────│                    │
│             │     Bewässerung / Nährlösung       └────────┬───────────┘
└─────────────┘                                            │
       ▲                                                    │ ADC ≥ 200 kHz
       │                                                    ▼
       │              ┌──────────────────────────────────────────┐
       │              │  Signalverarbeitung                      │
       │              │  - Hochpass ≥ 20 kHz                    │
       │              │  - Mel-Spektrogramm (40 Bins, 49 Frames)│
       │              │  - ML-Inferenz (3-Klassen)              │
       │              │  - Regelentscheidung                    │
       │              └──────────────────────────────────────────┘
       │
       └──────────── Umweltkontrolle (T, rH, CO₂, PAR) ── Referenzmessung
```

#### 2.5 Physikalische Randbedingungen und Geltungsbereich

**Geltungsbereich: Indoor-CEA, kein Freiland.** Die Arbeit beschränkt sich bewusst auf kontrollierte Innenraumbedingungen (Hydrokultur, Plant Factory, Gewächshaus ohne Windeinfluss). Freilandtauglichkeit wird weder angestrebt noch behauptet. Wind induziert breitbandige niederfrequente Störsignale und mikrofoneigene Verwirbelungsartefakte, die eine zuverlässige UAE-Detektion ohne aufwändige Richtmikrofon-Arrays erschweren (vgl. Bonisoli et al. 2025). Unter Indoor-Bedingungen ist der Windeinfluss dagegen kontrollierbar vernachlässigbar.

**Physik akustischer Wellen vs. elektromagnetischer Wellen.** Im Gegensatz zu elektromagnetischen Signalen (z. B. Chlorophyllfluoreszenz, Thermographie, THz) unterliegen akustische Wellen in Luft fundamentalen physikalischen Einschränkungen, die nicht technisch überwunden werden können:

| Eigenschaft | Akustik (20–100 kHz in Luft) | Elektromagnetisch (optisch/THz) |
|---|---|---|
| Dämpfung | ~1–5 dB/m bei 80 kHz, 20 °C, 50 % rF (ISO 9613) | Vernachlässigbar auf Meter-Skala |
| Interferenz | Konstruktive/destruktive Überlagerung bei Mehrwegeausbreitung — Signal kann lokal vollständig auslöschen | Superposition ohne Auslöschung; Gesamtenergie bleibt erhalten |
| Reichweite | Begrenzt (< 2 m für Nutzsignal > Grundrauschen bei 80 kHz) | Praktisch unbegrenzt im CEA-Maßstab |
| Störquellen | Lüfter, Pumpen, LED-Treiber (breitbandig bis ~15 kHz, Oberschwingungen möglich) | Umgebungslicht (durch Modulation/Chopping diskriminierbar) |
| Richtwirkung | Schwach bei MEMS-Mikrofonen (omnidirektional); Richtmikrofone möglich aber teuer | Optische Linsen bündeln; THz-Antennen richten |

**Konsequenz für den Messaufbau:** Die akustische Detektion ist physikalisch auf kurze Distanzen (< 30 cm) und ruhige Umgebungen angewiesen. Dies ist im Indoor-CEA-Szenario jedoch keine Einschränkung, sondern eine realistische Randbedingung: In einer Plant Factory oder einem Hydrokultur-Rack befindet sich der Sensor ohnehin in unmittelbarer Pflanzennähe.

**Kein schalltoter Raum erforderlich.** Die spektrale Trennung zwischen Störquellen und Nutzsignal macht einen schalltoten Raum entbehrlich:
- Pumpen, Lüfter und LED-Treiber emittieren überwiegend im hörbaren Bereich (< 16 kHz) mit abklingenden Oberschwingungen bis ~40 kHz
- Kavitations-UAE liegen typisch bei 50–150 kHz (De Roo et al. 2016), mit Schwerpunkt 60–80 kHz
- Ein Hochpass-Filter (≥ 20 kHz) und eine Mel-Filterbank oberhalb 20 kHz trennen Stör- und Nutzsignal spektral — nicht räumlich
- MEMS-Mikrofone mit ausreichender Sensitivität im Ultraschallbereich (z. B. SPU0410LR5H: −38 dBV bei 1 kHz, flach bis 80 kHz) sind kommerziell für < 5 € verfügbar

**Detektionsgrenze: Krautige Pflanzen vs. Gehölze.** Die etablierte AE-Literatur verwendet überwiegend verholzte Pflanzen (Bäume, Weinreben) mit Xylem-Gefäßen im Millimeter-Durchmesser, deren Kavitation energiereiche Schallimpulse erzeugt. Für krautige Hydrokultur-Pflanzen (Salat, Basilikum, Tomate) mit Xylem-Gefäßen im Mikrometer-Bereich existieren zwei ermutigende Datenpunkte:
- Khait et al. (2023): Tomate und Tabak (beide krautig) → luftgetragene UAE auf 10 cm Distanz klassifizierbar
- Qiu et al. (2002): Tomate → AE detektierbar unter kontrolliertem Wasserstress

Die **Frage der minimalen Pflanzengröße für zuverlässige UAE-Detektion** wird in dieser Arbeit nicht als Ausschlusskriterium, sondern als **Teil der Forschungsfrage** behandelt. Der systematische Vergleich zwischen verschiedenen krautigen Arten mit abgestufter Xylem-Dimension (z. B. Basilikum < Salat < Tomate) liefert selbst dann eine wissenschaftliche Aussage, wenn die UAE-Rate unter die Detektionsschwelle fällt — nämlich die Bestimmung der Anwendbarkeitsgrenze akustischen PILs.

### 3. Signalverarbeitung und Merkmalsextraktion

Die akustische Signalkette folgt etablierten Verfahren aus Bioakustik (Khait et al. 2023) und Keyword-Spotting, adaptiert auf den Ultraschallbereich:

**Frequenzverschiebung (Domain Adaptation):** Sprache (0–8 kHz) → Pflanzen-Ultraschall (20–80 kHz). Die Mel-Filterbank wird linear in den Zielbereich transformiert; die CNN-Architektur bleibt topologisch identisch, lernt jedoch neue Filtergewichte.

```
Rohsignal (≥ 200 kHz, 16 bit)
    │
    ▼
Hochpass 20 kHz (entfernt Sprach-, Wind- und Maschinenartefakte)
    │
    ▼
Segmentierung: 1.2 s Fenster, 50 % Überlappung
    │
    ▼
Mel-Spektrogramm: FFT=1024, Hop=512, 40 Bins auf 20–80 kHz
    │
    ▼
Klassifikation: → Klasse 0 (normal) / 1 (Trockenstress) / 2 (Wachstumsaktivität)
    │
    ▼
Regelentscheidung (vgl. Abschnitt 5)
```

### 4. ML-Modell: Transfer von Keyword-Spotting auf Pflanzenakustik

#### 4.1 Wissenschaftliche Motivation des Transfers

Keyword-Spotting-Modelle (z. B. MicroWakeWord) sind darauf optimiert, kurze, charakteristische Schallereignisse in Audiodaten zu erkennen — exakt die gleiche Problemstruktur wie bei der Detektion von Kavitations-Clicks und Wachstums-Ultraschall-Emissionen. Die Übertragbarkeit wird empirisch geprüft (Fine-Tuning vs. Training from scratch).

#### 4.2 Modelltopologie

Eine schlanke CNN-Architektur mit Depthwise Separable Convolutions (Howard et al. 2017), quantisiert auf int8, ermöglicht Inferenz auf ressourcenlimitierten Mikrocontrollern. Die Topologie wird nicht als technisches Artefakt, sondern als notwendige Bedingung für dezentrale, echtzeitfähige Closed-Loop-Regelung in CEA-Umgebungen betrachtet.

#### 4.3 Trainingsdaten

Die Modellpflanze (z. B. *Solanum lycopersicum* oder *Lactuca sativa*) wird über 21 Tage unter kontrollierten Bedingungen aufgezeichnet:

| Klasse | Bedingung | Erwartetes akustisches Muster | Referenz |
|---|---|---|---|
| 0 (normal) | Optimale Bewässerung, EC 1.8, pH 5.8 | ≤ 2 UAE-Ereignisse/min | Khait et al. 2023: unstressed baseline |
| 1 (Trockenstress) | Keine Bewässerung, fortschreitende Austrocknung | Ansteigende UAE-Rate, hochfrequent (60–80 kHz) | De Roo et al. 2016: cavitation clicks |
| 2 (Wachstum) | Dunkelphase bei Optimalbedingungen | Niederfrequente UAE (20–40 kHz), korreliert mit Kambiumaktivität | Zweifel & Zeugin 2008: growth-related AE |

**Label-Validierung:** Die Klassenzuordnung erfolgt nicht nur durch das Bewässerungsprotokoll, sondern wird durch unabhängige physiologische Messungen (stomatale Leitfähigkeit, Blattwasserpotential) abgesichert — eine methodische Stärke gegenüber rein korrelativen Vorgängerstudien.

#### 4.4 Evaluation des Modells

- **Klassifikationsgüte:** Konfusionsmatrix, Precision/Recall/F1 pro Klasse, Macro-F1
- **Baseline-Vergleich:** Einfacher Schwellwertklassifikator (UAE-Rate > τ → Stress) als nicht-ML-Vergleich
- **Ablationsstudie:** Training from scratch vs. Fine-Tuning vs. Feature-Freeze → quantifiziert den Transfer-Nutzen
- **Statistische Signifikanz:** McNemar-Test für paarweisen Klassifikatorvergleich

### 5. Regelstrategien (als experimentelle Bedingungen, nicht als Produktvarianten)

Die drei Regelstrategien werden als *unabhängige experimentelle Bedingungen* in Phase 3 (Tag 15–21) verglichen:

| Bedingung | Beschreibung | Forschungsbeitrag |
|---|---|---|
| **A — Schwellwert (Baseline)** | UAE-Rate überschreitet Schwellwert → Bewässerung | Minimaler Regelungseingriff: Reicht das? |
| **B — ML-Klassifikation** | ML-Modell klassifiziert Zustand → spezifische Intervention | Kann semantischere Zustandserkennung die Regelgüte verbessern? |
| **C — PID-Regelung** | UAE-Rate als kontinuierliche Prozessgröße → PID-Stellgröße | Erlaubt kontinuierliches akustisches Feedback feinere Regelung? |

**Zentrale Hypothese (alle Bedingungen):** Akustisch gesteuerte Bewässerung hält den Pflanzenzustand aufrecht (Fv/Fm, Biomasse) *und* reduziert den Wasserbedarf gegenüber getakteter Bewässerung.

### 6. Statistische Auswertung

- **FF1 (Korrelation):** Pearson/Spearman-Korrelation UAE-Rate ↔ Blattwasserpotential; lineares gemischtes Modell mit Pflanze als Zufallseffekt
- **FF2 (Klassifikation):** Konfusionsmatrix, 3×3; zufallskorrigierter Cohen's κ; Vergleich gegen Majority-Class-Baseline
- **FF3 (Regelung):** Repeated-measures ANOVA über die drei Regelbedingungen × zwei Bewässerungsmodi (akustisch vs. getaktet); Post-hoc: Tukey HSD

### 7. Erwarteter wissenschaftlicher Beitrag

| Beitrag | Beschreibung |
|---|---|
| **Empirisch** | Erstmaliger Nachweis, dass pflanzliche UAE als Echtzeit-Feedback in einem geschlossenen Regelkreis funktional einsetzbar sind |
| **Methodisch** | Adaption von Keyword-Spotting-Architekturen auf bioakustische Klassifikationsprobleme im Ultraschallbereich |
| **Konzeptionell** | Erweiterung des Plant-in-the-Loop-Paradigmas um eine bisher ungenutzte, kontaktlose Signalmodalität |
| **Abgrenzend** | Systematischer Vergleich akustischer Regelung gegen getaktete Bewässerung (Kontrollgruppe) und gegen nicht-akustische PIL-Verfahren (Literatur) |

### 8. Einordnung in den Stand der Forschung

| Aspekt | Kernbach (2024) | Khait et al. (2023) | **Diese Arbeit** |
|---|---|---|---|
| Signalquelle | Pflanzenelektrophysiologie | Luftgetragener Ultraschall | Luftgetragener Ultraschall |
| Closed-Loop | Ja (Beleuchtung, Bewässerung) | Nein (nur Klassifikation) | **Ja (Bewässerung via akustischem Feedback)** |
| ML-Modellierung | Nicht im Fokus | CNN auf Spektrogramm (offline) | **Transfer von Keyword-Spotting; Quantisierung für dezentrale Inferenz** |
| Kontakt zur Pflanze | Elektroden (invasiv/aufliegend) | Kondensatormikrofone (kontaktlos) | Breitband-Mikrofon (kontaktlos) |
| Experimentelles Design | Demonstration im Labor | Korrelative Feldmessung | **Kontrolliertes Experiment mit Positiv-/Negativkontrolle, n ≥ 12** |
| Regelstrategie | Direktes Biofeedback | Keine | **Vergleich Schwellwert vs. ML-Klassifikation vs. PID** |

---

*Erstellt: Mai 2026 | Branch: literatur-abgrenzungstabelle-akustisch*
