from flask import Flask, request, jsonify, send_file
from fpdf import FPDF
import pandas as pd
import os
import logging
from flask_cors import CORS

# Inisialisasi Flask
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Fungsi untuk membaca dataset
DATASET_PATH = "dataset\information_data_run10-13.xlsx"  # Ganti dengan path dataset Anda
try:
    dataset = pd.read_excel(DATASET_PATH)
    logging.info(f"Dataset loaded successfully with columns: {dataset.columns}")
except Exception as e:
    logging.error(f"Failed to load dataset: {e}")
    dataset = pd.DataFrame()

# ACMG Interpretation Columns
def get_acmg_interpretation(row):
    acmg_data = row.get('acmg_criteria', '')  # Gets value as string, '' default if missing
    interpretations = acmg_data.split(", ") if acmg_data else []  # Split into individual interpretations
    formatted_interpretation = []

    for interpretation in interpretations:
        if ":" in interpretation and "(" in interpretation and ")" in interpretation:
            parts = interpretation.split(": ")  # Split into key-value
            key = parts[0]  # Key like "PVS_score"
            value_rationale = parts[1].split(" (")  # Split value and rationale
            value = value_rationale[0]  # Score
            rationale = value_rationale[1][:-1]  # Rationale without the ")"
            formatted_interpretation.append(f"{key}: {value} ({rationale})")  # Append formatted interpretation

    if formatted_interpretation:
        return "\n".join(formatted_interpretation)  # Join the interpretations
    else:
        return "No ACMG interpretation available."  # Return fallback message if no interpretations found

class CustomPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_path = "asset\logo-bio.png"  # Path ke file logo organisasi

    def header(self):
        if self.page_no() == 1:
            # Tambahkan logo di pojok kiri
            if os.path.exists(self.logo_path):
                self.image(self.logo_path, x=10, y=10, w=30)  # x, y, width (height dihitung otomatis)
            else:
                logging.warning(f"Logo file not found at {self.logo_path}")

            # Judul laporan
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Variant Analysis Report', 0, 1, 'C')
        else:
            self.set_font('Arial', '', 8)
            self.cell(0, 10, '', 0, 1)

    def add_patient_info(self, patient_info):
        self.set_font('Arial', '', 10)
        for label, value in patient_info.items():
            self.cell(0, 8, f"{label}: {value}", 0, 1)

    def add_generated_version(self, version):
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f"Generated Version: {version}", 0, 1, 'R')
        self.ln(5)

    def add_title(self, title):
        self.set_font('Arial', 'B', 13)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(1)

    def add_styled_title(self, title):
        self.set_fill_color(211, 211, 211)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 12)
        self.rect(15, self.get_y(), 180, 10, 'F')
        self.set_xy(15, self.get_y() + 2)
        self.cell(0, 6, title, 0, 1, 'L')
        self.ln(5)

    def add_paragraph(self, text):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, str(text))
        self.ln()

    def add_table(self, data, col_widths, col_headers):
        self.set_font('Arial', 'B', 10)
        for header, width in zip(col_headers, col_widths):
            self.cell(width, 10, str(header), 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 8)
        for row in data:
            for item, width in zip(row, col_widths):
                self.cell(width, 10, str(item) if pd.notna(item) else '', 1, 0, 'C')
            self.ln(15)

    def add_bullet_points(self, items, bullet="•"):
        self.set_font('Arial', '', 10)
        if bullet == "\u2022":
            bullet = "*"
        for item in items:
            self.multi_cell(0, 5, f"{bullet} {item}")
        self.ln(2)

# Fungsi untuk menghasilkan data JSON
def generate_json(variant, dataset):
    row = dataset[dataset["Uploaded_variation"] == variant]

    if row.empty:
        return None

    variant_row = row.iloc[0]
    acmg_interpretation = get_acmg_interpretation(variant_row)

    report_data = {
        "variant": variant,
        "patient_info": {
            "Name": "John Doe",
            "Date of Birth": "12/01/1987",
            "Sex": "Male",
            "Test Ordered By": "Dr. Fulan, Amazing Hospital Centre"
        },
        "executive_summary": variant_row.get("Summary", "No explanation available."),
        "testing_material_and_methods": variant_row.get("method", "No Methods available"),
        "acmg_interpretation": acmg_interpretation,
        "recommendation": variant_row.get("recommendation", "No recommendation available."),
        "counselors_note": variant_row.get("counselor's note", "No Counselor's Note available."),
        "conclusion": variant_row.get("conclusion report", "No conclusion available.")
    }

    return report_data

