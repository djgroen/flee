# Fukushima 2011 Evacuation Observations

## Source
Hayano, R.S. and Adachi, R. (2013). Estimation of the total population
moving into and out of the 20 km evacuation zone during the Fukushima NPP
accident as calculated using "Auto-GPS" mobile phone data.
Proceedings of the Japan Academy, Series B, 89(5):196-199.
DOI: 10.2183/pjab.89.196. PMC: PMC3722575.

## Files
- `hayano_2013_fig3_hourly.csv` — Population by distance zone, hourly
  resolution, March 10-18 2011. Digitized from Figure 3 using graph2table.com.

## Known limitations
- Data digitized from published figures, not raw GPS data.
- GPS method accuracy: +-20% at n=10,000; +-50% at n=1,000 (per paper).
- Rows 2011-03-13 06:00 through 2011-03-14 12:00 are unreliable due to
  mobile phone network outage from power failures. Flagged as unusable
  in calibration_targets/fukushima_2011_targets.csv.
- Temporal resolution is 4-6 hours in digitized version vs. hourly in
  original. Inner band departure timing accurate to +-2-4 hours.
- Diurnal spikes in <5km band on 3/10-11 reflect TEPCO plant worker
  commuting, not residential population. Residential baseline is
  taken from 2011-03-11 04:00 (pre-earthquake night values).

## Key event timestamps (JST, t=0 at earthquake onset)
- t=0.0h:  2011-03-11 14:46  Earthquake / crisis onset (t=0)
- t=6.6h:  2011-03-11 21:23  3km evacuation order issued
- t=15.0h: 2011-03-12 05:44  10km evacuation order issued
- t=24.8h: 2011-03-12 15:36  Hydrogen explosion Unit 1
- t=27.6h: 2011-03-12 18:25  20km evacuation order issued

## Calibration targets
See data/calibration_targets/fukushima_2011_targets.csv
