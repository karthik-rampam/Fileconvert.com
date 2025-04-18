from flask import Flask, render_template, request, send_file
from pdf2docx import Converter
from docx2pdf import convert
from PyPDF2 import PdfMerger
import os
import uuid
from fpdf import FPDF
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    try:
        uploaded_files = request.files.getlist('file')
        conversion_type = request.form.get('conversionType')

        if not uploaded_files or not conversion_type:
            print("Missing files or conversion type")
            return "Missing files or conversion type", 400

        file_paths = []
        for uploaded_file in uploaded_files:
            if uploaded_file.filename == '':
                continue
            unique_filename = f"{uuid.uuid4()}_{uploaded_file.filename}"
            input_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            uploaded_file.save(input_path)
            file_paths.append(input_path)

        if not file_paths:
            print("No valid files uploaded")
            return "No valid files uploaded", 400

        output_path = None

        if conversion_type == "pdf" and file_paths[0].lower().endswith(".docx"):
            output_path = os.path.splitext(file_paths[0])[0] + "_converted.pdf"
            convert(file_paths[0], output_path)

        elif conversion_type == "docx" and file_paths[0].lower().endswith(".pdf"):
            output_path = os.path.splitext(file_paths[0])[0] + "_converted.docx"
            cv = Converter(file_paths[0])
            cv.convert(output_path)
            cv.close()

        elif conversion_type == "mergepdf":
            merger = PdfMerger()
            for file in file_paths:
                if file.lower().endswith(".pdf"):
                    merger.append(file)
            output_path = os.path.join(UPLOAD_FOLDER, 'merged_output.pdf')
            merger.write(output_path)
            merger.close()

        # Image ➝ PDF
        elif conversion_type == "img2pdf":
            image = Image.open(file_paths[0])
            pdf_path = os.path.splitext(file_paths[0])[0] + "_converted.pdf"
            image.convert("RGB").save(pdf_path)
            output_path = pdf_path

        # Text ➝ PDF
        elif conversion_type == "txt2pdf":
            txt_file = file_paths[0]
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            with open(txt_file, "r", encoding="utf-8") as f:
                for line in f:
                    pdf.multi_cell(0, 10, line)
            output_path = os.path.splitext(txt_file)[0] + "_converted.pdf"
            pdf.output(output_path)

        # Compress PDF
        elif conversion_type == "compresspdf":
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(file_paths[0])
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            output_path = os.path.splitext(file_paths[0])[0] + "_compressed.pdf"
            with open(output_path, "wb") as f_out:
                writer.write(f_out)

        # Image Conversion (PNG ↔ JPG)
        elif conversion_type == "imgconvert":
            image = Image.open(file_paths[0])
            ext = ".jpg" if file_paths[0].lower().endswith(".png") else ".png"
            output_path = os.path.splitext(file_paths[0])[0] + "_converted" + ext
            image.convert("RGB").save(output_path)    
        
        # Excel ➝ PDF
        elif conversion_type == "excel2pdf" and file_paths[0].lower().endswith(".xlsx"):
            import win32com.client
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False

            wb = excel.Workbooks.Open(os.path.abspath(file_paths[0]))
            output_path = os.path.splitext(file_paths[0])[0] + "_converted.pdf"

            try:
                wb.ExportAsFixedFormat(0, os.path.abspath(output_path))  # 0 = PDF format
            finally:
                wb.Close(False)
                excel.Quit()


        elif conversion_type == "ppt2pdf":
            import win32com.client
            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            powerpoint.Visible = 1
            presentation = powerpoint.Presentations.Open(os.path.abspath(file_paths[0]), WithWindow=False)
            output_path = os.path.splitext(file_paths[0])[0] + "_converted.pdf"
            presentation.SaveAs(os.path.abspath(output_path), 32)  # 32 is for PDF
            presentation.Close()
            powerpoint.Quit()


        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("Error:", e)
        return "An error occurred during the conversion. Please try again.", 500

if __name__ == '__main__':
    app.run(debug=True)
