import os
os.environ["PAFY_BACKEND"] = "internal"
import streamlit as st
import pandas as pd
import base64
import random
import time
import datetime
from pyresparser import ResumeParser
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
import io
from streamlit_tags import st_tags
from PIL import Image
import psycopg2
import yt_dlp
import plotly.express as px
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')

try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    print("Stopwords resource not found. Downloading...")
    import nltk
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

# Adding database

def create_db_connection():
    try:
        connection = psycopg2.connect(
            host='localhost',
            user='resume',
            password='12345',
            dbname='resume'
        )
        connection.autocommit = True
        cursor = connection.cursor()
        return connection, cursor
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None, None

# Fetch YouTube Video

def fetch_yt_video(link):
    """
    Fetch video data with yt_dlp directly to handle compatibility errors.
    """
    # yt_dlp options for better compatibility
    ydl_opts = {
        'quiet': True,
        'geo_bypass': True,
        'noplaylist': True,  # Avoid processing playlists unless necessary
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Extract video data using yt_dlp
            info = ydl.extract_info(link, download=False)
            return info.get("title", "Unknown Title")
        except Exception as e:
            print(f"Error: {e}")
            return "Error Fetching Title"


# Download PDF link
def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Show PDF Function
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# PDF reader Function
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    text = ""
    with open(file, "rb") as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text

# Define Course Recommender
def course_recommender(course_list):
    st.subheader("**Courses & Certifications Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations: ', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

# Define insert data function for storing in the database
def insert_data(connection, cursor, name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    try:
        DB_table_name = 'user_data'
        insert_sql = f"INSERT INTO {DB_table_name} VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        rec_values = (
            name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses
        )
        cursor.execute(insert_sql, rec_values)
        connection.commit()
    except Exception as e:
        st.error(f"Data insertion failed: {e}")

st.set_page_config(
    page_title="Resume Analyser",
    page_icon="./Logo/LOGO.jpg",
)

def run():
    # Create DB connection
    connection, cursor = create_db_connection()
    if not connection or not cursor:
        st.error("Failed to connect to the database.")
        return

    st.title("Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)

    img = Image.open('./Logo/LOGO.jpg')
    img = img.resize((250, 250))
    st.image(img)

    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'resume'")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email_id VARCHAR(50) NOT NULL,
            resume_score VARCHAR(8) NOT NULL,
            timestamp VARCHAR(50) NOT NULL,
            page_no VARCHAR(5) NOT NULL,
            predicted_field VARCHAR(25) NOT NULL,
            user_level VARCHAR(30) NOT NULL,
            actual_skills VARCHAR(300) NOT NULL,
            recommended_skills VARCHAR(300) NOT NULL,
            recommended_courses VARCHAR(600) NOT NULL
        );
    """)
    connection.commit()

    if choice == 'User':
        pdf_file = st.file_uploader("Choose Your Resume", type=["pdf"])
        if pdf_file is not None:
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                resume_text = pdf_reader(save_image_path)
                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data.get("name", "User"))

                st.subheader("**Your Basic Information**")
                try:
                    st.text("Name: " + resume_data['name'])
                    st.text("Email: " + resume_data['email'])
                    st.text("Contact: " + resume_data.get('mobile_number', 'N/A'))
                    st.text("Resume Pages: " + str(resume_data.get("no_of_pages", 0)))
                except KeyError:
                    pass

                cand_level = ""
                no_of_pages = resume_data.get('no_of_pages', 0)
                if no_of_pages == 1:
                    cand_level = "Fresher (Undergraduate or graduate)"
                    st.markdown('<h4 style="color: #d73b5c;">You are looking Fresher.</h4>', unsafe_allow_html=True)
                elif no_of_pages == 2:
                    cand_level = "Intermediate"
                    st.markdown('<h4 style="color: #1ed760;">You are at intermediate level!</h4>', unsafe_allow_html=True)
                elif no_of_pages >= 3:
                    cand_level = "Experienced"
                    st.markdown('<h4 style="color: #fba171;">You are at experience level!</h4>', unsafe_allow_html=True)

                st.subheader("**Skills Recommendation**")
                skills = resume_data.get('skills', [])
                keywords = st_tags(label='## Skills you have', value=skills, key='1')

                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

                reco_field = ""
                recommended_skills = []
                rec_course = ''

                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break
                #
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration✍/h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)


                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration✍/h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)


                insert_data(
                    connection, cursor, 
                    resume_data['name'], resume_data['email'], 
                    str(resume_score), timestamp, 
                    no_of_pages, reco_field, cand_level, 
                    ', '.join(skills), ', '.join(recommended_skills), "None"
)

                
                st.header("**Bonus Video for Resume Writing**")
                resume_vid = random.choice(resume_videos)
                st.subheader(fetch_yt_video(resume_vid))
                st.video(resume_vid)

    elif choice == 'Admin':
        st.success("Welcome to the ADMIN Panel")
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type="password")
        if st.button("Login"):
            if ad_user == 'Tharindu15270' and ad_password == "12345":
                st.success("Welcome Admin")
                cursor.execute('SELECT * FROM user_data')
                data = cursor.fetchall()
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Pages',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Courses'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)

                plot_data = pd.read_sql('SELECT * FROM user_data', connection)
                labels = plot_data.predicted_field.unique()
                st.write(plot_data.columns)

                values = plot_data.predicted_field.value_counts()
                fig = px.pie(values=values, names=labels, title='Predicted Field according to the Skills')
                st.plotly_chart(fig)
            else:
                st.error("Wrong ID & Password Provided")

run()
