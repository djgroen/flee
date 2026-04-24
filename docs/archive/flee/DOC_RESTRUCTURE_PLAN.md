# Documentation Restructure Plan

**Branch:** `docs/restructure` (flee and FabFlee repos)  
**Goal:** Merge flee + FabFlee docs into a single, well-structured site at https://flee.readthedocs.io  
**Audience:** Computer science students — intelligent but new to the codebase, varying programming levels  
**Date started:** April 2026

---

## Guiding principles

- "flee" is always lowercase, never "Flee" or "FLEE" in prose
- DFlee (disaster use case, flood_levels) is presented as distinct from the conflict use case
- All figures live in `docs/Figs/` (not `docs/images/`)
- No content is deleted — everything is first moved to `docs/archive/`
- Many small focused pages, not long scrolling pages
- FabFlee docs are incorporated into this single site; the FabFlee `doc/` folder is then retired
- A `dev/` section is included for developers

---

## Phase 1 — Branches and plan ✅

- [x] `git checkout -b docs/restructure` on flee repo
- [x] `git checkout -b docs/restructure` on FabFlee repo
- [x] This plan document

---

## Phase 2 — Archive ✅

Copy all existing content to `docs/archive/` so nothing is lost.

- `docs/archive/flee/` — original flee docs (all `*.md` from `docs/`)
- `docs/archive/fabflee/` — FabFlee `doc/` folder contents
- `docs/archive/README.md` — note that these are superseded by the new structure

---

## Phase 3 — New directory structure

```
docs/
├── Figs/                               # ALL figures (moved from images/ + FabFlee doc/)
├── archive/                            # Archived originals (do not edit)
├── index.md                            # Site home page
│
├── getting-started/
│   ├── index.md                        # What is flee? Quick orientation
│   ├── installation.md                 # Install flee (from Installation_and_Testing.md)
│   ├── quick-start.md                  # Run your first simulation in <10 mins
│   └── testing.md                      # Run the test suite
│
├── concepts/
│   ├── index.md                        # Conceptual overview of the model
│   ├── agent-based-model.md            # How the ABM works
│   ├── location-types.md               # From Types_of_location_graphs.md
│   └── conflict-vs-disaster.md         # Conflict vs DFlee use cases explained
│
├── conflict/                           # Conflict displacement use case
│   ├── index.md                        # Overview
│   ├── data-sources.md                 # ACLED, UNHCR, population databases
│   ├── locations.md                    # Building locations.csv
│   ├── routes.md                       # Building routes.csv
│   ├── conflict-schedule.md            # conflicts.csv
│   ├── camps.md                        # Camp data
│   ├── validation-data.md              # Source data for validation
│   └── input-file-generator.md         # From Input_File_generator.md
│
├── dflee/                              # DFlee disaster use case
│   ├── index.md                        # What is DFlee? (distinct from conflict)
│   ├── overview.md                     # From Using_DFlee_For_Disaster_Driven_Displacement.md
│   ├── data-files.md                   # From DFlee_Data_Files.md
│   ├── food-security.md                # From Food_Security_Mechanisms.md
│   └── construction.md                 # How to set up a DFlee scenario
│
├── running/
│   ├── index.md                        # Overview of running simulations
│   ├── local.md                        # From Simulation_instance_execution.md
│   ├── settings-basic.md               # From Simulation_settings_basic.md (split: log, spawn, move)
│   ├── settings-move.md                # Movement rule parameters
│   ├── settings-optimisation.md        # Optimisation parameters
│   ├── settings-reference.md           # Full reference from Simulation_settings_reference.md
│   └── output.md                       # From Output_file_descriptions.md
│
├── advanced/
│   ├── index.md
│   ├── ensemble.md                     # From Flee_Ensemble.md
│   ├── multiscale.md                   # From Multiscale_Simulation_instance_construction.md
│   ├── sensitivity.md                  # From Sensitivity_analysis_of_parameters_using_EasyVVUQ.md
│   └── camp-capacity.md                # From Camp_Capacity_Explained.md
│
├── fabflee/                            # FabFlee / FabSim3 plugin
│   ├── index.md                        # What is FabFlee? Why use it?
│   ├── setup.md                        # Installing FabFlee + FabSim3 (from TutorialSetup.md)
│   ├── running-local.md                # Single run locally (from Tutorial.md)
│   ├── construction.md                 # Building scenarios with FabFlee (TutorialConstuct.md)
│   ├── validation.md                   # Validating runs (TutorialValidate.md)
│   ├── ensemble.md                     # Ensemble runs (from FabFlee.md ensemble section)
│   ├── hpc.md                          # HPC / supercomputer (Remote_execution + FabFlee.md HPC)
│   ├── sensitivity.md                  # EasyVVUQ sensitivity analysis (TutorialSensitivity.md)
│   ├── multiobjective.md               # Multi-objective optimisation (TutorialMOO.md)
│   ├── multiscale.md                   # Coupled / multiscale (from FabFlee.md + TutorialAdvanced.md)
│   └── qcg-pilot.md                    # QCG Pilot Job (from FabFlee.md QCG section)
│
├── dev/                                # Developer section
│   ├── index.md                        # Overview for developers
│   ├── contributing.md                 # From contributing.md
│   ├── architecture.md                 # Code architecture overview
│   ├── testing.md                      # Running / writing tests
│   ├── adding-features.md              # How to add new features / use cases
│   └── roadmap.md                      # Planned work
│
├── code-reference/                     # API auto-docs (from code_reference/)
│   ├── index.md
│   ├── flee/
│   ├── pflee/
│   └── multiscale/
│
└── about/
    ├── credits.md                      # From credits.md
    ├── literature.md                   # From Flee_Literature.md
    └── changelog.md                    # New
```

