#!/usr/bin/env python3
"""Generate TMI network CSVs, conflict schedule, population, and empirical JSON (Day 11)."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TMI = REPO / "input_data" / "tmi"

LOCATIONS = [
    # name, region, country, gps_x(lon), gps_y(lat), type, conflict_date, pop/cap, [optional attrs]
    ("middletown", "Dauphin", "USA", "-76.730", "40.200", "town", "-1", "9000"),
    ("goldsboro", "York", "USA", "-76.787", "40.140", "town", "-1", "1100"),
    ("royalton", "Dauphin", "USA", "-76.718", "40.188", "town", "-1", "1200"),
    ("elizabethtown", "Lancaster", "USA", "-76.602", "40.152", "town", "-1", "8500"),
    ("hershey", "Dauphin", "USA", "-76.650", "40.286", "forward", "-1", "14000"),
    ("harrisburg", "Dauphin", "USA", "-76.884", "40.273", "town", "-1", "68000"),
    ("steelton", "Dauphin", "USA", "-76.834", "40.232", "town", "-1", "6200"),
    ("new_cumberland", "Cumberland", "USA", "-76.868", "40.232", "town", "-1", "7000"),
    ("york", "York", "USA", "-76.728", "39.962", "town", "-1", "45000"),
    ("lancaster", "Lancaster", "USA", "-76.306", "40.038", "town", "-1", "54000"),
    ("carlisle", "Cumberland", "USA", "-77.188", "40.202", "town", "-1", "19000"),
    ("lebanon", "Lebanon", "USA", "-76.437", "40.340", "town", "-1", "25000"),
    ("harrisburg_camp", "Dauphin", "USA", "-76.870", "40.285", "camp", "-1", "200000"),
    ("lancaster_camp", "Lancaster", "USA", "-76.292", "40.025", "camp", "-1", "150000"),
    ("york_camp", "York", "USA", "-76.714", "39.948", "camp", "-1", "100000"),
]

# Undirected logical corridors (linkUp adds reverse automatically). 17 rows.
ROUTES = [
    ("middletown", "harrisburg", "15.0", "0"),
    ("middletown", "elizabethtown", "15.0", "0"),
    ("middletown", "hershey", "18.0", "0"),
    ("middletown", "steelton", "8.0", "0"),
    ("steelton", "new_cumberland", "6.0", "0"),
    ("new_cumberland", "harrisburg", "5.0", "0"),
    ("harrisburg", "carlisle", "35.0", "0"),
    ("harrisburg", "harrisburg_camp", "1.0", "0"),
    ("hershey", "lebanon", "24.0", "0"),
    ("hershey", "harrisburg", "18.0", "0"),
    ("elizabethtown", "lancaster", "20.0", "0"),
    ("elizabethtown", "york", "30.0", "0"),
    ("lancaster", "lancaster_camp", "1.0", "0"),
    ("york", "york_camp", "1.0", "0"),
    ("york", "harrisburg", "35.0", "0"),
    ("goldsboro", "harrisburg", "18.0", "0"),
    ("royalton", "middletown", "3.0", "0"),
    ("lebanon", "harrisburg", "38.0", "0"),
]

C_VALUES = [
    0.00, 0.05, 0.15, 0.30, 0.20, 0.25, 0.20, 0.25, 0.35, 0.75,
    1.00, 0.85, 0.55, 0.40, 0.30, 0.20, 0.10, 0.08, 0.05, 0.00,
]

POPULATION_ROWS = [
    ("middletown", 20),
    ("goldsboro", 3),
    ("royalton", 3),
    ("elizabethtown", 10),
    ("hershey", 15),
    ("harrisburg", 65),
    ("steelton", 7),
    ("new_cumberland", 10),
    ("york", 50),
    ("lancaster", 60),
    ("carlisle", 20),
    ("lebanon", 37),
]

PSI_NOTE = """Psi operationalization: Option B (Day 11)

Option B uses the same experience_index distribution as standard FLEE / Fukushima
initialization (Beta(2, 5) in Person.__init__), assigned independently per agent
without distance-based or zone-based structure.

Rationale: if the Zeigler paradox (early short-distance departures near the plant vs
later long-distance travel from the outer zone) emerges without baking spatial Psi
into initialization, that is stronger evidence for the dual-process mechanism.

