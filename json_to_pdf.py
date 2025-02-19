import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from textwrap import wrap

def json_to_pdf(json_files, output_dir="output_pdfs"):
    os.makedirs(output_dir, exist_ok=True)

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        pdf_filename = os.path.join(output_dir, os.path.basename(json_file).replace(".json", ".pdf"))
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 10)
        
        y_position = height - 40  # Start position for text
        line_height = 14  # Line spacing

        def draw_text(text, indent=0):
            """Draws text on the canvas with automatic wrapping and pagination."""
            nonlocal y_position
            
            max_width = width - 80  # Account for margins
            wrapped_lines = wrap(text, width=int(max_width / 6))  # Wrap text
            
            for line in wrapped_lines:
                if y_position < 40:  # Start a new page if out of space
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - 40
                
                c.drawString(40 + indent * 20, y_position, line)
                y_position -= line_height

        draw_text(f"JSON File: {os.path.basename(json_file)}")
        draw_text("=" * 60)

        def format_json(obj, indent=0):
            """Recursively formats JSON data into readable text with proper indentation."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    draw_text(f"{key}:", indent)
                    format_json(value, indent + 1)
            elif isinstance(obj, list):
                for index, item in enumerate(obj):
                    draw_text(f"- Item {index + 1}:", indent)
                    format_json(item, indent + 1)
            else:
                draw_text(str(obj), indent)

        format_json(data)
        c.save()

        print(f"Converted {json_file} → {pdf_filename}")

# Example usage
json_files = ["./competitors/competitors_data.json", "./web_search/analyst_reports.json", "./web_search/earnings_transcripts.json", "./specific/sec_financial_data.json", "./specific/yahoo_results.json"] 
json_to_pdf(json_files)
