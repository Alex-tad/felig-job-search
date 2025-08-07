# job_search_ui.py (Streamlit GUI for job_search_ai_agent.py)
import streamlit as st
import os
import tempfile
from job_search_ai_agent import run_job_search_agent

st.set_page_config(page_title="Felig AI Job Agent", page_icon="🤖")
st.title("🤖 Felig AI Job Search Agent")

with st.form("job_search_form"):
    st.subheader("🔍 Search Criteria")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    query = st.text_input("Job Title (e.g. Data Analyst)", value="Data Analyst")
    location = st.text_input("Location (e.g. Remote or City, State)", value="Remote")

    st.subheader("📎 Upload Resume")
    resume_file = st.file_uploader("Resume (PDF only)", type=["pdf"])

    submitted = st.form_submit_button("🚀 Run AI Agent")

if submitted:
    if not all([first_name, last_name, email, query, location, resume_file]):
        st.error("❌ Please fill in all fields and upload a resume.")
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(resume_file.read())
            resume_path = temp_file.name

        st.success("✅ Starting job search and application simulation...")
        run_job_search_agent(
            first_name=first_name,
            last_name=last_name,
            email=email,
            resume_path=resume_path,
            query=query,
            location=location
        )
        os.remove(resume_path)
        st.success("✅ Job search and simulation completed. Check logs/output folder.")
