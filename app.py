import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, date

import db_helper as db
import scheduler

st.set_page_config(
    page_title="PlanAI - Smart Study Planner",
    page_icon="assets/favicon.ico" if os.path.exists("assets/favicon.ico") else "📚",
    layout="wide"
)

# Initialize Database
db.init_db()

# Custom CSS for UI styling
st.markdown("""
<style>
    .main-title { font-size: 32px; font-weight: 700; color: #1E293B; margin-bottom: 0px; }
    .sub-title { font-size: 15px; color: #64748B; margin-bottom: 25px; }
    .metric-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# App Header
col_logo, col_heading = st.columns([1, 8])
with col_logo:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=70)
    else:
        st.markdown("# 🧠")

with col_heading:
    st.markdown('<div class="main-title">PlanAI: Intelligent Study Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Algorithmic prioritization, revision tracking, and focus management</div>', unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Choose Module",
    ["📋 Topic Intake", "⚡ AI Daily Schedule", "📊 Analytics & Progress", "⏱️ Pomodoro Timer"]
)

# ----------------------------------------------------
# 1. TOPIC INTAKE MODULE
# ----------------------------------------------------
if menu == "📋 Topic Intake":
    st.subheader("Add Syllabus Topics")
    with st.form("add_topic_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject Name", placeholder="e.g., Computer Networks, Java")
            topic = st.text_input("Topic Name", placeholder="e.g., TCP/IP 3-Way Handshake")
            exam_date = st.date_input("Target Exam / Deadline Date", min_value=date.today())
        with col2:
            difficulty = st.slider("Difficulty (1 = Simple, 5 = Very Hard)", 1, 5, 3)
            confidence = st.slider("Current Confidence (1 = Low, 5 = Mastered)", 1, 5, 2)
            est_hours = st.number_input("Estimated Study Hours Required", min_value=0.5, max_value=50.0, value=3.0, step=0.5)

        submit = st.form_submit_button("Save Topic to Database")
        if submit:
            if subject.strip() and topic.strip():
                db.add_topic(subject.strip(), topic.strip(), str(exam_date), difficulty, confidence, est_hours)
                st.success(f"Topic '{topic}' added successfully!")
            else:
                st.error("Please provide both Subject and Topic names.")

    st.divider()
    st.subheader("Current Topics in Repository")
    raw_topics = db.get_all_topics()
    if raw_topics:
        df = pd.DataFrame(raw_topics, columns=["ID", "Subject", "Topic", "Exam Date", "Difficulty", "Confidence", "Est Hours", "Completed"])
        df["Completed"] = df["Completed"].apply(lambda x: "✅ Yes" if x == 1 else "⏳ In Progress")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No topics added yet. Add your first syllabus unit above.")

# ----------------------------------------------------
# 2. AI DAILY SCHEDULE MODULE
# ----------------------------------------------------
elif menu == "⚡ AI Daily Schedule":
    st.subheader("Dynamic Prioritization Engine")
    topics = db.get_all_topics()

    if not topics:
        st.warning("No syllabus data available. Please add topics under 'Topic Intake' first.")
    else:
        daily_capacity = st.slider("Select Available Study Time for Today (Hours)", min_value=1.0, max_value=14.0, value=4.0, step=0.5)
        
        if st.button("Generate Optimized Schedule"):
            schedule = scheduler.generate_heuristic_schedule(topics, daily_capacity)
            if not schedule:
                st.success("All registered topics are already completed!")
            else:
                st.session_state["active_schedule"] = schedule

        if "active_schedule" in st.session_state:
            st.markdown("#### Recommended Plan for Today")
            sched_df = pd.DataFrame(st.session_state["active_schedule"])
            st.dataframe(sched_df[["subject", "topic", "days_left", "priority_score", "recommended_hours"]], use_container_width=True)

            st.divider()
            st.markdown("#### Mark Tasks & Request AI Guidance")
            for item in st.session_state["active_schedule"]:
                c1, c2, c3 = st.columns([4, 2, 2])
                with c1:
                    st.write(f"**{item['subject']}**: {item['topic']} ({item['recommended_hours']} hrs)")
                with c2:
                    if st.button(f"Mark Done #{item['id']}", key=f"done_{item['id']}"):
                        db.update_topic_status(item["id"], 1)
                        db.log_study_time(item["id"], item["recommended_hours"])
                        st.toast(f"Completed {item['topic']}!")
                        st.rerun()
                with c3:
                    if st.button(f"Get AI Tips #{item['id']}", key=f"ai_{item['id']}"):
                        tips = scheduler.generate_ai_advice(item["topic"], item["subject"], 3, 2)
                        st.info(tips)

# ----------------------------------------------------
# 3. ANALYTICS & PROGRESS MODULE
# ----------------------------------------------------
elif menu == "📊 Analytics & Progress":
    st.subheader("Performance & Syllabus Coverage")
    topics = db.get_all_topics()
    
    if not topics:
        st.info("Log syllabus topics to view analytics.")
    else:
        df = pd.DataFrame(topics, columns=["ID", "Subject", "Topic", "Exam Date", "Difficulty", "Confidence", "Est Hours", "Completed"])
        total_tasks = len(df)
        completed_tasks = len(df[df["Completed"] == 1])
        completion_rate = round((completed_tasks / total_tasks) * 100, 1)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Topics", total_tasks)
        col2.metric("Completed Topics", completed_tasks)
        col3.metric("Completion Rate", f"{completion_rate}%")

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.markdown("##### Topic Status Distribution")
            fig1, ax1 = plt.subplots(figsize=(4, 4))
            ax1.pie([completed_tasks, total_tasks - completed_tasks], labels=["Completed", "Pending"], autopct="%1.1f%%", colors=["#10B981", "#EF4444"])
            st.pyplot(fig1)

        with col_chart2:
            st.markdown("##### Hours Studied by Subject")
            stats = db.get_logged_study_stats()
            if stats:
                stat_df = pd.DataFrame(stats, columns=["Subject", "Hours Studied"])
                fig2, ax2 = plt.subplots(figsize=(5, 4))
                ax2.bar(stat_df["Subject"], stat_df["Hours Studied"], color="#3B82F6")
                ax2.set_ylabel("Hours")
                plt.xticks(rotation=30, ha="right")
                st.pyplot(fig2)
            else:
                st.write("Complete tasks from the schedule to populate hours studied.")

# ----------------------------------------------------
# 4. POMODORO FOCUS TIMER MODULE
# ----------------------------------------------------
elif menu == "⏱️ Pomodoro Timer":
    st.subheader("Focus Timer")
    work_time = st.number_input("Work Session Duration (Minutes)", min_value=5, max_value=60, value=25)
    
    if st.button("Start Sprint"):
        timer_placeholder = st.empty()
        total_seconds = int(work_time * 60)
        
        while total_seconds > 0:
            mins, secs = divmod(total_seconds, 60)
            timer_placeholder.markdown(f"## ⏳ `{mins:02d}:{secs:02d}`")
            time.sleep(1)
            total_seconds -= 1
            
        timer_placeholder.markdown("## 🎉 Session Complete! Take a 5-minute break.")
        st.balloons()
