# RupeeRadar — Project Context

## Overview

RupeeRadar is an AI-powered personal finance assistant that helps users understand where their money is going by analyzing bank statement data. Professionals make hundreds of monthly transactions across UPI, cards, bank transfers, subscriptions, EMIs, rent, shopping, food delivery, travel, and investments — but bank statements are difficult to parse because transaction descriptions are messy, inconsistent, and hard to categorize manually.

The goal is to build an end-to-end solution that converts raw financial transaction data into meaningful personal finance insights.

## Core Objectives

The solution should help users answer questions like:
- What are my biggest spending categories?
- How much did I spend this month?
- Which transactions are recurring subscriptions or EMIs?
- What was my biggest transaction?
- What are the top insights from my spending behavior?

## Functional Requirements

1. **Data Ingestion** — Accept bank statement data as input (CSV, PDF, or other common formats).
2. **Transaction Extraction & Cleaning** — Parse and clean raw transaction data into a structured format (handling messy descriptions).
3. **Categorization** — Classify transactions into meaningful groups:
   - Food, Travel, Shopping, Bills, EMI, Subscriptions, Salary, Rent, Investments, Other
4. **Recurring Detection** — Identify recurring transactions (subscriptions, EMIs, rent, SIPs, insurance payments).
5. **Financial Metrics** — Calculate:
   - Total income
   - Total spend
   - Savings (income − spend)
   - Top spending categories
   - Biggest transactions
6. **Insight Generation** — Generate clear, human-readable spending insights using actual transaction amounts.
7. **Dashboard / Report** — Present the output through a simple UI, dashboard, or downloadable report.

## Expected Deliverables

- Cleaned transaction data display
- Categorized expenses view
- Recurring payment detection
- Spend summary dashboard
- At least 3 personalized financial insights
- A final report or visual summary that can be shared

## Evaluation Criteria

- Accuracy of transaction cleaning and categorization
- Quality of financial insights
- Ability to handle real-world messy transaction descriptions
- Simplicity and usefulness of the user experience
- Completeness of the end-to-end workflow
- Privacy-conscious handling of sensitive financial data

## Key Constraint

Priority is a **working end-to-end prototype** over perfect support for every bank format. The technology stack and implementation approach are open for the team to decide.

## Tech Stack Considerations (To Be Decided)

- **Frontend:** UI framework for the dashboard (React, Vue, Svelte, or vanilla HTML/CSS/JS)
- **Backend:** API layer (Node.js, Python/Flask/FastAPI, or serverless)
- **AI/ML:** LLM-based transaction categorization and insight generation (OpenAI, local model, or rule-based fallback)
- **Parsing:** CSV/PDF parsing libraries
- **Deployment:** Local-first or cloud-deployed

## Privacy

Financial data is highly sensitive. The solution should minimize data leaving the user's machine where possible, or ensure clear disclosure of data handling practices.

---

*Generated from docs/problemStatement.txt*
