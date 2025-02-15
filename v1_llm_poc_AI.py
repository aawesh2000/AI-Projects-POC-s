import streamlit as st
import os
os.system("pip install pdfplumber")
import pdfplumber
from groq import Groq
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# Initialize Groq client
client = Groq(api_key="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")  # Replace with your actual API key

def read_pdf(file):
    """Extract text while preserving formatting using pdfplumber."""
    with pdfplumber.open(file) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text

def extract_sections(resume_text):
    """Extracts only specific sections (Technical Skills, Experience, etc.)."""
    sections = {}
    current_section = None
    for line in resume_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.lower() in ["technical skills", "experience", "tools"]:
            current_section = line.lower()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    return sections

def tailor_sections(sections, jd_text):
    """Modify only relevant sections while keeping other parts unchanged."""
    for section in ["technical skills", "experience", "tools"]:
        if section in sections:
            original_content = '\n'.join(sections[section])
            tailored_content = tailor_resume(original_content, jd_text)
            sections[section] = tailored_content.split('\n')
    return sections

def reconstruct_resume(resume_text, tailored_sections):
    """Rebuild the resume while keeping original structure."""
    updated_resume = []
    lines = resume_text.split('\n')
    current_section = None
    for line in lines:
        if line.strip().lower() in tailored_sections:
            current_section = line.strip().lower()
            updated_resume.append(line)  # Keep section heading
            updated_resume.extend(tailored_sections[current_section])  # Insert tailored content
        else:
            updated_resume.append(line)  # Keep unchanged content
    return "\n".join(updated_resume)

def tailor_resume(resume_text, jd_text):
    """Use AI to modify only relevant sections."""
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Update this resume section based on the job description while keeping structure: {resume_text}. Job Description: {jd_text}",
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print("Request failed:", e)
        return resume_text  # Return original if AI fails

def generate_pdf(updated_text):
    """Generate a new PDF with the updated resume."""
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 10)

    y_position = 750  # Start writing from the top

    # Write updated text on a new PDF page
    for line in updated_text.split("\n"):
        if y_position < 50:  # If running out of space, create a new page
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = 750
        c.drawString(50, y_position, line)
        y_position -= 12  # Line spacing

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

def extract_company_name(jd_text):
    """Extracts the company name from JD."""
    lines = jd_text.splitlines()
    if lines:
        return lines[0].split()[0]  
    return "UnknownCompany"

def extract_role(jd_text):
    """Extracts the job role from JD."""
    lines = jd_text.splitlines()
    if lines:
        role = lines[0].strip()
        return role.replace('/', '_').replace(' ', '_')
    return "UnknownRole"

def main():
    """Main function for Streamlit UI."""
    st.title("Resume Tailoring App")
    
    resume_file = st.file_uploader("Upload your resume (PDF format)", type="pdf")
    jd_text = st.text_area("Paste the Job Description here")

    if st.button("Tailor Resume"):
        if resume_file and jd_text:
            resume_text = read_pdf(resume_file)
            sections = extract_sections(resume_text)
            tailored_sections = tailor_sections(sections, jd_text)
            updated_resume = reconstruct_resume(resume_text, tailored_sections)
            
            st.subheader("Tailored Resume Preview")
            st.text(updated_resume)

            # Generate new PDF with the updated text
            pdf_buffer = generate_pdf(updated_resume)

            # Provide Download Button
            st.download_button(
                label="Download Tailored Resume",
                data=pdf_buffer,
                file_name="Tailored_Resume.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Please upload a resume and enter a job description.")

if __name__ == "__main__":
    main()
