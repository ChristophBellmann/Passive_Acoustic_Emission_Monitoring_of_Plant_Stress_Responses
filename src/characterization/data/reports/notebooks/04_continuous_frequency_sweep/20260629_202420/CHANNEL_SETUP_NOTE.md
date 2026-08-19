# Channel Setup Caveat

This run was stopped on 2026-06-30 after the physical channel wiring was clarified.

Actual sensor wiring at the time of review:

| Channel | Actual sensor |
| --- | --- |
| CH1 | amplifier + 820 kΩ + piezo |
| CH2 | disabled |
| CH3 | amplifier + 820 kΩ + piezo + metal rod |
| CH4 | amplifier + 820 kΩ + piezo + metal rod |

The acquisition notebook and deep-memory setup used by this run still contained
stale assumptions from earlier setups:

- CH1 was documented as a Pico GP14 marker / timing channel in the notebook.
- `deep_acquisition.py` configured CH1 as a passive 1:1 820 kΩ reference channel
  at 0.02 V/div.
- `experiment_plant_acoustic_emissions_20260621/config.yaml` still described a
  legacy CH1/CH2/CH3 setup and did not define CH4 metadata.

Consequence:

- Raw CH3/CH4 voltage data remain useful as sensor data.
- CH1 amplitude, labels, and any interpretation treating CH1 as a timing marker,
  EM reference, or correctly scaled amplified channel are not reliable for this run.
- Cross-channel event labels and reports should be interpreted with this caveat.

The code/configuration was corrected after this run for future acquisitions.