---

## Phase 4 — mkdocs.yml nav update

The `mkdocs.yml` `nav:` section will be rewritten to match the new structure. The site name stays `flee` (lowercase in the title). The `docs_dir` remains `docs/`.

---

## Phase 5 — Content population (can span multiple sessions)

Pages to write/split, in priority order:

| Priority | Page | Source |
|----------|------|--------|
| 1 | `getting-started/installation.md` | `Installation_and_Testing.md` (install section) |
| 1 | `getting-started/testing.md` | `Installation_and_Testing.md` (test section) |
| 1 | `getting-started/quick-start.md` | New — short worked example |
| 1 | `getting-started/index.md` | New intro |
| 2 | `concepts/` all pages | `Types_of_location_graphs.md` + new writing |
| 2 | `conflict/locations.md` | `Simulation_instance_construction.md` pt 1 |
| 2 | `conflict/routes.md` | `Simulation_instance_construction.md` pt 2 |
| 2 | `conflict/conflict-schedule.md` | `Simulation_instance_construction.md` pt 3 |
| 2 | `conflict/camps.md` | `Simulation_instance_construction.md` pt 4 |
| 2 | `conflict/validation-data.md` | `Simulation_instance_construction.md` pt 5 |
| 2 | `conflict/input-file-generator.md` | `Input_File_generator.md` |
| 3 | `dflee/` all pages | DFlee docs |
| 3 | `running/` all pages | Settings + execution docs |
| 4 | `advanced/` all pages | Ensemble, multiscale, sensitivity, camp capacity |
| 4 | `fabflee/` all pages | FabFlee docs |
| 5 | `dev/` all pages | contributing + new |
| 5 | `about/` | credits, literature |

---

## Phase 6 — Cleanup

- Remove/retire FabFlee `doc/` folder (it moves to `docs/archive/fabflee/` in flee)
- Remove old `docs/images/` (contents moved to `docs/Figs/`)
- Remove old flat docs (now in `archive/flee/`)
- Fix all internal links across pages
- Fix `mkdocs.yml` nav to match final state
- Check: "flee" is never capitalized in prose across all pages
- Check: all figures reference `../Figs/filename.png` (or correct relative path)
- Add a note in FabFlee repo pointing users to flee.readthedocs.io

---

## Capitalization audit

Search and replace across all new docs:
- `FLEE` → `flee` (in prose, keep in code blocks / git URLs)
- `Flee` → `flee` (in prose, keep at sentence starts carefully)
- Note: `FabFlee` stays as-is (it's a proper tool name), `DFlee` stays as-is

---

## Notes on content accuracy

Files that are known to be old or potentially inaccurate:
- `FabFlee_Automated_Flee_based_simulation.md` — contains old FabFlee command syntax; cross-check against current FabFlee plugin code
- `OldSingleModelTutorial.md` — explicitly old, archive only
- `FabFlee.md` (in FabFlee/doc/) — comprehensive but verbose; split and verify commands
- `Remote_execution_on_a_supercomputer.md` — verify ARCHER2 / HPC instructions still current
- Any VECMA-era references (VECMAtk) — update or note as historical context

---

## Session log

- Session 1 (Apr 2026): Branches created, plan written, archive and structure stubs created, mkdocs.yml updated, getting-started + concepts + conflict + dflee pages populated.
