# Wire Tracer

A hybrid pipeline tool for electrical engineering schematics. It combines vector extraction (using `pdfplumber`) for precise coordinate mapping with AI vision (using Google Gemini 2.0) to trace wires and extract contextual descriptions.

## Features
- **Vector Text Extraction:** Identifies and flips component labels from PDFs.
- **AI Visual Tracing:** Uses Gemini Vision to trace lines between verified coordinates.
- **Interactive UI:** Flask-based web interface for uploading PDFs, setting tokens, and visualizing results.
- **Export:** Download connections as CSV.

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
