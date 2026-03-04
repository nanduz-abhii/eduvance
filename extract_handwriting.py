import os
import argparse
from google import genai
from PIL import Image
import fitz  # PyMuPDF

# Replace with your actual Gemini API Key if not set in environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyANUm5NhkC12yWPW3fR5Kf5NO4vC26ZVCw")
client = genai.Client(api_key=GEMINI_API_KEY)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a standard PDF file using PyMuPDF."""
    print("Trying standard PDF extraction...")
    with fitz.open(pdf_path) as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    return text

def extract_handwriting_with_gemini(file_path):
    """Extracts handwritten text from an image or PDF using Google Gemini Vision."""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        prompt = "Transcribe the handwritten text in this document exactly as it is written. Do not add any extra commentary or formatting."
        
        if file_extension in ['.jpg', '.jpeg', '.png']:
            print(f"Processing image: {file_path}")
            image = Image.open(file_path)
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=[prompt, image]
            )
            return response.text
            
        elif file_extension == '.pdf':
            print(f"Processing PDF document: {file_path}")
            try:
                # Upload the file directly to Gemini API
                uploaded_file = client.files.upload(file=file_path)
                print(f"File uploaded to Gemini successfully (name: {uploaded_file.name}), analyzing...")
                
                response = client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=[prompt, uploaded_file]
                )
                
                # Clean up (Optional, but good practice if you have many files)
                # client.files.delete(name=uploaded_file.name)
                
                return response.text
            except Exception as e:
                print(f"Gemini API upload/analysis failed: {e}")
                print("Falling back to standard PyMuPDF extraction...")
                return extract_text_from_pdf(file_path)
                
        else:
            return f"Unsupported file format: {file_extension}. Please provide a PDF or Image (.jpg, .png)."
            
    except Exception as e:
        return f"Error during handwriting extraction: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract handwriting from a PDF or image using Gemini API.")
    parser.add_argument("filepath", help="Required: Path to the PDF or image file (e.g., test_handwriting.png)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.filepath):
        print(f"Error: File '{args.filepath}' not found.")
        print("Please provide a valid path to an image or PDF file.")
        exit(1)
        
    print(f"Starting extraction for: {args.filepath}")
    result = extract_handwriting_with_gemini(args.filepath)
    print("\n--- Extracted Text ---\n")
    print(result)
    print("\n----------------------")
