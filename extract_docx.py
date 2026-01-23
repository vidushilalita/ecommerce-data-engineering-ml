import zipfile
import xml.etree.ElementTree as ET
import sys

def extract_text_from_docx(docx_path):
    """Extract text from a .docx file without python-docx library"""
    text_content = []
    
    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            xml_content = zip_ref.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # Define the namespace
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            
            # Extract all text elements
            for paragraph in root.findall('.//w:t', namespaces):
                if paragraph.text:
                    text_content.append(paragraph.text)
            
        return '\n'.join(text_content)
    except Exception as e:
        return f"Error extracting text: {str(e)}"

if __name__ == "__main__":
    # Set UTF-8 encoding for output
    sys.stdout.reconfigure(encoding='utf-8')
    
    docx_path = r"C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml\data\DM4ML-Assignment-I.docx"
    text = extract_text_from_docx(docx_path)
    
    # Save to file with UTF-8 encoding
    output_file = r"C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml\assignment_content.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"Assignment content extracted to: {output_file}")
