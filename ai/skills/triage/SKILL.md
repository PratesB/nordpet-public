---
name: triage
description: Clinical triage skill for veterinary clinical. Classifies patient urgency into GREEN, YELLOW, ORANGE, or RED based on structured clinical inputs from the Triage model (heart rate, respiratory rate, temperature, weight, complaint, notes, and species via Animal relation). Always used when a Triage record is created or when risk_level must be inferred or recalculated.
---

# Triage — Risk Classification System

## Overview

This skill performs automated clinical triage classification for veterinary patients using structured data coming directly from the system database.

It classifies the patient into one of four urgency levels:

- 🔴 **RED** — Emergency (immediate life-threatening condition)
- 🟠 **ORANGE** — Urgent (risk of rapid deterioration, care within 10 minutes)
- 🟡 **YELLOW** — Less urgent (stable but requires medical attention within 30 minutes)
- 🟢 **GREEN** — Non-urgent (routine consultation / elective care)

---

## Input Data (From Triage Model)

This skill does NOT request missing data. All values are assumed to come directly from the database.

### Required fields:

| Field | Source | Description |
|------|--------|-------------|
| species | Animal model | Species of the patient (dog, cat, bird, reptile, rabbit, hamsters, other) |
| weight | Triage.weight | Weight in kg |
| heart_rate | Triage.heart_rate | Heart rate (bpm) |
| respiratory_rate | Triage.respiratory_rate | Respiratory rate (rpm) |
| temperature | Triage.temperature | Body temperature (°C) |
| complaint | Triage.complaint | Chief complaint from tutor |
| notes | Triage.notes | Clinical observations from triage staff |

---

## Species Handling

Supported species (via Animal model):

- dog  
- cat  
- bird  
- reptile  
- rabbit  
- hamsters  
- other  

If species-specific vitals are unknown or unreliable (ex: exotic animals), apply conservative escalation (bias toward higher severity).

---

## Clinical Logic

Classification follows a hierarchical severity system:

> RED overrides ORANGE, ORANGE overrides YELLOW, YELLOW overrides GREEN.

---

## 🔴 RED — Emergency

Assign RED if ANY of the following are present:

### Vital signs
- Severe bradycardia or tachycardia outside safe physiological limits
- Respiratory distress (severe dyspnea, open-mouth breathing in non-panting species)
- Temperature > 41.0°C or < 36.0°C (mammals/birds)

### Clinical conditions
- Cardiorespiratory arrest or suspicion
- Active seizures or unconsciousness
- Severe trauma (vehicle accident, major fall, inter-animal attack)
- Active uncontrolled hemorrhage
- Cyanosis or severe hypoxia signs
- Severe abdominal distension with pain (suspected torsion)
- Organ prolapse
- Toxic ingestion with clinical signs
- Shock (pale mucosa + prolonged CRT + tachycardia + hypothermia)
- CRT > 4 seconds
- Non-responsive animal

---

## 🟠 ORANGE — Urgent

Assign ORANGE if ANY of the following are present (and not RED):

### Vital signs
- Significant tachycardia/bradycardia for species
- RR 45–60 rpm (or severe abnormal breathing pattern)
- Temperature 40.1–41.0°C or 36.0–36.9°C

### Clinical conditions
- Hematemesis, melena, hematochezia
- Moderate trauma or fractures
- Severe abdominal pain
- Urinary obstruction (>12h, especially male cats → always ORANGE minimum)
- Foreign body ingestion with obstruction signs
- High-risk toxin ingestion (no symptoms yet)
- Recent seizure (<1h, recovered)
- Proptosis
- Anaphylaxis signs
- Severe dehydration (>8%)
- Marked lethargy or collapse

---

## 🟡 YELLOW — Less Urgent

Assign YELLOW if ANY of the following are present (and no RED/ORANGE):

### Vital signs
- Mild deviations from normal species ranges
- RR 36–44 rpm
- Mild fever or mild hypothermia

### Clinical conditions
- Persistent vomiting (>3 episodes/24h without blood)
- Diarrhea without blood
- Mild/moderate pain
- Minor wounds without bleeding risk
- Coughing or mild respiratory signs
- Anorexia (>24h dogs, >12h cats)
- Mild dehydration (5–8%)
- Mild mucosal pallor
- CRT 2–3 seconds
- Stable but abnormal behavior

---

## 🟢 GREEN — Non-Urgent

Assign GREEN when:

### Vital signs
- All parameters within normal physiological range for species

### Clinical conditions
- Routine check-up
- Vaccination or preventive care
- Chronic stable conditions (dermatology, otitis without pain)
- Mild chronic lameness
- Elective procedures (spay/neuter)
- Minor complaints without systemic signs
- Alert, active, stable, hydrated patient

---

## Decision Rules

1. Clinical complaint overrides vitals if high-risk (e.g. toxin ingestion, trauma, seizures)
2. Combine multiple YELLOW findings → escalate to ORANGE
3. Uncertain cases → always escalate one level higher
4. Exotic species (bird, reptile, hamster, other) → conservative escalation recommended
5. Male cats with urinary obstruction → minimum ORANGE
6. Young/elderly animals → lower physiological reserve → consider escalation

---

## Output Format

Return ONLY one lowercase word:

- `green`
- `yellow`
- `orange`
- `red`

### Strict rules:
- No explanation
- No punctuation
- No extra text
- Single word only

If explanation is required later, it can be derived separately via audit module (RF06).