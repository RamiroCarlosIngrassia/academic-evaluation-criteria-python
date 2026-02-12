Academic Evaluation Criteria – Python

Formalizing academic evaluation criteria into explicit, reproducible Python rules.

This project implements rule-based evaluation logic for different types of academic assignments, separating:

Technical rules

Formal requirements

Exceptions

Human judgment

The objective is to transform implicit correction criteria into transparent, testable, and reusable evaluation scripts.

Project Structure
academic-evaluation-criteria-python/
│
├── bpmn/
│   ├── scripts for BPMN evaluation
│   └── README.md
│
├── database/
│   ├── scripts for database evaluation
│   └── README.md
│
└── README.md

Modules
📌 bpmn/

Contains Python scripts that formalize evaluation criteria for BPMN modeling exercises.

Although originally designed for a specific assignment or topic, the logic is structured to be adaptable to:

Any BPMN exercise

Any canonical process model

Any defined rubric structure

Focus areas include:

Structural validation

Rubric-based scoring

Integration of administrative and technical criteria

📌 database/

Contains Python scripts for rule-based evaluation of Database assignments.

The logic supports:

Comparison against a canonical schema

SQL validation

Integration of schema and query feedback

Rubric-based scoring

Although initially developed for a specific topic, the structure is adaptable to any database assignment with a defined canonical reference.

Methodological Principles

This project is based on three core principles:

Explicitness
Evaluation rules must be clearly defined and codified.

Reproducibility
The same input must always produce the same evaluation result.

Separation of concerns
Distinguish between:

Automatic rule validation

Exceptions

Context-dependent academic judgment

The scripts are not meant to replace human evaluation, but to formalize and stabilize the technical component of grading.

Educational Context

This repository reflects a broader objective:

Transform correction criteria from tacit knowledge into structured, computational rules.

It is especially useful in contexts where:

Large numbers of assignments must be evaluated

Rubrics must be consistently applied

Transparency in grading is required

Feedback should be partially automated
