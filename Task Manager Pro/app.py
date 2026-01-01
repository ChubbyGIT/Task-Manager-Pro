#python -m streamlit run "path of app.py" 
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from streamlit_calendar import calendar

# Import backend functions
import database as db

# Initialize Database
db.init_db()

# ==========================================
# UI CONFIGURATION
# ==========================================

st.set_page_config(page_title="Task Master Pro", layout="wide", page_icon="📦")
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
        .stCheckbox { margin-bottom: -10px; }
        .streamlit-expanderHeader { background-color: #f0f2f6; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Calendar Dashboard", "Analytics"])

# ==========================================
# PAGE 1: CALENDAR DASHBOARD
# ==========================================
if page == "Calendar Dashboard":
    st.title("Task Master Pro 📅")
    col_cal, col_tools = st.columns([3, 1])
    df = db.get_tasks_df()
    
    # --- 1. PREPARE DATA ---
    res_tasks = df[df['task_type'] == 'resolution'] if not df.empty else pd.DataFrame()
    
    events = []
    prio_colors = {"High": "#FF4B4B", "Medium": "#FFAA00", "Low": "#00CC96"}
    
    if not df.empty:
        cal_df = df[df['task_type'] != 'resolution']
        for _, row in cal_df.iterrows():
            s_date = row['start_date']
            e_date = row['end_date'] + timedelta(days=1)
            bg_color = prio_colors.get(row['priority'], "#3788d8")
            title_prefix = "☑ " if row['is_daily'] else ""

            events.append({
                "title": f"{title_prefix}{row['name']} ({row['progress']}%)",
                "start": str(s_date),
                "end": str(e_date),
                "backgroundColor": bg_color,
                "borderColor": bg_color,
                "extendedProps": {
                    "id": row['id'],
                    "desc": row['description'],
                    "progress": row['progress'],
                    "priority": row['priority'],
                    "is_daily": row['is_daily'],
                    "start": str(row['start_date']),
                    "end": str(row['end_date'])
                }
            })

    cal_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "selectable": True,
    }

    # --- RENDER CALENDAR ---
    with col_cal:
        cal_state = calendar(events=events, options=cal_options, key="main_cal")

    # --- RENDER SIDEBAR (CARD VIEW) ---
    with col_tools:
        
        # === CARD 1: RESOLUTIONS ===
        with st.container(border=True):
            st.subheader("🌟 Resolutions")
            if not res_tasks.empty:
                for _, row in res_tasks.iterrows():
                    with st.expander(f"{row['name']} ({row['progress']}%)"):
                        st.caption(f"_{row['description']}_")
                        new_val = st.slider("Progress", 0, 100, row['progress'], key=f"res_s_{row['id']}")
                        if st.button("Save", key=f"res_b_{row['id']}"):
                            db.update_task_progress(row['id'], new_val)
                            st.rerun()
            else:
                st.caption("No resolutions yet.")

        st.write("") # Spacer

        # === CARD 2: TASK MANAGER ===
        with st.container(border=True):
            st.subheader("Task Manager")

            # --- A. EDIT / DELETE LOGIC (If Event Clicked) ---
            if cal_state.get("eventClick"):
                event = cal_state["eventClick"]["event"]
                props = event["extendedProps"]
                task_id = props['id']
                
                # Check expiration
                task_end_date = datetime.strptime(props['end'], "%Y-%m-%d").date()
                today_date = date.today()
                is_expired = task_end_date < today_date

                st.info(f"**{event['title']}**")
                
                if is_expired:
                    st.warning("⚠️ This task has expired and is locked.")
                else:
                    if props['is_daily']:
                        st.write("---")
                        st.caption("Daily Checklist")
                        s_d = datetime.strptime(props['start'], "%Y-%m-%d").date()
                        e_d = task_end_date
                        delta = (e_d - s_d).days + 1
                        status_map = db.get_daily_status_map(task_id)
                        
                        with st.container():
                            for i in range(delta):
                                day = s_d + timedelta(days=i)
                                day_str = str(day)
                                is_done = status_map.get(day_str, False)
                                chk_key = f"chk_{task_id}_{day_str}"
                                new_status = st.checkbox(day.strftime("%a, %b %d"), value=is_done, key=chk_key)
                                if new_status != is_done:
                                    db.toggle_daily_status(task_id, day_str, new_status)
                                    st.rerun()
                    else:
                        new_prog = st.slider("Progress %", 0, 100, props['progress'], key="edit_slider")
                        if st.button("Save"):
                            db.update_task_progress(task_id, new_prog)
                            st.rerun()
                
                st.divider()
                col_d1, col_d2 = st.columns(2)
                if col_d1.button("🗑️ Delete"):
                    db.delete_task(task_id)
                    st.rerun()
                if col_d2.button("Close"):
                    st.rerun()

            # --- B. ADD NEW TASK (Collapsible) ---
            else:
                pkg_start, pkg_end = db.get_package_dates()
                today = date.today()
                
                start_default = today
                if cal_state.get("dateClick"):
                    raw_date = cal_state["dateClick"]["date"]
                    date_str = raw_date.split("T")[0]
                    start_default = datetime.strptime(date_str, "%Y-%m-%d").date()

                end_default = pkg_end if pkg_end else (start_default + timedelta(days=4))
                is_end_locked = True if pkg_end else False

                with st.expander("➕ Add New Task", expanded=False):
                    with st.form("add_task_form", clear_on_submit=True):
                        if pkg_end:
                             st.caption(f"🔒 Active Cycle: Ends {pkg_end.strftime('%b %d')}")
                        else:
                             st.caption("✨ Starting New Cycle")

                        t_name = st.text_input("Task Name")
                        t_desc = st.text_area("Description", height=68)
                        t_prio = st.selectbox("Priority", ["High", "Medium", "Low"])
                        
                        d_start = st.date_input("Start", start_default)
                        d_end = st.date_input("End", end_default, disabled=is_end_locked)
                        
                        is_daily = st.checkbox("Daily Checklist?", value=False)
                        
                        if st.form_submit_button("Add Task"):
                            if d_end < d_start:
                                st.error("End Date cannot be before Start Date.")
                            elif not t_name:
                                st.error("Name required")
                            else:
                                db.add_task_to_db(t_name, t_desc, t_prio, d_start, d_end, "regular", is_daily)
                                st.success("Added!")
                                st.rerun()

            # --- C. ACTIVE TASKS LIST (Beautified) ---
            if not df.empty:
                reg_df = df[df['task_type'] != 'resolution']
                today_date = date.today()
                
                # Filter for active tasks (End date is today or future)
                active_cycle_df = reg_df[reg_df['end_date'] >= today_date] if not reg_df.empty else pd.DataFrame()

                if not active_cycle_df.empty:
                    st.divider()
                    st.caption("Active Tasks Status")
                    
                    # Sort by Priority then Progress
                    active_cycle_df['prio_val'] = pd.Categorical(active_cycle_df['priority'], ["High", "Medium", "Low"])
                    active_cycle_df = active_cycle_df.sort_values(by=["prio_val", "progress"])
                    
                    for _, row in active_cycle_df.iterrows():
                        # Priority Color Indicator
                        p_emoji = "🔴" if row['priority'] == "High" else "🟡" if row['priority'] == "Medium" else "🟢"
                        
                        with st.expander(f"{p_emoji} {row['name']} ({row['progress']}%)"):
                            if row['description']:
                                st.caption(f"_{row['description']}_")
                            
                            st.caption(f"📅 Due: {row['end_date']}")
                            
                            new_val = st.slider("Progress", 0, 100, int(row['progress']), key=f"act_s_{row['id']}")
                            if st.button("Update", key=f"act_b_{row['id']}"):
                                db.update_task_progress(row['id'], new_val)
                                st.rerun()
                else:
                    if not reg_df.empty:
                        st.divider()
                        st.caption("No active tasks.")

