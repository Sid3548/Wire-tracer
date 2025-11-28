import pdfplumber
import fitz  # PyMuPDF
import re
import json
import base64
import requests
import urllib3

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VectorTextProcessor:
    @staticmethod
    def extract_and_flip_text(pdf_path, page_num, x_tolerance=3, y_tolerance=3):
        print(f"\n🔧 Mining vector data from Page {page_num}...")
        extracted_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < 1 or page_num > len(pdf.pages):
                    print(f"❌ Page {page_num} out of range.")
                    return []
                
                page = pdf.pages[page_num - 1]
                words = page.extract_words(x_tolerance=x_tolerance, y_tolerance=y_tolerance, keep_blank_chars=False)
                
                for w in words:
                    raw_text = w['text']
                    flipped_text = raw_text[::-1]
                    
                    center_x = w['x0'] + (w['width'] / 2)
                    center_y = w['top'] + (w['height'] / 2)
                    bbox = [int(w['x0']), int(w['top']), int(w['x1']), int(w['bottom'])]

                    extracted_data.append({
                        "text": flipped_text,
                        "raw_text": raw_text, 
                        "x": int(center_x),
                        "y": int(center_y),
                        "bbox": bbox
                    })
            
            final_data = VectorTextProcessor.merge_numbers(extracted_data)
            print(f"✅ Found {len(final_data)} labels (Flipped & Merged).")
            return final_data
            
        except Exception as e:
            print(f"❌ Vector Extraction Failed: {e}")
            return []

    @staticmethod
    def merge_numbers(items):
        terminals = []
        numbers = []
        others = []

        for item in items:
            txt = item['text'].strip()
            if re.match(r'^\d+[A-Z]?$', txt): numbers.append(item)
            elif 1 < len(txt) < 8 and txt.isupper(): terminals.append(item)
            else: others.append(item)

        merged_output = list(others) + list(numbers) 

        for term in terminals:
            best_match = None
            min_dist = 1000 
            SEARCH_R_X = 80 
            SEARCH_R_Y = 60 

            for num in numbers:
                dx = abs(term['x'] - num['x'])
                dy = abs(term['y'] - num['y'])
                
                if (dy < 10 and dx < SEARCH_R_X) or (dx < 10 and dy < SEARCH_R_Y):
                    dist = dx + dy
                    if dist < min_dist:
                        min_dist = dist
                        best_match = num

            if best_match:
                new_text = f"{best_match['text']}-{term['text']}"
                term['text'] = new_text
                merged_output.append(term)
            else:
                merged_output.append(term)

        return merged_output

    @staticmethod
    def get_coordinates_for_gemini(all_labels, from_token, to_token):
        from_token = from_token.upper().strip()
        to_token = to_token.upper().strip()
        from_list = []
        to_list = []
        for item in all_labels:
            if from_token in item['text'].upper(): from_list.append(item)
            elif to_token in item['text'].upper(): to_list.append(item)
        return from_list, to_list

class WireExtractorGemini:
    def __init__(self, pdf_path: str, api_key: str):
        self.pdf_path = pdf_path
        self.api_key = api_key
        self.model_name = "gemini-2.0-flash-lite" 
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def set_model(self, model_name):
        self.model_name = model_name
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def get_page_image_b64(self, page_num, dpi=300):
        try:
            doc = fitz.open(self.pdf_path)
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            print(f"❌ Image Error: {e}")
            return None

    def trace_wires_with_coordinates(self, page_num, from_token, to_token, known_labels):
        from_points, to_points = VectorTextProcessor.get_coordinates_for_gemini(known_labels, from_token, to_token)
        
        if not from_points or not to_points:
            return {"error": "Label mismatch - check FROM/TO tokens"}

        img_b64 = self.get_page_image_b64(page_num)
        if not img_b64: return {"error": "Failed to extract page image"}

        prompt_text = f"""
        You are an expert electrical engineer verifying a schematic.
        I am providing verified start/end coordinates (x,y).

        TASK:
        1. Trace the black line from each 'FROM' coordinate to the valid 'TO' coordinate.
        2. EXTRACT CONTEXTUAL TEXT. The text is often floating NEAR the wire, not touching it.

        INPUT DATA:
        - FROM_POINTS: {json.dumps([{'text': p['text'], 'x': p['x'], 'y': p['y']} for p in from_points])}
        - TO_POINTS: {json.dumps([{'text': p['text'], 'x': p['x'], 'y': p['y']} for p in to_points])}

        CRITICAL DESCRIPTION RULES:
        - If the wire connects to a Component Tag (e.g., "Q00", "Q51"), look ABOVE, BELOW, or TO THE SIDE of that tag for the Function Text (e.g., "GCB OPEN", "ES CLOSE").
        - Combine them! Example: Do not return "Q00". Return "Q00 GCB OPEN".
        - If the wire goes to an Alarm Box, read the text inside the box (e.g., "LOW GAS PRESSURE").
        - If the wire hits a coil/contact, looks for the identifier (e.g. "TC-1").
        - If you see a "None" description, look harder in a 100-pixel radius around the connection point.

        OUTPUT FORMAT (JSON ONLY):
        [
          {{ "from": "Label_Name", "to": "Label_Name", "description": "TAG + FUNCTION" }},
          ...
        ]
        """

        payload = {
            "contents": [{"parts": [{"text": prompt_text}, {"inline_data": {"mime_type": "image/png", "data": img_b64}}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192, 
                "response_mime_type": "application/json"
            }
        }

        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
                verify=False
            )
            
            if response.status_code != 200:
                return {"error": f"API Error {response.status_code}"}

            result = response.json()
            try:
                raw_json = result['candidates'][0]['content']['parts'][0]['text']
                if "```json" in raw_json: raw_json = raw_json.split("```json")[1].split("```")[0]
                elif "```" in raw_json: raw_json = raw_json.split("```")[1].split("```")[0]
                return {"success": True, "connections": json.loads(raw_json)}
            except Exception:
                return {"error": "Failed to parse API response"}

        except Exception as e:
            return {"error": f"Network error: {str(e)}"}
