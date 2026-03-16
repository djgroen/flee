# Fukushima 2011 — Observational Data

## Source
Hayano, R.S. and Adachi, R. (2013). Estimation of the total population
moving into and out of the 20 km evacuation zone during the Fukushima NPP
accident as calculated using "Auto-GPS" mobile phone data.
Proceedings of the Japan Academy, Series B, 89(5):196-199.
DOI: 10.2183/pjab.89.196. PMC: PMC3722575.

## Files
- `hayano_2013_fig3_hourly.csv` — Population by distance zone (8 bands,
  0-5km through 35-40km), 4-6 hour resolution, March 10-18 2011.
  Digitized from Figure 3 using graph2table.com.

## Known limitations
- Digitized from published figures, not raw GPS data.
- GPS accuracy: +-20% at n=10,000; +-50% at n=1,000 (per paper).
- Rows 2011-03-13 06:00 through 2011-03-14 12:00: network outage artifact.
  Flagged usable=FALSE in data/calibration_targets/fukushima_2011_targets.csv.
- Diurnal spikes in <5km on 3/10-3/11 are TEPCO plant workers, not
  residents. Residential baseline: 2011-03-11 04:00.

## Key event timestamps (JST)
- 2011-03-11 14:46  t=0.0h   Earthquake / crisis onset
- 2011-03-11 21:23  t=6.6h   3km evacuation order
- 2011-03-12 05:44  t=15.0h  10km evacuation order
- 2011-03-12 15:36  t=24.8h  Hydrogen explosion Unit 1
- 2011-03-12 18:25  t=27.6h  20km evacuation order