# ==========================================
# PAGE 2: ANALYTICS
# ==========================================
elif page == "Analytics":
    st.title("📈 Performance & Resolutions")
    
    # --- SUCCESS MESSAGE LOGIC ---
    if st.session_state.get('res_success'):
        st.success("✨ New Year Resolution Added Successfully!")
        del st.session_state['res_success']

    # --- MANAGE RESOLUTIONS SECTION ---
    with st.expander("✨ Manage New Year Resolutions", expanded=False):
        
        lock_date = date(2026, 1, 3)
        can_edit = date.today() <= lock_date

        res_df = db.get_resolutions_df()

        if not res_df.empty:
            st.subheader("Your Goals")
            for _, row in res_df.iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"🎯 **{row['name']}**")
                    if row['description']:
                        st.caption(f"_{row['description']}_")
                with col2:
                    if can_edit:
                        if st.button("🗑️", key=f"del_res_{row['id']}"):
                            db.delete_task(row['id'])
                            st.rerun()
                    else:
                        st.caption("🔒 Locked")
            st.divider()
        
        if can_edit:
            st.subheader("Add New")
            with st.form("res_add", clear_on_submit=True):
                r_name = st.text_input("Resolution Goal")
                r_desc = st.text_input("Details")
                
                if st.form_submit_button("Lock In"):
                    if r_name:
                        s_26 = date(2026, 1, 1)
                        e_26 = date(2026, 12, 31)
                        db.add_task_to_db(r_name, r_desc, "High", s_26, e_26, "resolution", False)
                        st.session_state['res_success'] = True
                        st.rerun()
                    else:
                        st.error("Please enter a name for your resolution.")
        else:
            st.warning("Resolutions are locked for the year.")
            
    st.divider()
    
    df = db.get_tasks_df()
    if not df.empty:
        # Filter regular tasks
        reg_df = df[df['task_type'] != 'resolution'].copy()
        
        if not reg_df.empty:
            
            # --- 1. SPRINT CALCULATION LOGIC ---
            reg_df['end_date'] = pd.to_datetime(reg_df['end_date'])
            sprint_groups = reg_df.groupby('end_date')
            
            sprint_data = []
            
            for i, (end_dt, group) in enumerate(sorted(sprint_groups)):
                sprint_num = i + 1
                avg_eff = group['progress'].mean()
                task_count = len(group)
                sprint_data.append({
                    "Sprint": f"Sprint {sprint_num}",
                    "End Date": end_dt.strftime("%Y-%m-%d"),
                    "Efficiency": int(avg_eff),
                    "Tasks": task_count,
                    "Data": group
                })
            
            sprint_df = pd.DataFrame(sprint_data)
            
            # --- 2. HEADER METRICS ---
            total = len(reg_df)
            completed = len(reg_df[reg_df['progress'] == 100])
            avg_sprint_eff = sprint_df['Efficiency'].mean() if not sprint_df.empty else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Tasks", total)
            c2.metric("Completed Tasks", completed)
            c3.metric("Avg Sprint Efficiency", f"{int(avg_sprint_eff)}%")
            
            st.divider()
            
            # --- 3. CHARTS ---
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.subheader("Efficiency (Last 7 Sprints)")
                if not sprint_df.empty:
                    recent_sprints = sprint_df.tail(7)
                    fig_sprint = px.bar(
                        recent_sprints,
                        x="Sprint",
                        y="Efficiency",
                        text="Efficiency",
                        color="Efficiency",
                        color_continuous_scale="Blues",
                        range_y=[0, 100]
                    )
                    fig_sprint.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig_sprint.update_layout(height=300, margin=dict(t=30, b=10, l=10, r=10), coloraxis_showscale=False)
                    st.plotly_chart(fig_sprint, use_container_width=True)
                else:
                    st.info("No sprints found.")

            with col_g2:
                st.subheader("Current Sprint Status")
                if sprint_data:
                    latest_sprint = sprint_data[-1] 
                    ls_df = latest_sprint['Data']
                    
                    done_count = len(ls_df[ls_df['progress'] == 100])
                    pending_count = len(ls_df[ls_df['progress'] < 100])
                    
                    pie_data = pd.DataFrame({
                        "Status": ["Completed", "Pending"],
                        "Count": [done_count, pending_count]
                    })
                    
                    fig_pie = px.pie(
                        pie_data, 
                        values='Count', 
                        names='Status',
                        color='Status',
                        color_discrete_map={"Completed": "#00CC96", "Pending": "#FF4B4B"},
                        hole=0.4
                    )
                    fig_pie.update_layout(
                        height=300, 
                        margin=dict(t=10, b=10, l=10, r=10),
                        showlegend=True,
                        annotations=[dict(text=f"{latest_sprint['Sprint']}", x=0.5, y=0.5, font_size=14, showarrow=False)]
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No active sprint data.")
            
            # --- 4. EXPANDABLE SPRINT LIST ---
            st.subheader("Sprint Details")
            st.caption("Click on a row to expand details.")

            for item in reversed(sprint_data):
                s_name = item['Sprint']
                s_eff = item['Efficiency']
                s_date = item['End Date']
                s_count = item['Tasks']
                
                emoji = "🟢" if s_eff >= 80 else "🟡" if s_eff >= 50 else "🔴"
                label = f"{emoji} {s_name} │ 📅 Ends: {s_date} │ 📊 Efficiency: {s_eff}% │ 📝 {s_count} Tasks"
                
                with st.expander(label):
                    sub_df = item['Data'][['name', 'start_date', 'end_date', 'progress', 'priority']].copy()
                    sub_df['start_date'] = pd.to_datetime(sub_df['start_date']).dt.date
                    sub_df['end_date'] = pd.to_datetime(sub_df['end_date']).dt.date
                    
                    st.dataframe(sub_df, use_container_width=True, hide_index=True)
            
        else:
            st.info("No regular tasks found in package.")
    else:
        st.info("No data yet.")