# DCF Valuation Automation Platform | Python, React

## Overview

This project is an interactive DCF valuation platform that converts spreadsheet-based valuation logic into a Python and React application. It allows users to adjust key assumptions, generate forecast schedules, compare perpetuity and exit-multiple valuation methods, run sensitivity analysis, and visualize valuation outputs in a dashboard-style interface.

## Key Features

- Interactive DCF dashboard with perpetuity and multiple-based valuation outputs
- Workbook-style inputs sheet for valuation assumptions
- Revenue, cost, income statement, working capital, depreciation, asset, tax, and UFCF schedules
- Sensitivity analysis for WACC, terminal growth, and terminal multiple
- Company/ticker input workflow for market-data-driven assumptions
- Visual dashboard with charts and summary boxes

## Tech Stack

- Python
- FastAPI
- React
- Recharts
- AG Grid
- yFinance

## Architecture

- **Backend:** FastAPI valuation engine and company data endpoints
- **Frontend:** React dashboard with workbook-style tabs and analytics views
- **Data Layer:** Static DCF model assumptions plus ticker-based market data integration


## Screenshots

<img width="3766" height="1986" alt="image" src="https://github.com/user-attachments/assets/8289b710-8db8-4e4e-a987-f5226b65a253" />


<img width="3772" height="1430" alt="image" src="https://github.com/user-attachments/assets/420a41df-2ee9-401d-b1b8-e21d1211a783" />


<img width="3758" height="1866" alt="image" src="https://github.com/user-attachments/assets/a2e058bb-94bb-4827-ab12-1869a2c34681" />

### Future improvements

- Export valuation outputs to Excel and PDF
- Deploy frontend and backend for live demo access
- Add real financial statement ingestion
- Extend ticker-based model prefill with historical revenue and EBITDA
