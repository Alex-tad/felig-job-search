# job_bot_gui.py
import streamlit as st
from multi_portal_bot import route_application, detect_portal
import openai
import os
import csv
import pandas as pd
from datetime import datetime

# -------------------- CONFIG -------------------- #
openai.api_key = os.getenv("OPENAI_API_KEY")
LOG_FILE = "application_log.csv"

st.set_page_config(page_title="Felig Job Application Bot", page_icon="🤖")
st.title("🤖 Felig Job Application Assistant")

menu = st.sidebar.selectbox("Choose View", ["Apply", "Dashboard"])

# -------------------- GPT Cover Letter Generation -------------------- #
def generate_cover_letter(job_url, resume_text):
    prompt = f"""
You are an AI assistant helping someone apply for a job. Given the resume and job link, generate a professional and concise cover letter.

Job URL:
{job_url}

Resume:
{resume_text}

Guidelines:
- Address it to "Dear Hiring Manager"
- Highlight relevant skills and experience
- Be under 300 words
- End with "Sincerely, Sarah Tadesse"
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"[Error generating cover letter: {e}]"

# -------------------- Application Logger -------------------- #
def log_application(first_name, last_name, email, job_url, portal, status):
    headers = ["First Name", "Last Name", "Email", "Job URL", "Portal", "Status", "Timestamp"]
    row = [
        first_name,
        last_name,
        email,
        job_url,
        portal,
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)

# -------------------- Dashboard -------------------- #
def show_dashboard():
    st.header("📊 Application Dashboard")
    if not os.path.exists(LOG_FILE):
        st.warning("No applications have been logged yet.")
        return

    df = pd.read_csv(LOG_FILE)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Applications", len(df))
        st.metric("Unique Portals", df["Portal"].nunique())
    with col2:
        success_count = df["Status"].str.contains("Success").sum()
        st.metric("Successful", success_count)
        st.metric("Failed", len(df) - success_count)

    st.subheader("Applications by Portal")
    portal_counts = df["Portal"].value_counts()
    st.bar_chart(portal_counts)

    st.subheader("Detailed Log")
    st.dataframe(df.sort_values("Timestamp", ascending=False), use_container_width=True)

# -------------------- Streamlit Form -------------------- #
def show_application_form():
    st.markdown("Automatically fill job applications across major portals like Workable, Greenhouse, and more.")

    with st.form("job_form"):
        st.subheader("👤 Your Info")
        first_name = st.text_input("First Name", value="Sarah")
        last_name = st.text_input("Last Name", value="Tadesse")
        email = st.text_input("Email", value="sarah.tadesse@example.com")

        st.subheader("📎 Files")
        resume_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

        st.subheader("🔗 Job URL")
        job_url = st.text_input("Paste the full job application URL")

        generate = st.form_submit_button("✍️ Generate Cover Letter with GPT")
        submitted = st.form_submit_button("🚀 Apply")

    cover_letter = ""
    if generate and resume_file and job_url:
        with st.spinner("Generating cover letter using GPT-4..."):
            resume_path = os.path.join("temp", resume_file.name)
            os.makedirs("temp", exist_ok=True)
            with open(resume_path, "wb") as f:
                f.write(resume_file.getbuffer())
            with open(resume_path, "rb") as f:
                resume_text = f.read().decode(errors="ignore")
            cover_letter = generate_cover_letter(job_url, resume_text)
            st.session_state["cover_letter"] = cover_letter
            st.text_area("📄 Suggested Cover Letter", value=cover_letter, height=250)
            os.remove(resume_path)

    if submitted:
        if not resume_file or not job_url:
            st.error("Please upload your resume and provide the job URL.")
        else:
            with st.spinner("Filling application form..."):
                os.makedirs("temp", exist_ok=True)
                resume_path = os.path.join("temp", resume_file.name)
                with open(resume_path, "wb") as f:
                    f.write(resume_file.getbuffer())

                user_info = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "cover_letter": st.session_state.get("cover_letter", "This is a default cover letter.")
                }

                portal = detect_portal(job_url)
                try:
                    route_application(job_url, resume_path, user_info)
                    st.success("✅ Application simulated successfully (not submitted).")
                    log_application(first_name, last_name, email, job_url, portal, "Success")
                except Exception as e:
                    st.error(f"❌ Error during application: {e}")
                    log_application(first_name, last_name, email, job_url, portal, f"Error: {e}")

                os.remove(resume_path)

# -------------------- App Controller -------------------- #
if menu == "Dashboard":
    show_dashboard()
else:
    show_application_form()