A distance-stratified Psi sensitivity is deferred to Day 14.
"""

CONFLICT_SCHEDULE_META = {
    "description": "TMI five-day information crisis schedule",
    "omega_type": "spatially_uniform_temporally_volatile",
    "fukushima_contrast": "Fukushima is spatially structured, temporally stable",
    "timestep_hours": 6,
    "n_timesteps": 20,
    "peak_timestep": 10,
    "peak_event": "Governor Thornburgh advisory + NRC misreport, March 30 12:30pm",
    "peak_empirical_anchor": "54-55% of all evacuation units departed this day (3 surveys)",
    "recovery_timestep": 16,
    "recovery_event": "President Carter tours TMI plant, April 1",
    "recovery_empirical_anchor": "98% return within 3 weeks begins here",
    "sources": ["Kemeny Commission 1979", "Walker 2004", "Zeigler et al. 1981"],
    "c_values": C_VALUES,
}

# Empirical database for figures — single source; figure scripts read only this file.
TMI_EMPIRICAL_DATA = {
    "flee_model_qois_summary": {
        "primary_qois": [
            {"name": "share_departed_peak_day", "target": 0.54},
            {"name": "return_within_three_weeks", "target": 0.98},
            {"name": "evacuation_rate_flat_inside_12mi", "target": 0.39},
            {"name": "median_evacuation_distance_miles_zeigler", "target": 85.0},
            {"name": "mean_evacuation_distance_miles_cutter", "target": 111.6},
            {"name": "directional_flow_nw_fraction", "target": 0.50},
            {"name": "inner_zone_departure_by_friday_fraction", "target": 0.77},
            {"name": "outer_zone_departure_by_friday_fraction", "target": 0.33},
        ]
    },
    "conflict_schedule": {
        "key_events": {
            "t_10": {"description": "Governor advisory spike", "departure_fraction_surveys": [0.54, 0.55]},
            "t_16": {"description": "Carter visit; return window opens"},
        }
    },
    "evacuation_quarters": {
        "hershey_official_shelter_households": 1,
        "note": "Zeigler 1981; model Hershey as transit, not camp.",
    },
    "evacuation_rate_by_distance": {
        "source": "Zeigler 1981 Table III",
        "discontinuity_mi": 12,
        "data": [
            {"zone": "1-3 mi", "rate_percent": 55, "zone_group": "inner"},
            {"zone": "4-6 mi", "rate_percent": 56, "zone_group": "inner"},
            {"zone": "7-9 mi", "rate_percent": 53, "zone_group": "middle"},
            {"zone": "10-12 mi", "rate_percent": 47, "zone_group": "middle"},
            {"zone": "13-15 mi", "rate_percent": 13, "zone_group": "outer"},
            {"zone": ">15 mi", "rate_percent": 9, "zone_group": "outer"},
        ],
    },
    "departure_timing": {
        "friday_timestep": 10,
        "footnote_interpolation": (
            "Interpolated; only 0-6mi (77%) and >10mi (33%) are directly reported "
            "in Zeigler et al. 1981. Intermediate values are estimated."
        ),
        "zones_g1": [
            {"label": "1-3 mi", "pct_by_friday": 77.0, "interpolated": False, "style": "inner"},
            {"label": "4-6 mi", "pct_by_friday": 77.0, "interpolated": False, "style": "inner"},
            {"label": "7-9 mi", "pct_by_friday": 60.0, "interpolated": True, "style": "middle"},
            {"label": "10-12 mi", "pct_by_friday": 45.0, "interpolated": True, "style": "middle"},
            {"label": "13-15 mi", "pct_by_friday": 20.0, "interpolated": True, "style": "outer"},
            {"label": ">15 mi", "pct_by_friday": 15.0, "interpolated": True, "style": "outer"},
        ],
        "cumulative_departure_g3": {
            "0-6mi": {
                "points": [
                    {"date": "1979-03-28", "cumulative_pct": 10.0},
                    {"date": "1979-03-30", "cumulative_pct": 77.0},
                    {"date": "1979-03-31", "cumulative_pct": 95.0},
                    {"date": "1979-04-01", "cumulative_pct": 100.0},
                ]
            },
            "7-12mi": {
                "points": [
                    {"date": "1979-03-28", "cumulative_pct": 5.0},
                    {"date": "1979-03-30", "cumulative_pct": 50.0},
                    {"date": "1979-03-31", "cumulative_pct": 90.0},
                    {"date": "1979-04-02", "cumulative_pct": 100.0},
                ],
                "interpolated": True,
            },
            ">12mi": {
                "points": [
                    {"date": "1979-03-28", "cumulative_pct": 5.0},
                    {"date": "1979-03-30", "cumulative_pct": 33.0},
                    {"date": "1979-04-01", "cumulative_pct": 85.0},
                    {"date": "1979-04-03", "cumulative_pct": 100.0},
                ]
            },
        },
    },
    "evacuation_rates_comparison": {
        "zeigler_1981_table3": [
            {"zone": "1-3", "rate_percent": 55},
            {"zone": "4-6", "rate_percent": 56},
            {"zone": "7-9", "rate_percent": 53},
            {"zone": "10-12", "rate_percent": 47},
            {"zone": "13-15", "rate_percent": 13},
            {"zone": ">15", "rate_percent": 9},
        ],
        "cutter_1982_table2": [
            {"zone": "0-5", "rate_percent": 52},
            {"zone": "5-10", "rate_percent": 48},
            {"zone": "10-15", "rate_percent": 35},
            {"zone": "15-20", "rate_percent": 18},
            {"zone": ">20", "rate_percent": 8},
        ],
    },
    "advisory_contrast": {
        "pct_within_15mi_evacuated": 39,
        "pct_officially_advised": 0.5,
    },
    "stress_curves_g2": {
        "threshold": 0.65,
        "threshold_citation": "Zeigler 1981, p.13",
        "evacuees": [
            [0, 0.15], [1, 0.25], [2, 0.35], [3, 0.45], [4, 0.40], [5, 0.42],
            [6, 0.48], [7, 0.52], [8, 0.62], [9, 0.78], [10, 0.85], [11, 0.70],
            [12, 0.55], [13, 0.48], [14, 0.40], [15, 0.30], [16, 0.18], [17, 0.12],
            [18, 0.08], [19, 0.05],
        ],
        "residual_population": [
            [0, 0.08], [1, 0.12], [2, 0.18], [3, 0.22], [4, 0.20], [5, 0.24],
            [6, 0.26], [7, 0.28], [8, 0.35], [9, 0.48], [10, 0.52], [11, 0.50],
            [12, 0.45], [13, 0.40], [14, 0.35], [15, 0.28], [16, 0.18], [17, 0.14],
            [18, 0.10], [19, 0.06],
        ],
        "event_markers": [
            {"t": 3, "label": "Scranton reversal"},
            {"t": 9, "label": "NRC misreport"},
            {"t": 10, "label": "Governor's advisory\n← 54% depart", "emphasis": "red"},
            {"t": 16, "label": "Carter visits plant\n← return begins", "emphasis": "green"},
        ],
    },
    "return_behavior": {
        "weeks": [0, 1, 2, 3, 4],
        "cumulative_return_pct": [0, 53, 90, 98, 100],
        "carter_visit_date": "1979-04-01",
    },
    "cutter_age_evacuation_rates": {
        "source": "Cutter 1982 Table 3",
        "age_groups": ["20-29", "30-39", "40-49", "50-59", "60+"],
        "rates_percent": [46.8, 43.5, 45.3, 14.3, 13.8],
    },
    "cutter_social_influence": {
        "source": "Cutter 1982 Table 6",
        "evacuees_neighbors_left_pct": 74,
        "non_evacuees_neighbors_stayed_pct": 50,
        "p_value_note": "0.000",
    },
    "reasons_for_evacuating": [
        {"reason": "Safety", "percent": 91},
        {"reason": "Gov+Utility conflict", "percent": 48},
        {"reason": "Utility conflict", "percent": 26},
        {"reason": "Govt conflict", "percent": 24},
        {"reason": "News media", "percent": 20},
        {"reason": "Everyone evacuating", "percent": 7},
    ],
    "reasons_for_not_evacuating": [
        {"reason": "No order", "percent": 62},
        {"reason": "Conflicting reports", "percent": 42},
        {"reason": "No reason", "percent": 38},
        {"reason": "Safe distance", "percent": 31},
        {"reason": "Fear looting", "percent": 24},
        {"reason": "No children", "percent": 23},
    ],
    "education_effect": {
        "finding_rutgers_weak": {
            "spatial_inconsistency": [
                {"zone_code": "I", "zone": "0-5mi", "chi_sq": 1.52, "p_value": 0.750, "gamma": 0.137},
                {"zone_code": "II", "zone": "5-10mi", "chi_sq": 13.72, "p_value": 0.003, "gamma": 0.582},
                {"zone_code": "III", "zone": "10-15mi", "chi_sq": 3.27, "p_value": 0.351, "gamma": 0.033},
                {"zone_code": "IV", "zone": "15-20mi", "chi_sq": 11.54, "p_value": 0.010, "gamma": 0.647},
            ]
        }
    },
    "johnson_zeigler_1986_panel": {
        "r2": 0.21,
        "reclassified_pct": 71,
        "caption": (
            "Predicts WHO evacuated (binary)\n"
            "p²=0.21 · 71% reclassified\n"
            "Static logistic model · Cannot produce Zeigler paradox"
        ),
    },
    "flee_dual_process_panel": {
        "caption": (
            "Predicts WHERE agents go and HOW FAR\n"
            "Zeigler paradox · Return timing · Shadow evacuation\n"
            "Dynamic · Agent-based"
        ),
    },
    "bridging_model_text": (
        "COMPLEMENTARY, NOT COMPETING\n"
        "JZ1986: explains who left (demographics → binary decision)\n"
        "FLEE: explains where they went (cognitive architecture → trajectory)\n"
        "JZ1986 'evacuation-response threshold' (p.13) = CMC in FLEE\n"
        "Threshold variability across agents = Ψ distribution"
    ),
    "destination_map_g6": {
        "plant": {"lat": 40.153, "lon": -76.726},
        "flow_arrows": [
            {"direction": "NW", "fraction_pct": 50, "lw": 4.0},
            {"direction": "SE", "fraction_pct": 10, "lw": 1.5},
            {"direction": "NE", "fraction_pct": 20, "lw": 2.0},
            {"direction": "SW", "fraction_pct": 20, "lw": 2.0},
        ],
        "rings_mi": [15, 45, 90],
        "cities": [
            {"name": "Harrisburg", "lat": 40.273, "lon": -76.884, "note": "transit only"},
            {"name": "Middletown", "lat": 40.200, "lon": -76.730, "note": "plant area"},
            {"name": "Carlisle", "lat": 40.202, "lon": -77.188, "note": ""},
            {"name": "Hershey", "lat": 40.286, "lon": -76.650, "note": "unused shelter"},
            {"name": "State College", "lat": 40.793, "lon": -77.860, "note": ""},
            {"name": "Reading", "lat": 40.336, "lon": -75.927, "note": ""},
            {"name": "Philadelphia", "lat": 39.953, "lon": -75.164, "note": ""},
            {"name": "Baltimore", "lat": 39.290, "lon": -76.612, "note": ""},
            {"name": "Pittsburgh", "lat": 40.441, "lon": -79.990, "note": ""},
            {"name": "New York", "lat": 40.713, "lon": -74.006, "note": ""},
        ],
        "distance_estimates": [
            {"label": "85 mi (MSU, Zeigler 1981)", "kind": "median"},
            {"label": "100 mi (NRC, Flynn 1979)", "kind": "median"},
            {"label": "111.6 mi (Rutgers, Cutter 1982)", "kind": "mean"},
        ],
    },
}


def write_locations(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["#name", "region", "country", "gps_x", "gps_y", "location_type", "conflict_date", "pop/cap"]
        )
        w.writerows(LOCATIONS)


def write_routes(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#name1", "name2", "distance", "forced_redirection"])
        w.writerows(ROUTES)


def write_conflicts(path: Path, loc_names: list[str]) -> None:
    """Uniform c(t) on population nodes only. Camps are omitted so they stay sinks."""
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#Day"] + loc_names)
        for t, c in enumerate(C_VALUES):
            w.writerow([str(t)] + [f"{c:.2f}"] * len(loc_names))


def write_population(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#location", "n_agents"])
        w.writerows(POPULATION_ROWS)


def main() -> None:
    TMI.mkdir(parents=True, exist_ok=True)
    (REPO / "results" / "tmi" / "smoke_test").mkdir(parents=True, exist_ok=True)
    (REPO / "figures" / "tmi" / "empirical").mkdir(parents=True, exist_ok=True)

    loc_path = TMI / "locations.csv"
    write_locations(loc_path)
    write_routes(TMI / "routes.csv")
    pop_nodes = [row[0] for row in LOCATIONS if "camp" not in row[5].lower()]
    write_conflicts(TMI / "conflicts.csv", pop_nodes)
    write_population(TMI / "population_tmi.csv")
    (TMI / "psi_initialization_note.txt").write_text(PSI_NOTE, encoding="utf-8")

    with (TMI / "conflict_schedule_tmi.json").open("w", encoding="utf-8") as f:
        json.dump(CONFLICT_SCHEDULE_META, f, indent=2)

    emp_path = TMI / "tmi_empirical_data.json"
    with emp_path.open("w", encoding="utf-8") as f:
        json.dump(TMI_EMPIRICAL_DATA, f, indent=2)

    # Validate
    with emp_path.open(encoding="utf-8") as f:
        d = json.load(f)
    assert "flee_model_qois_summary" in d
    assert len(d["flee_model_qois_summary"]["primary_qois"]) == 8
    print("Wrote TMI inputs to", TMI)
    print("Empirical JSON OK —", len(d), "top-level keys")


if __name__ == "__main__":
    main()
