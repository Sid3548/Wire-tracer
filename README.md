# Wire Tracer: Hybrid Schematic Analysis Tool

**Wire Tracer** is a web-based application designed to automate the tedious process of verifying electrical connections in PDF schematics. By combining deterministic vector data extraction with the visual reasoning capabilities of Google's Gemini 2.0 Flash, this tool can "see" and "read" engineering drawings to trace wires from source to destination.

![Project Status](https://img.shields.io/badge/Status-Prototype-orange) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![AI](https://img.shields.io/badge/Powered%20by-Gemini%202.0-8E75B2)

## About the Project

Electrical engineers often spend hours manually tracing lines on PDF schematics to verify logic (e.g., "Does this wire go to the correct alarm contact?"). This tool attempts to solve that by:
1.  **Extracting Text:** Using `pdfplumber` to find label coordinates.
2.  **Visual Tracing:** Sending the specific coordinates and a simplified image to a Multimodal LLM (Gemini) to visually trace the black line connecting them.
3.  **Context Extraction:** Reading the descriptive text near the wire (e.g., "GCB OPEN" or "LOW GAS PRESSURE").

## A Note on Development & AI Assistance

**This project is a personal learning initiative.** I am currently learning Python and full-stack development. To bridge the gap between my engineering logic and the implementation code, I utilized AI coding assistants (LLMs) heavily during development. 

The AI acted as a "pair programmer," helping me:
* Structure the Flask backend and modularize the code.
* Write complex Regular Expressions (Regex) for text filtering.
* Debug JavaScript for the interactive frontend.

While the core logic and system design are mine, the code reflects a collaborative effort between a learning developer and modern AI tools. Feedback on code quality and structure is always welcome!

## Key Features

* **Hybrid Pipeline:** Uses standard Python libraries for text precision and AI for visual line tracing.
* **Vector Text Processing:** Automatically flips reversed text (common in schematics) and merges split labels (e.g., "X" + "01" becomes "X01").
* **Interactive UI:** A clean web interface to upload PDFs, set "From/To" search tokens, and view results.
* **Visual Preview:** Zoomable preview of the schematic page.
* **Data Export:** Export traced connections to CSV for documentation.

## Tech Stack

* **Backend:** Python, Flask
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **PDF Processing:** `pdfplumber` (text extraction), `PyMuPDF/fitz` (image rendering)
* **AI Model:** Google Gemini 2.0 Flash / Flash-Lite (via Google Generative AI SDK)

## Installation & Usage

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/yourusername/wire-tracer.git](https://github.com/yourusername/wire-tracer.git)
    cd wire-tracer
    ```

2.  **Install Dependencies**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    ```bash
    python app.py
    ```
PS. it is made on a notion that your pdf's are Vector pdf's and not imaged ones so please see to that while using.I do have another methord to read just via images the accuracy i have achieved is around 85-90% but this work does need manual check due to various factors which will make this rant go for too long!!

---
*Created by Siddharth J - 2025*
