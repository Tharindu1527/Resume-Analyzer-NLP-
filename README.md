# Resume Analyser

A comprehensive web application to analyze resumes, provide skill recommendations, and suggest personalized courses to boost job prospects. The project is built using **Streamlit**, **PyResParser**, and other Python libraries.

## Features

- Upload resumes in PDF format for analysis.
- Extract key details like name, email, contact number, and skills.
- Analyze resume content to:
  - Provide skill recommendations based on the extracted data.
  - Suggest relevant courses to improve specific skill sets.
- Resume writing tips and suggestions to enhance profile strength.
- Admin panel for managing and visualizing user data.

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: Python
- **Database**: PostgreSQL
- **Libraries**:
  - `PyResParser` for resume parsing
  - `Psycopg2` for database interactions
  - `Plotly` for data visualization
  - `PDFMiner` for reading PDFs
  - `Pandas` for data manipulation

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/resume-analyser.git
   cd resume-analyser
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Set up the database:
  - Create a PostgreSQL database named resume.
  - Use the credentials defined in the create_db_connection function of Resume_Analyser.py to connect to the database.

4. Download required NLTK data:
    ```bash
    python -m nltk.downloader stopwords
    ```
5. Run the application:
   ```bash
   streamlit run Resume_Analyser.py
