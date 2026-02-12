# Academic Evaluation Criteria – Python

Formalizing academic evaluation criteria into explicit, reproducible Python rules.

---

## Overview

This project implements rule-based evaluation logic for different types of academic assignments.  

The objective is to transform implicit correction criteria into:

- **Transparent evaluation rules**
- **Testable validation logic**
- **Reusable scripts**
- **Clear separation between automated checks and human judgment**

The approach distinguishes between:

- Technical rules  
- Formal requirements  
- Defined exceptions  
- Human judgment (when automation is not appropriate)

---

## Project Structure

The repository is organized into modules according to assignment type:

### 📂 `database/`

Contains Python scripts that formalize evaluation criteria for Database assignments.

Although some scripts were originally developed for a specific topic, the logic is designed to be adaptable to any database assignment with:

- A defined canonical schema
- Explicit evaluation rules
- Structured student submissions

### 📂 `bpmn/`

Contains Python scripts implementing rule-based evaluation for BPMN modeling exercises.

Even when initially created for a particular exercise or topic, the structure is intended to be reusable for any BPMN assignment with:

- Clearly defined modeling criteria
- Formal validation rules
- Explicit rubric structure

---

## Design Philosophy

The core principle of this project is the separation of:

1. **Objective, automatable validation**
2. **Interpretative or pedagogical judgment**

By formalizing technical and structural rules in code, the evaluation process becomes:

- More consistent  
- More transparent  
- Easier to audit  
- Easier to refine over time  

This repository is not just a collection of scripts — it is a methodology for transforming academic correction criteria into explicit, reproducible systems.

---

## Scope

While specific examples may reference particular topics or exercises, the architecture is intentionally generic and adaptable to new assignments, new rubrics, and new academic contexts.
