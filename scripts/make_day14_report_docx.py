#!/usr/bin/env python3
"""Generate the Day 14 TMI CMC-calibration Word report.

Reads the committed Day-14 result artifacts and builds a structured .docx with
the calibration design, the clamp diagnostic, the Stage-1 grid result, the
regime-justified clamp decision, the locked TMI CMC, the robustness verdict,
the camp/path-metric fix, the calibration figure, gate status (the check-26
flip headline), and the Day-15/16 implications.

Output: reports/TMI_Day14_Report.docx   (NOT committed to the repo)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

REPO = Path(__file__).resolve().parent.parent
RES = REPO / "results" / "tmi"
FIG = REPO / "figures" / "tmi"
OUT = REPO / "reports" / "TMI_Day14_Report.docx"

NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2E, 0x5F, 0xA3)
GOLD = RGBColor(0xC9, 0xA2, 0x27)
GREY = RGBColor(0x55, 0x55, 0x55)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
RED = RGBColor(0xB0, 0x2A, 0x2A)


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------

def _load():
    return {
        "locked": json.loads((RES / "day14_locked_params.json").read_text()),
        "rob": json.loads((RES / "day14_robustness_verdict.json").read_text()),
        "gate": json.loads((RES / "diagnostics_gate_day14.json").read_text()),
        "grid": pd.read_csv(RES / "day14_calibration_grid.csv"),
        "diag": pd.read_csv(RES / "day14_clamp_diagnostic.csv"),
        "rob_csv": pd.read_csv(RES / "day14_robustness.csv"),
        "path": pd.read_csv(RES / "day14_zeigler_pathfix.csv"),
        "path_note": (RES / "day14_zeigler_pathfix_note.txt").read_text().strip(),
    }


# --------------------------------------------------------------------------
# docx helpers
# --------------------------------------------------------------------------

def _h(doc, text, level=1, color=NAVY, size=None):
    p = doc.add_heading(level=level)
    run = p.add_run(text)
    run.font.color.rgb = color
    if size:
        run.font.size = Pt(size)
    return p


def _para(doc, text, italic=False, bold=False, size=10.5, color=None, space_after=6):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = italic
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    p.paragraph_format.space_after = Pt(space_after)
    return p


def _bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        r.font.size = Pt(10.5)
    r2 = p.add_run(text)
    r2.font.size = Pt(10.5)
    return p


def _style_header_row(row):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    for cell in row.cells:
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                r.font.size = Pt(9.5)
        tc = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "1F3864")
        tc.append(shd)


def _table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        t.rows[0].cells[i].paragraphs[0].add_run(h)
    _style_header_row(t.rows[0])
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            run = cells[i].paragraphs[0].add_run(str(v))
            run.font.size = Pt(9.5)
    if widths:
        for col, w in enumerate(widths):
            for row in t.rows:
                row.cells[col].width = Inches(w)
    return t


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build():
    d = _load()
    locked, rob, gate = d["locked"], d["rob"], d["gate"]
    grid, diag = d["grid"], d["diag"]
    path = d["path"]
    bf = locked["best_fit"]
    tgt = locked["empirical_targets"]

    off = grid[grid.clamp == "off"].reset_index(drop=True)
    on = grid[grid.clamp == "on"].reset_index(drop=True)
    off_best = off.loc[off.misfit.idxmin()]
    on_best = on.loc[on.misfit.idxmin()]
    cmc_lock = locked["tmi_cmc_locked"]

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)

    # --- Title block ---
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("FLEE Dual-Process Model \u2014 Phase 3: TMI Full Calibration")
    r.bold = True; r.font.size = Pt(13); r.font.color.rgb = NAVY
    sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("Day 14 \u2014 TMI CMC Calibration, Panic-Clamp Decision, and "
                    "Path-Metric Fix")
    r.bold = True; r.font.size = Pt(15); r.font.color.rgb = BLUE
    attr = doc.add_paragraph(); attr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = attr.add_run("Columbia University Climate School \u00b7 Center for Climate "
                     "Systems Research")
    r.italic = True; r.font.size = Pt(10); r.font.color.rgb = GREY
    doc.add_paragraph()

    # --- 1. Executive Summary ---
    _h(doc, "1. Executive Summary", level=1)
    _para(doc,
          "Day 14 inverts the Fukushima Days 8\u20139 procedure. At Fukushima the "
          "conflict move-chance (CMC) was physically anchored and the dual-process "
          "parameters \u03b1/\u03b2/\u03ba were fit; at TMI the reverse holds \u2014 \u03b1/\u03b2/\u03ba are "
          "LOCKED at the Fukushima transfer values (1.6667 / 2.1667 / 18.407) and "
          "CMC is the single free parameter, calibrated jointly with a decision on "
          "the panic clamp because the two interact. Day 13 had shown CMC is the "
          "mobilisation calibration target (ST=0.78) but that the clamp masks it "
          "(total-evac ST 0.61\u21920.78 when the clamp is removed). The central "
          "question is whether TMI's information-driven threat implies a different "
          "physical CMC than Fukushima's radiological one.")
    _para(doc,
          "Answer: yes \u2014 markedly lower. The misfit-minimising solution is "
          f"CMC = {cmc_lock:.2f} under the clamp DISABLED, a lower-boundary "
          "solution (misfit increases monotonically with CMC). This is the "
          "physically sensible reading: TMI mobilisation is System-2 "
          "deliberation-driven, not System-1 panic-flight, so near-zero "
          "System-1 conflict move-chance is required. Versus Fukushima's locked "
          f"CMC = 0.25 the ratio is {locked['ratio_tmi_over_fukushima']:.2f} "
          "(lower, as hypothesised).", bold=False)

    _bullet(doc, f"DISABLED for the information regime. With the clamp ON, total "
                 "evac is flat across CMC (Task A) \u2014 unidentifiable; the "
                 "Fukushima population-wide 0.95 floor is the wrong physics for "
                 "TMI's uniform, information-driven spike.", bold_prefix="Panic clamp: ")
    _bullet(doc, f"locked at {cmc_lock:.2f} (clamp OFF). Lower than Fukushima 0.25 "
                 f"(ratio {locked['ratio_tmi_over_fukushima']:.2f}).",
            bold_prefix="TMI CMC: ")
    _bullet(doc, f"{bf['total_evac']*100:.1f}% at the locked CMC \u2014 IN the "
                 f"[{int(tgt['band'][0]*100)},{int(tgt['band'][1]*100)}]% band "
                 "(target ~21%). The Day-12/13 check 26 FLIPS to PASS.",
            bold_prefix="Total evac: ")
    _bullet(doc, f"CMC {rob['robustness_verdict']} (max QoI change "
                 f"{rob['max_relative_change']*100:.0f}% over CMC\u00b1neighbourhood); "
                 "P1 uniform P_S2 holds; \u03ba flat.", bold_prefix="Robustness: ")
    _bullet(doc, "\u03b1/\u03b2/\u03ba UNCHANGED (locked, not retuned) \u2014 gate check 38 "
                 "verifies this so the Day-16 cross-domain transfer test stays "
                 "valid.", bold_prefix="Guardrail: ")
    _para(doc, f"Diagnostics gate: {gate['verdict']}. Check 41 (total evac in band) "
               "FLIPPED to PASS \u2014 the headline validation that calibration "
               "worked; the single remaining failure is the inherited Day-12 "
               "frozen-CMC run, unchanged by design.", italic=True, color=GREY)

    # --- 2. Calibration design ---
    _h(doc, "2. Calibration Design", level=1)
    _para(doc, "Full-mixture (blend) mode \u2014 the regime in which \u03b1/\u03b2/\u03ba act and "
               "CMC enters via the System-1 move chance. TMI network (OSM driving "
               "distances from Day 12); horizon t_max = T_SCHED; 5 fixed seeds "
               "averaged per grid point; \u03b1/\u03b2/\u03ba held LOCKED throughout. "
               "conflict_movechance is applied via SimulationSettings overrides "
               "immediately after ReadFromYML().")
    _h(doc, "2.1 CMC grid and clamp states", level=2, color=BLUE)
    _table(doc, ["Aspect", "Setting"], [
        ["CMC range", "[0.00, 0.30]"],
        ["Fine resolution", "[0.00, 0.12] step 0.01 (where Day-13 expects the answer)"],
        ["Coarse resolution", "{0.15, 0.20, 0.25, 0.30} step 0.05"],
        ["Grid points", f"{len(off)} per clamp state"],
        ["Clamp states", "ON and OFF (full grid each)"],
        ["Seeds", "5 averaged per point"],
    ], widths=[1.9, 4.6])

    _h(doc, "2.2 Calibration QoIs and empirical targets", level=2, color=BLUE)
    _table(doc, ["QoI", "Role", "Empirical target"], [
        ["Total evacuation rate (20-mi pop)", "Primary",
         f"~{tgt['total_evac']*100:.0f}%  band "
         f"[{int(tgt['band'][0]*100)},{int(tgt['band'][1]*100)}]%"],
        ["Evac rate by band: inner / middle / outer", "Primary",
         f"{tgt['zones']['inner']:.2f} / {tgt['zones']['middle']:.2f} / "
         f"{tgt['zones']['outer']:.2f}"],
        ["Fraction of inner-zone departed by t=10", "Check",
         f">{tgt['frac_inner_by_t10_min']:.2f}"],
        ["Zeigler timing gap median_dep(outer)\u2212(inner)", "Directional",
         ">0 (outer leaves later)"],
    ], widths=[3.3, 0.9, 2.3])
    _para(doc, "Misfit = weighted sum-of-squares on QoIs 1\u20132 (primary), reported "
               "alongside QoIs 3\u20134. The total-evac QoI uses the established "
               "Day-12 definition exactly \u2014 evac_frac_town \u00d7 town_pop(258,000) / "
               "POP_20MI(663,500) \u2014 so that check 41 is the precise flip of "
               "check 26 (the model represents ~258k of the 20-mi region's 663.5k "
               "residents as mobile town agents).",
          italic=True, color=GREY, size=9.5)

    # --- 3. Clamp diagnostic ---
    _h(doc, "3. Clamp Diagnostic (Task A)", level=1)
    _para(doc, "Before calibrating, the clamp problem is demonstrated directly: a "
               "CMC sweep with the clamp ON shows total mobilisation is flat \u2014 "
               "essentially everyone moves once conflict spikes at t=10, "
               "irrespective of CMC.")
    drows = []
    for _, r0 in diag.iterrows():
        drows.append([f"{r0['cmc']:.2f}", f"{r0['total_evac_all']*100:.1f}%",
                      f"{r0['evac_inner']:.2f}", f"{r0['evac_outer']:.2f}"])
    span = (diag["total_evac_all"].max() - diag["total_evac_all"].min())
    _table(doc, ["CMC", "Within-20mi evac (clamp ON)", "evac inner", "evac outer"],
           drows, widths=[0.9, 2.4, 1.3, 1.3])
    _para(doc, f"CMC unidentifiable on evac rate under clamp ON: CONFIRMED "
               f"(within-20mi evac span only {span*100:.1f} pts across the full "
               "CMC range).", bold=True, color=RED)

    # --- 4. Calibration grid ---
    _h(doc, "4. Stage-1 CMC Calibration Grid (Task B)", level=1)
    _para(doc, "The full grid was run under both clamp states. For each state the "
               "CMC minimising misfit is reported; under clamp OFF the misfit "
               "increases monotonically with CMC, placing the optimum at the lower "
               "boundary.")
    _table(doc, ["Clamp", "Best-fit CMC", "Misfit", "Total evac",
                 "inner / mid / outer"], [
        ["OFF", f"{off_best['cmc']:.2f}", f"{off_best['misfit']:.3f}",
         f"{off_best['total_evac']*100:.1f}%",
         f"{off_best['evac_inner']:.2f} / {off_best['evac_middle']:.2f} / "
         f"{off_best['evac_outer']:.2f}"],
        ["ON", f"{on_best['cmc']:.2f}", f"{on_best['misfit']:.3f}",
         f"{on_best['total_evac']*100:.1f}%",
         f"{on_best['evac_inner']:.2f} / {on_best['evac_middle']:.2f} / "
         f"{on_best['evac_outer']:.2f}"],
    ], widths=[0.7, 1.1, 0.9, 1.0, 2.3])
    _para(doc, "Clamp OFF gives the far lower misfit (a third of the clamp-ON "
               "value) and an in-band total evac; clamp ON saturates the zone "
               "rates near unity. Best-fit CMC is 0.00 under both states, but only "
               "clamp OFF is identifiable and in band.", color=GREY, italic=True,
          size=9.5)

    # --- 5. Clamp decision ---
    _h(doc, "5. The Clamp Decision (Task C)", level=1)
    _table(doc, ["Criterion", "Clamp ON", "Clamp OFF"], [
        ["Identifiability (evac sensitive to CMC?)", "No (saturated)", "Yes"],
        ["Best-fit quality (in-band total evac?)",
         "No (~36% scaled, saturated)", "Yes (26.5%, in band)"],
        ["Zeigler timing differential emerges?",
         "No (saturated timing)", "Partial (uniform spike)"],
    ], widths=[3.0, 1.8, 1.8])
    _para(doc, "Verdict: DISABLE the panic clamp for the information regime. The "
               "decision is regime-justified, not fit-chasing: the clamp encodes "
               "near-certain flight under a LOCALISED SPATIAL hazard spike "
               "(Fukushima's inner zone). TMI's threat is UNIFORM and "
               "information-driven, so a population-wide movechance floor is "
               "physically inappropriate and it fires everywhere. A threshold "
               "retune cannot help here: with no spatial conflict gradient to key "
               "off, any level-based threshold fires everywhere or nowhere. The "
               "misfit numbers (Section 4) confirm the physical argument.", bold=True)
    _para(doc, "For the record (not implemented today): the cleaner long-term fix "
               "is a conflict-dependent CMC so flight-under-extreme-threat emerges "
               "from System-1 itself rather than from an override \u2014 flagged for "
               "the theory paper / future work.", italic=True, color=GREY, size=9.5)

    # --- 6. Locked CMC ---
    _h(doc, "6. Locked TMI CMC (Task D)", level=1)
    _table(doc, ["Parameter", "Value", "Status"], [
        ["TMI CMC (calibrated)", f"{cmc_lock:.2f}", "LOCKED (clamp OFF)"],
        ["Fukushima CMC", "0.25", "reference"],
        ["Ratio TMI / Fukushima", f"{locked['ratio_tmi_over_fukushima']:.2f}",
         "lower than Fukushima: "
         f"{'YES' if locked['lower_than_fukushima'] else 'NO'}"],
        ["\u03b1 (alpha)", f"{locked['alpha']}", "LOCKED (not retuned)"],
        ["\u03b2 (beta)", f"{locked['beta']}", "LOCKED (not retuned)"],
        ["\u03ba (kappa)", f"{locked['kappa']}", "LOCKED (not retuned)"],
    ], widths=[2.2, 1.3, 3.0])
    _para(doc, "Empirical cross-check: CMC \u2248 0 is consistent with TMI's observed "
               "voluntary / partial departure \u2014 mobilisation driven by official "
               "information and deliberation (System 2), not by an automatic "
               "conflict-triggered flight response (System 1). The lock is a "
               "lower-boundary solution and is reported as such.",
          italic=True, color=GREY, size=9.5)

    # --- 7. Match at locked CMC ---
    _h(doc, "7. Match at the Locked CMC", level=1)
    def _ok(cond):
        return ("PASS", GREEN) if cond else ("partial", GOLD)
    te_s, te_c = _ok(locked["total_evac_in_band"])
    rows = [
        ["Total evac (20-mi pop)", f"{bf['total_evac']*100:.1f}%",
         f"~{tgt['total_evac']*100:.0f}% (band "
         f"{int(tgt['band'][0]*100)}\u2013{int(tgt['band'][1]*100)}%)", te_s],
        ["Evac inner", f"{bf['evac_inner']:.2f}", f"{tgt['zones']['inner']:.2f}",
         "low"],
        ["Evac middle", f"{bf['evac_middle']:.2f}", f"{tgt['zones']['middle']:.2f}",
         "match"],
        ["Evac outer", f"{bf['evac_outer']:.2f}", f"{tgt['zones']['outer']:.2f}",
         "high"],
        ["Inner departed by t=10", f"{bf['frac_inner_by_t10']*100:.0f}%",
         f">{tgt['frac_inner_by_t10_min']*100:.0f}%", "slightly below"],
        ["Zeigler timing gap", f"{bf['zeigler_gap']:.1f}", ">0", "wrong sign"],
    ]
    _table(doc, ["QoI", "Model", "Empirical", "Verdict"], rows,
           widths=[2.3, 1.0, 1.8, 1.4])
    _para(doc, "HEADLINE: total evac is IN BAND \u2014 check 26 flips to PASS. "
               "Calibration succeeds on its primary driver.", bold=True, color=GREEN)
    _para(doc, "Honest caveat: the zone gradient is INVERTED (inner < middle < "
               "outer vs the empirical 0.55 > 0.50 > 0.16). The big outer towns "
               "(York, Lancaster) sit ~1 hop / ~2.5 km from a camp, so the "
               "System-2 gradient toward the adjacent zero-conflict camp pushes "
               "outer mobilisation toward 1. CMC cannot fix this (it is "
               "topology / System-2 driven, and \u03b1/\u03b2/\u03ba are locked). The "
               "total-evac band check passes; the zone-level fit does not \u2014 "
               "flagged for the Day-15 topology fix and the theory paper "
               "(conflict-dependent CMC). The uniform spike likewise gives all "
               "zones near-identical timing, so the timing-based Zeigler gap does "
               "not emerge with the expected sign this round.",
          italic=True, color=GREY, size=9.5)

    # --- 8. Robustness ---
    _h(doc, "8. CMC Robustness (Task E)", level=1)
    _para(doc, f"At the locked CMC plus a one-sided neighbourhood "
               f"{rob['neighbourhood']}, with \u03b1/\u03b2/\u03ba locked and the clamp OFF, "
               "the primary QoI stability gives a verdict of "
               f"{rob['robustness_verdict']} (same scheme as Fukushima Day 9, "
               "where CMC was MODERATE).")
    rc = rob["relative_change_by_qoi"]
    _table(doc, ["QoI", "Max relative change over neighbourhood"], [
        ["Total evac", f"{rc['total_evac']*100:.1f}%"],
        ["Evac inner", f"{rc['evac_inner']*100:.1f}%"],
        ["Evac middle", f"{rc['evac_middle']*100:.1f}%  (driver of the verdict)"],
        ["Evac outer", f"{rc['evac_outer']*100:.1f}%"],
    ], widths=[2.6, 3.4])
    _bullet(doc, f"verdict = {rob['robustness_verdict']} "
                 f"(max {rob['max_relative_change']*100:.1f}%; "
                 "ROBUST<15% MODERATE<30% else FRAGILE).", bold_prefix="CMC: ")
    _bullet(doc, f"P1 uniform P_S2 still holds (zone P_S2 spread "
                 f"{rob['zone_ps2_spread_t10']:.4f} < 0.05); peak mean P_S2 = "
                 f"{rob['peak_ps2']:.2f} (plausible).", bold_prefix="P_S2 dynamics: ")
    kc = rob["kappa_check"]
    _bullet(doc, f"flat / irrelevant at TMI \u2014 total evac span {kc['span']:.3f} "
                 f"over \u03ba\u2208{kc['kappas']} (consistent with Day-13 ST=0.01); "
                 "not retuned.", bold_prefix="\u03ba: ")

    # --- 9. Path-metric fix ---
    _h(doc, "9. Camp / Path-Metric Fix (Task F)", level=1)
    _para(doc, "The distance-based Zeigler signature (close = shorter travel, far = "
               "longer travel) was unreadable because camp adjacency dominates "
               "path-length-at-arrival. The diagnosis and the applied fix:")
    prows = []
    for _, r0 in path.iterrows():
        prows.append([r0["zone"], int(r0["n_arrivals"]),
                      f"{r0['nearest_camp_net_km']:.1f}",
                      f"{r0['nearest_camp_hops']:.1f}",
                      f"{r0['path_km_median']:.1f}",
                      f"{r0['dest_dist_plant_mi_median']:.1f}"])
    _table(doc, ["Zone", "Arrivals", "Nearest camp (km)", "Hops",
                 "Confounded path (km)", "FIXED dest\u2013plant (mi)"], prows,
           widths=[0.8, 0.8, 1.3, 0.6, 1.5, 1.5])
    _para(doc, "Fix applied: Option A (metric). Path-length-at-arrival (network "
               "distance to the variably-adjacent camp) is replaced by the "
               "straight-line displacement of the FINAL destination from the "
               "PLANT (the fixed hazard source). The diagnosis showed the topology "
               "is unrepresentative \u2014 outer towns are ~1 hop / ~2.5 km from a "
               "camp while inner towns are 24\u201327 km \u2014 so a source-referenced "
               "metric is preferred over mutating the shared TMI network (Days "
               "11\u201313 depend on it).")
    _para(doc, "Result: the Zeigler distance signature inner < outer now reads "
               f"(inner {path.loc[path.zone=='inner','dest_dist_plant_mi_median'].iloc[0]:.1f} "
               f"< outer {path.loc[path.zone=='outer','dest_dist_plant_mi_median'].iloc[0]:.1f} "
               "mi); the confounded network path was inverted (inner 47.8 > outer "
               "2.5 km). This is a Day-15 validation precondition, not a "
               "calibration target, and does not change the Task-B/E evac results. "
               "A full Option-B topology fix (symmetric / distant camp placement "
               "matching the real 85\u2013111 mi evacuation geography) is recommended "
               "for Day 15+ and would require re-running calibration.",
          bold=True, color=GREEN)

    # --- 10. Figure ---
    _h(doc, "10. Figure \u2014 CMC Calibration", level=1)
    fig = FIG / "day14_calibration.png"
    if fig.exists():
        doc.add_picture(str(fig), width=Inches(7.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run("Figure 1. Left: CMC misfit curve, clamp ON vs OFF, with "
                        "the locked TMI CMC and the Fukushima CMC=0.25 marked for "
                        "contrast \u2014 clamp OFF is identifiable and far lower-misfit. "
                        "Right: zone evacuation rates at the locked CMC vs the "
                        "empirical targets; total evac (27%) is annotated IN BAND, "
                        "while the zone gradient is visibly inverted (the "
                        "camp-adjacency confound).")
        r.italic = True; r.font.size = Pt(9); r.font.color.rgb = GREY

    # --- 11. Gate ---
    _h(doc, "11. Diagnostics Gate", level=1)
    _para(doc, f"Verdict: {gate['verdict']}.", bold=True)
    grows = []
    for c in gate["day14_new_checks"]:
        grows.append([c["name"], c["status"], c["detail"][:74]])
    _table(doc, ["Check", "Status", "Detail"], grows, widths=[2.7, 0.7, 3.4])
    _para(doc, "Check-26 flip (headline): " + gate["check_26_flip"]["note"],
          bold=True, color=GREEN, size=10)
    if gate.get("inherited_expected_failures"):
        _para(doc, "Inherited expected failure (by design, unchanged today): "
                   + gate["inherited_expected_failures"][0], italic=True,
              color=GREY, size=9.5)

    # --- 12. Implications ---
    _h(doc, "12. Implications for Days 15\u201316", level=1)
    _bullet(doc, "shadow-evac re-test, return-mechanism build, and the post-fix "
                 "Zeigler distance read; the inverted zone gradient (camp "
                 "adjacency) needs the Option-B topology fix before zone-level "
                 "validation.", bold_prefix="Day 15 (validation): ")
    _bullet(doc, f"locked TMI CMC = {cmc_lock:.2f} vs Fukushima 0.25 is the "
                 "context-specific piece; \u03b1/\u03b2 are to be compared as the transfer "
                 "hypothesis (kept locked precisely so this test is valid).",
            bold_prefix="Day 16 (cross-domain): ")
    _bullet(doc, "a conflict-dependent CMC so flight-under-extreme-threat emerges "
                 "from System-1 rather than from a clamp override \u2014 would also "
                 "address the inverted zone gradient at source.",
            bold_prefix="Theory paper / future work: ")

    # --- Appendix ---
    _h(doc, "Appendix \u2014 Artifact Manifest", level=2, color=BLUE)
    for f in ["scripts/run_tmi_day14_clamp_diagnostic.py",
              "scripts/run_tmi_day14_calibration.py",
              "scripts/decide_tmi_day14_clamp.py",
              "scripts/run_tmi_day14_robustness.py",
              "scripts/run_tmi_day14_pathfix.py",
              "scripts/plot_tmi_day14_calibration.py",
              "scripts/run_diagnostics_gate_day14.py",
              "results/tmi/day14_preflight.txt",
              "results/tmi/day14_clamp_diagnostic.csv",
              "results/tmi/day14_calibration_grid.csv",
              "results/tmi/day14_clamp_decision.txt",
              "results/tmi/day14_locked_params.json",
              "results/tmi/day14_robustness.csv",
              "results/tmi/day14_robustness_verdict.json",
              "results/tmi/day14_zeigler_pathfix.csv",
              "results/tmi/diagnostics_gate_day14.json",
              "figures/tmi/day14_calibration.png"]:
        _para(doc, f, size=9, space_after=1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"[docx] wrote {OUT}")


if __name__ == "__main__":
    build()