# Fungsi untuk menghasilkan PDF
def generate_pdf(variant, dataset, output_path):
    row = dataset[dataset["Uploaded_variation"] == variant]

    if row.empty:
        return None

    variant_row = row.iloc[0]
    acmg_interpretation = get_acmg_interpretation(variant_row)

    pdf = CustomPDF()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.add_page()

    # Add generated version
    version_info = "v1.0.0 (January 2025)"
    pdf.add_generated_version(version_info)

    # Patient Information
    patient_info = {
        "Name": "John Doe",
        "Date of Birth": "12/01/1987",
        "Sex": "Male",
        "Test Ordered By": "Dr. Fulan, Amazing Hospital Centre"
    }
    pdf.add_patient_info(patient_info)

    # Executive Summary
    pdf.add_styled_title("Executive Summary")
    executive_summary = variant_row.get("Summary", "No explanation available.")
    pdf.add_paragraph(executive_summary)

    # Testing Material and Methods
    pdf.add_styled_title("Testing Material and Methods")
    material_methods = variant_row.get("method", "No Methods available")
    if isinstance(material_methods, str):
        material_methods_list = material_methods.split(". ")
    else:
        material_methods_list = material_methods

    if material_methods_list:
        pdf.add_bullet_points(material_methods_list)
    else:
        pdf.add_paragraph("No testing material or methods available.")

    # ACMG Interpretation
    pdf.add_styled_title("ACMG Result & Interpretation")
    table_data = [
        [variant_row["Nomenclature"], variant_row["Zygosity"], variant_row["effectid_5cls"]],
    ]
    table_headers = ["Variant Detail", "Zygosity", "ACMG"]
    col_widths = [70, 40, 70]
    pdf.add_table(table_data, col_widths, table_headers)
    pdf.add_title("Interpretation")
    if acmg_interpretation:
        pdf.add_paragraph(acmg_interpretation)
    else:
        pdf.add_paragraph("No ACMG interpretation available.")

    # Recommendations
    pdf.add_styled_title("Recommendation")
    recommend = variant_row.get("recommendation", "No recommendation available.")
    pdf.add_paragraph(recommend)

    # Genetic Counselor
    pdf.add_styled_title("Counselor's Note")
    conclu = variant_row.get("counselor's note", "No Counselor's Note available.")
    pdf.add_paragraph(conclu)

    # Conclusion
    pdf.add_styled_title("Conclusion")
    conclu = variant_row.get("conclusion report", "No conclusion available.")
    pdf.add_paragraph(conclu)

    # Simpan PDF
    pdf.output(output_path)
    return output_path

# Endpoint untuk menghasilkan laporan
@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        variant = data.get('variant')
        output_format = data.get('format', 'pdf')  # Default format adalah PDF

        if not variant:
            return jsonify({"error": "Variant name is required."}), 400

        if output_format not in ['pdf', 'json']:
            return jsonify({"error": "Invalid format. Supported formats are 'pdf' and 'json'."}), 400

        if output_format == 'pdf':
            output_dir = "generated_reports"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{variant}_report.pdf")
            pdf_path = generate_pdf(variant, dataset, output_path)

            if not pdf_path:
                return jsonify({"error": f"Variant {variant} not found in the dataset."}), 404

            return send_file(pdf_path, as_attachment=True)

        elif output_format == 'json':
            json_data = generate_json(variant, dataset)

            if not json_data:
                return jsonify({"error": f"Variant {variant} not found in the dataset."}), 404

            return jsonify(json_data)

    except Exception as e:
        logging.error(f"An error occurred in /generate_report endpoint: {e}")
        return jsonify({"error": "An error occurred while generating the report."}), 500
        
#######

def filter_variants_by_effect(dataset, effect):
    if effect.lower() == "all":
        # Ambil semua varian dengan efeknya
        filtered_variants = dataset[["Uploaded_variation", "effectid_5cls"]].values.tolist()
    else:
        # Filter berdasarkan kelas tertentu
        filtered_variants = dataset[dataset["effectid_5cls"].str.lower() == effect.lower()][["Uploaded_variation"]].values.tolist()
    
    return filtered_variants

def generate_variant_list_pdf(variants, effect, output_path):
    pdf = CustomPDF()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.add_page()

    # Add generated version
    version_info = "v1.0.0 (January 2025)"
    pdf.add_generated_version(version_info)

    # Dynamic Title
    if effect.lower() == "all":
        title = "List of All Variants"
    else:
        formatted_effect = effect.lower().capitalize()
        title = f"List of Variant {formatted_effect}"
    
    pdf.add_styled_title(title)

    # Add variants as bullet points
    if effect.lower() == "all":
        # Jika semua varian, tambahkan kelasnya juga
        formatted_variants = [f"{var[0]} ({var[1]})" for var in variants]
    else:
        formatted_variants = [var[0] for var in variants]

    pdf.add_bullet_points(formatted_variants)

    # Simpan PDF
    pdf.output(output_path)
    return output_path

@app.route('/generate_variant_list', methods=['POST'])
def generate_variant_list():
    try:
        # Log raw data received
        logging.info(f"Raw data received: {request.data}")

        # Periksa apakah data JSON diterima
        if not request.is_json:
            logging.error("Request is not in JSON format.")
            return jsonify({"error": "Request must be in JSON format."}), 400

        data = request.get_json()

        # Log parsed JSON data
        logging.info(f"Parsed JSON data: {data}")

        # Periksa apakah field 'effect' ada dalam data
        if not data or 'effect' not in data:
            logging.error("Field 'effect' is missing in the JSON body.")
            return jsonify({"error": "Field 'effect' is required in the JSON body."}), 400

        effect = data['effect'].strip().lower()  # Normalisasi input

        # Filter variants based on effect
        variants = filter_variants_by_effect(dataset, effect)

        if not variants:
            logging.error(f"No variants found for effectid_5cls: {effect}.")
            return jsonify({"error": f"No variants found for effectid_5cls: {effect}."}), 404

        # Generate PDF
        output_dir = "generated_reports"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{effect}_variants_report.pdf")
        pdf_path = generate_variant_list_pdf(variants, effect, output_path)

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        logging.error(f"An error occurred in /generate_variant_list endpoint: {e}")
        return jsonify({"error": "An error occurred while generating the variant list report."}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=5001)