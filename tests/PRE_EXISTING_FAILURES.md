# Pre-existing test failures (not introduced by dual-process PR)

The following tests fail with `FileNotFoundError: empty.yml` when run from project root.
**Root cause:** Tests call `ReadFromYML("empty.yml")` expecting `empty.yml` in the current
working directory. `tests/empty.yml` exists, but FLEE tests conventionally expect
`empty.yml` in the project root.

**Evidence:** All 26 failures show the identical error. This is a pre-existing FLEE
test environment dependency, not introduced by Prompts 1–9.

## Affected tests (26)

| File | Tests |
|------|-------|
| test_1_agent.py | test_1_agent |
| test_awareness.py | test_awareness, test_marker_location |
| test_camp_sink.py | test_camp_sink |
| test_close_location.py | test_close_location |
| test_conflict_driven_spawning.py | test_conflict_driven_spawning, test_conflict_driven_spawning_post_conflict |
| test_crawling.py | test_location_crawling_4loc |
| test_csv.py | test_location_changes, test_csv |
| test_dflee.py | test_read_flood_csv, test_flood_level_location_attribute, test_flood_forecaster, test_agent_flood_awareness |
| test_flood_driven_spawning.py | test_flood_driven_spawning |
| test_load_agent.py | test_load_agent |
| test_micro_model.py | test_micro_model |
| test_moving.py | test_stay_close_to_home, test_stay_close_to_home_fixed_routes, test_scoring_foreign_weight |
| test_path_choice.py | test_path_choice |
| test_removelink.py | test_removelink |
| test_spawning.py | test_get_attribute_ratio |
| test_tiny_closure.py | test_tiny_closure |
| test_toy_escape.py | test_toy_escape, test_toy_escape_start_empty |

## Workaround

Create a symlink from project root: `ln -s tests/empty.yml empty.yml`
Or copy: `cp tests/empty.yml empty.yml`

## Fixed in this PR

- **test_demographics.py:** Resolved 2 ERRORS (not failures). The `setup()` function
  conflicted with pytest's xUnit-style setup hook, causing `TypeError` when pytest
  passed the module as the `yaml` parameter. Renamed to `_make_demographics_ecosystem`
  and added fallback path for empty.yml.
