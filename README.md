Academic Evaluation Criteria – Python

Formalizing academic evaluation criteria into explicit, reproducible Python rules.

Overview

This project implements rule-based evaluation logic for different types of academic assignments.

The objective is to transform implicit correction criteria into:

Transparent evaluation rules

Testable validation logic

Reusable scripts

Clear separation between automated checks and human judgment

The approach distinguishes between:

Technical rules

Formal requirements

Exceptions

Human judgment

Project Structure

The repository is organized by assignment type.

📌 BPMN

Contains Python scripts that formalize evaluation criteria for BPMN modeling exercises.

Although originally developed for a specific topic, the logic is designed to be adaptable to any BPMN assignment with defined evaluation rules.

Includes:

Rubric calculation scripts

Integration of technical and administrative criteria

Structured scoring logic

📌 Database

Contains Python scripts implementing rule-based evaluation for Database assignments.

Originally developed for a specific topic, the logic is structured to be adaptable to any database assignment with:

A canonical schema

Defined SQL requirements

Explicit correction criteria

Includes:

Schema comparison against canonical definitions

SQL validation

Integration of evaluation feedback

Design Philosophy

The core principle of this repository is:

Make evaluation criteria explicit, structured, and reproducible.

Each script focuses on separating:

What can be evaluated automatically

What requires interpretative or contextual academic judgment

This allows greater transparency, consistency, and methodological clarity in academic assessment.
