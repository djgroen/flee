"""
Dual-Process Cognitive Model (System 1 / System 2) — Continuous Mixture.

Renamed from ``s1s2_model.py`` in Day 7b to disambiguate from sobol
sensitivity indices (first-order ``S_first`` and total-order ``ST`` in the
remap convention used after Day 7b). Within this module, the ``S2`` in
``P_S2`` and ``compute_s2_move_probability`` refers to System 2 cognition,
not a sobol second-order index. See ``results/day7b/COLUMN_CHANGELOG.md``
for full notation rules.

Mathematical model (nuclear reduced form):
    Ψ(x; α) = Ψ_min + (1 - Ψ_min)(1 - exp(-αx))   # Cognitive capacity
    Ω(c; β) = exp(-βc)                              # Structural opportunity
    P_S2   = Ψ × Ω                                  # Deliberation reliability
    σ      = 1 / (1 + exp(-κ·(rad_here - rad_best)/d_best))  # System 2 move probability

Free parameters: α, β, κ
Architectural constant: Ψ_min = 0.1
"""

import math

PSI_MIN = 0.1  # Baseline deliberative capacity (Assumption 1 in theory doc)


def compute_capacity(experience_index: float, alpha: float = 2.0) -> float:
    """Cognitive capacity: Ψ(x; α) = Ψ_min + (1 - Ψ_min)(1 - exp(-αx))"""
    return PSI_MIN + (1.0 - PSI_MIN) * (1.0 - math.exp(-alpha * max(0.0, experience_index)))


def compute_opportunity(perceived_threat: float, beta: float = 2.0) -> float:
    """
    Structural opportunity: Ω(c; β) = exp(-βc)

    Driven by perceived threat (urgency, panic, noise) — NOT radiation per se.
    In nuclear context, perceived_threat is correlated with radiation but also
    includes official warnings, proximity to plant, social panic signals.
    Interface unchanged; parameter renamed for clarity.
    """
    return math.exp(-beta * max(0.0, min(1.0, perceived_threat)))


def compute_deliberation_weight(experience_index: float, perceived_threat: float,
                                 alpha: float = 2.0, beta: float = 2.0) -> float:
    """Deliberation reliability weight: P_S2 = Ψ × Ω (continuous, NOT a probability for Bernoulli draw)."""
    return compute_capacity(experience_index, alpha) * compute_opportunity(perceived_threat, beta)


def compute_s2_move_probability(
    rad_here: float,
    rad_best: float,
    distance_best: float,
    kappa: float = 5.0,
) -> float:
    """
    S2 (deliberative) move probability: logistic function of radiation-per-distance.

    Nuclear reduced form: gamma=0 (no social ties), eta=1 (linear distance decay).

    Positive signal (rad_here > rad_best): agent moves toward safer location.
    Zero signal (rad_here == rad_best): sigma = 0.5 (uncertain).
    Negative signal (rad_here < rad_best): agent tends to stay.

    Ref: Daw, Niv & Dayan 2005 NatureNeuro; Zipf 1946 for distance decay.
    """
    if distance_best <= 0:
        distance_best = 1.0
    safety_signal = kappa * (rad_here - rad_best) / distance_best
    safety_signal = max(-20.0, min(20.0, safety_signal))
    return 1.0 / (1.0 + math.exp(-safety_signal))


class RadiationField:
    """
    Spatially and temporally varying radiation dose rate field.
    For Fukushima validation: wraps a 2D interpolant over plume model output.
    For idealized runs: returns a distance-from-source function.

    Units: mSv/hr (normalized to [0,1] for use in s2 signal).
    """

    def __init__(self, mode="distance_decay", source_lat=37.421, source_lon=141.033):
        self.mode = mode
        self.source_lat = source_lat  # Fukushima Daiichi
        self.source_lon = source_lon
        self._interpolant = None  # populated by load_plume_data()

    def load_plume_data(self, filepath: str):
        """
        Load spatially gridded dose rate data (CSV or NetCDF).
        Expected columns: lat, lon, time_hours, dose_rate_msv_hr
        Builds scipy RegularGridInterpolator for fast lookup.
        """
        import pandas as pd

        df = pd.read_csv(filepath)
        # Build interpolant — stub for now, full implementation in Prompt 4
        self.mode = "plume"
        self._df = df  # store raw for now

    def get_dose_rate(self, lat: float, lon: float, time_hours: float = 0.0) -> float:
        """
        Return normalized dose rate [0,1] at location (lat, lon) at time_hours.
        0 = background, 1 = maximum observed in field.
        """
        if self.mode == "distance_decay":
            dlat = lat - self.source_lat
            dlon = lon - self.source_lon
            dist_km = math.sqrt((dlat * 111.0) ** 2 + (dlon * 88.0) ** 2)
            return math.exp(-dist_km / 20.0)  # 20km decay length
        elif self.mode == "plume" and self._interpolant is not None:
            return float(self._interpolant([[lat, lon, time_hours]])[0])
        return 0.0


__all__ = [
    "PSI_MIN",
    "compute_capacity",
    "compute_opportunity",
    "compute_deliberation_weight",
    "compute_s2_move_probability",
    "RadiationField",
]
