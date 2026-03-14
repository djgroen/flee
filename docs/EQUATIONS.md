# S1/S2 Model: Equations and Code Reference

Use this document to verify equations against implementation and to cite code in write-ups.

---

## 1. Cognitive capacity Ψ

**Equation:**
$$\Psi(x; \alpha) = \Psi_{\min} + (1 - \Psi_{\min})(1 - e^{-\alpha x})$$

**Code:** `flee/s1s2_model.py`, `compute_capacity()`

```python
return PSI_MIN + (1.0 - PSI_MIN) * (1.0 - math.exp(-alpha * max(0.0, experience_index)))
```

**Constants:** `PSI_MIN = 0.1`

---

## 2. Structural opportunity Ω

**Equation:**
$$\Omega(c; \beta) = e^{-\beta c}$$

**Code:** `flee/s1s2_model.py`, `compute_opportunity()`

```python
return math.exp(-beta * max(0.0, min(1.0, conflict_intensity)))
```

---

## 3. Deliberation weight P_S2

**Equation:**
$$P_{S2} = \Psi \times \Omega$$

**Code:** `flee/s1s2_model.py`, `compute_deliberation_weight()`

```python
return compute_capacity(experience_index, alpha) * compute_opportunity(conflict_intensity, beta)
```

**Usage:** `flee/moving.py`, `calculateMoveChance()` line ~252

---

## 4. S2 move probability σ

**Equation:**
$$\sigma = \frac{1}{1 + \exp\left(-\kappa \frac{c_{\text{here}} - c_{\text{best}}}{d_{\text{best}}}\right)}$$

**Code:** `flee/s1s2_model.py`, `compute_s2_move_probability()`

```python
safety_signal = kappa * (conflict_here - conflict_best) / distance_best
safety_signal = max(-20.0, min(20.0, safety_signal))
return 1.0 / (1.0 + math.exp(-safety_signal))
```

**Usage:** `flee/moving.py`, `calculateMoveChance()` lines ~259–264 (c_best, d_best from best neighbor)

---

## 5. Blended move probability

**Equation:**
$$P_{\text{move}} = (1 - P_{S2}) \cdot P_{S1} + P_{S2} \cdot \sigma$$

**Code:** `flee/moving.py`, `calculateMoveChance()` line ~267

```python
blended_movechance = (1.0 - s2_weight) * movechance + s2_weight * sigma
```

---

## 6. High-conflict override

**Equation:** If $c > 0.9$: $P_{\text{move}} \leftarrow \max(P_{\text{move}}, 0.95)$

**Code:** `flee/moving.py`, lines ~269–270

```python
if conflict > 0.9:
    blended_movechance = max(blended_movechance, 0.95)
```

---

## Files to upload for equation verification

1. **flee/s1s2_model.py** — Equations 1–4
2. **flee/moving.py** — Equations 5–6, integration (lines ~237–280)
