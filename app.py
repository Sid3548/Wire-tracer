from flask import Flask, render_template, request, jsonify, send_file
import os
import pandas as pd
import fitz  # PyMuPDF
import base64
import io
from pathlib import Path
from utils import VectorTextProcessor, WireExtractorGemini

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/trace', methods=['POST'])
def trace_wires():
    try:
        data = request.json
        pdf_path = data.get('pdf_path')
        api_key = data.get('api_key')
        page = int(data.get('page'))
        from_token = data.get('from_token')
        to_token = data.get('to_token')
        model = data.get('model', 'gemini-2.0-flash-lite')
        
        if not all([pdf_path, api_key, page, from_token, to_token]):
            return jsonify({"error": "Missing required fields"}), 400
            
        if not Path(pdf_path).exists():
            return jsonify({"error": f"PDF not found: {pdf_path}"}), 404
        
        # Extract labels
        labels = VectorTextProcessor.extract_and_flip_text(pdf_path, page)
        if not labels:
            return jsonify({"error": "No text found on page"}), 400
        
        # Trace wires
        tracer = WireExtractorGemini(pdf_path, api_key)
        tracer.set_model(model)
        result = tracer.trace_wires_with_coordinates(page, from_token, to_token, labels)
        
        if "error" in result:
            return jsonify(result), 400
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_csv():
    try:
        data = request.json
        connections = data.get('connections', [])
        
        df = pd.DataFrame(connections)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='wire_connections.csv'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/preview', methods=['POST'])
def preview_page():
    try:
        data = request.json
        pdf_path = data.get('pdf_path')
        page = int(data.get('page', 1))
        
        if not Path(pdf_path).exists():
            return jsonify({"error": "PDF not found"}), 404
        
        # Use PyMuPDF to extract page image
        doc = fitz.open(pdf_path)
        page_obj = doc.load_page(page - 1)
        pix = page_obj.get_pixmap(dpi=150)  # Lower DPI for preview
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return jsonify({"success": True, "image": img_b64})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("="*60)
    print("WIRE TRACER FLASK APP")
    print("="*60)
    print("\nServer starting at http://127.0.0.1:5000")
    print("Press CTRL+C to stop\n")
    print("="*60)
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
