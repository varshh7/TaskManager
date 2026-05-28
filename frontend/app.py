"""
app.py — Entry point for the Task Manager Streamlit frontend.
Run with:  streamlit run app.py
"""
import streamlit as st
import api_client as api
from datetime import date

# ─── Page Config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="TaskFlow",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State Defaults ───────────────────────────────────────────────────
defaults = {
    "token": None,
    "user": None,          # {"username": ..., "full_name": ...}
    "page": "login",       # login | register | dashboard | new_task | edit_task
    "edit_task_data": None,
    "filter_status": "all",
    "filter_priority": "all",
    "success_msg": None,
    "error_msg": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #111827;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid #d1d5db;
}
section[data-testid="stSidebar"] * { color: #111827 !important; }

/* Main background */
.main { background: #f8fafc; }
.block-container { padding-top: 2rem; max-width: 1100px; }

/* Typography */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; color: #111827; }

/* Cards */
.task-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.task-card:hover { border-color: #cbd5e1; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08); }

/* Priority badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-high   { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
.badge-medium { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
.badge-low    { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.badge-todo        { background: #e2e8f0; color: #475569; border: 1px solid #cbd5e1; }
.badge-in_progress { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
.badge-done        { background: #d1fae5; color: #047857; border: 1px solid #a7f3d0; }

/* Stat tiles */
.stat-tile {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
}
.stat-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #4338ca;
}
.stat-label { font-size: 0.78rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em; }

/* Buttons override */
.stButton > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stDateInput > div > div > div > input,
input[type="text"],
input[type="password"],
textarea,
select {
    background: #ffffff !important;
    border-color: #d1d5db !important;
    color: #111827 !important;
    border-radius: 8px !important;
}

input::placeholder,
textarea::placeholder {
    color: #6b7280 !important;
    opacity: 1 !important;
}

select option {
    background: #ffffff !important;
    color: #111827 !important;
}

/* Divider */
hr { border-color: #e5e7eb !important; }

/* Hide default Streamlit header decoration */
header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _show_flash():
    if st.session_state.get("success_msg"):
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None
    if st.session_state.get("error_msg"):
        st.error(st.session_state.error_msg)
        st.session_state.error_msg = None


def _sidebar_controls():
    user = st.session_state.user or {}
    st.sidebar.markdown(f"""
        <div style='padding:1rem 0.5rem 0.5rem'>
            <div style='font-family:Syne,sans-serif;font-size:1.2rem;font-weight:700;color:#a78bfa;'>
                ✦ TaskFlow
            </div>
            <div style='font-size:0.8rem;color:#6b6b8a;margin-top:0.2rem;'>
                {user.get('full_name','—')}
            </div>
        </div>
        <hr style='margin:0.75rem 0;border-color:#1f1f2a;'/>
    """, unsafe_allow_html=True)

    if st.sidebar.button("＋  New Task", use_container_width=True, type="primary"):
        st.session_state.page = "new_task"
        st.rerun()

    st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("<div style='font-size:0.72rem;color:#6b6b8a;letter-spacing:0.08em;text-transform:uppercase;padding:0 0.25rem;'>Filter by Status</div>", unsafe_allow_html=True)
    status_opts = ["all", "todo", "in_progress", "done"]
    st.session_state.filter_status = st.sidebar.selectbox(
        "Status", status_opts,
        index=status_opts.index(st.session_state.filter_status),
        label_visibility="collapsed",
    )

    st.sidebar.markdown("<div style='font-size:0.72rem;color:#6b6b8a;letter-spacing:0.08em;text-transform:uppercase;padding:0.5rem 0.25rem 0;'>Filter by Priority</div>", unsafe_allow_html=True)
    prio_opts = ["all", "high", "medium", "low"]
    st.session_state.filter_priority = st.sidebar.selectbox(
        "Priority", prio_opts,
        index=prio_opts.index(st.session_state.filter_priority),
        label_visibility="collapsed",
    )

    st.sidebar.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("<hr style='border-color:#1f1f2a;margin-top:2rem;'/>", unsafe_allow_html=True)
    if st.sidebar.button("Sign Out", use_container_width=True):
        for k in ["token", "user", "edit_task_data"]:
            st.session_state[k] = None
        st.session_state.page = "login"
        st.rerun()


# ─── Page Renderers ─────────────────────────────────────────────────────────

def render_login():
    st.title("Sign in to TaskFlow")
    _show_flash()
    username = st.text_input("Username", key="login_username", placeholder="your_username")
    password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

    if st.button("Sign In →", use_container_width=True, type="primary"):
        if not username or not password:
            st.error("Please fill in both fields.")
        else:
            data, err = api.login(username, password)
            if err:
                st.error(f"Login failed: {err}")
            else:
                st.session_state.token = data["access_token"]
                me, _ = api.get_me()
                st.session_state.user = me
                st.session_state.page = "dashboard"
                st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("Create Account", use_container_width=True):
        st.session_state.page = "register"
        st.rerun()


def render_register():
    st.title("Create a TaskFlow account")
    _show_flash()
    full_name = st.text_input("Full Name", key="reg_full_name", placeholder="Varsha R")
    username = st.text_input("Username", key="reg_username", placeholder="varsha_r")
    password = st.text_input("Password", type="password", key="reg_password", placeholder="min 6 chars")
    confirm = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="repeat password")

    if st.button("Create Account →", use_container_width=True, type="primary"):
        if not all([full_name, username, password, confirm]):
            st.error("All fields are required.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            data, err = api.register(username, password, full_name)
            if err:
                st.error(f"Registration failed: {err}")
            else:
                st.session_state.success_msg = f"Account created! Welcome, {full_name}. Please log in."
                st.session_state.page = "login"
                st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()


def render_dashboard():
    st.title("Your Tasks")
    _sidebar_controls()
    _show_flash()

    stats, err = api.get_stats()
    if err:
        st.error(f"Could not load stats: {err}")
        return
    if stats:
        cols = st.columns(4)
        items = [
            ("Total", stats.get("total", 0), "#a78bfa"),
            ("To Do", stats.get("todo", 0), "#8888cc"),
            ("In Progress", stats.get("in_progress", 0), "#6baeff"),
            ("Done", stats.get("done", 0), "#6bffb0"),
        ]
        for col, (label, val, color) in zip(cols, items):
            col.markdown(f"""
                <div class="stat-tile">
                    <div class="stat-num" style="color:{color};">{val}</div>
                    <div class="stat-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    sf = st.session_state.filter_status
    pf = st.session_state.filter_priority
    tasks, err = api.list_tasks(
        status_filter=None if sf == "all" else sf,
        priority_filter=None if pf == "all" else pf,
    )
    if err:
        st.error(f"Could not load tasks: {err}")
        return

    if not tasks:
        st.markdown("""
            <div style='text-align:center;padding:3rem;color:#3d3d5c;'>
                <div style='font-size:2rem;'>✦</div>
                <div style='margin-top:0.5rem;font-size:0.9rem;'>No tasks yet. Create one!</div>
            </div>
        """, unsafe_allow_html=True)
        return

    for task in tasks:
        tid = task["id"]
        with st.container():
            st.markdown(f"""
            <div class="task-card">
                <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.35rem;">
                    <span style="font-family:Syne,sans-serif;font-size:1rem;font-weight:600;color:#111827;">
                        {task['title']}
                    </span>
                    <span class="badge badge-{task['priority']}">{task['priority'].title()}</span>
                    <span class="badge badge-{task['status']}">{task['status'].replace('_', ' ').title()}</span>
                </div>
                <div style="color:#6b6b8a;font-size:0.85rem;margin-bottom:0.5rem;">
                    {task.get('description') or '<em>No description</em>'}
                </div>
                <div style="font-size:0.72rem;color:#3d3d5c;">
                    Created {task['created_at'][:10]}
                    {'&nbsp;·&nbsp;Due ' + task['due_date'] if task.get('due_date') else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                new_status = st.selectbox(
                    "Status",
                    ["todo", "in_progress", "done"],
                    index=["todo", "in_progress", "done"].index(task["status"]),
                    key=f"sel_{tid}",
                    label_visibility="collapsed",
                )
                if new_status != task["status"]:
                    _, err = api.update_task(tid, status=new_status)
                    if not err:
                        st.rerun()
            with c2:
                if st.button("Edit", key=f"edit_{tid}", use_container_width=True):
                    st.session_state.edit_task_data = task
                    st.session_state.page = "edit_task"
                    st.rerun()
            with c3:
                if st.button("Delete", key=f"del_{tid}", use_container_width=True):
                    api.delete_task(tid)
                    st.rerun()
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)


def render_new_task():
    st.title("Create New Task")
    _sidebar_controls()
    _show_flash()

    col1, col2 = st.columns([2, 1])
    with col1:
        title = st.text_input("Title *", key="new_title", placeholder="e.g. Build REST API endpoints")
        description = st.text_area("Description", key="new_description", placeholder="What needs to be done?", height=120)
    with col2:
        priority = st.selectbox("Priority", ["medium", "high", "low"], key="new_priority")
        due_date = st.date_input("Due Date (optional)", value=None, min_value=date.today(), key="new_due")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("Create Task", type="primary", use_container_width=True):
            if not title.strip():
                st.error("Title is required.")
            else:
                due = str(due_date) if due_date else None
                _, err = api.create_task(title.strip(), description.strip(), priority, due)
                if err:
                    st.error(f"Failed: {err}")
                else:
                    st.session_state.success_msg = f"Task '{title}' created!"
                    st.session_state.page = "dashboard"
                    st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=False):
            st.session_state.page = "dashboard"
            st.rerun()


def render_edit_task():
    task = st.session_state.get("edit_task_data")
    if not task:
        st.session_state.page = "dashboard"
        st.rerun()
        return

    st.title("Edit Task")
    _sidebar_controls()
    _show_flash()

    col1, col2 = st.columns([2, 1])
    with col1:
        title = st.text_input("Title *", value=task["title"], key="edit_title")
        description = st.text_area("Description", value=task.get("description", ""), height=120, key="edit_description")
    with col2:
        prio_opts = ["low", "medium", "high"]
        priority = st.selectbox("Priority", prio_opts, index=prio_opts.index(task.get("priority", "medium")), key="edit_priority")
        status_opts = ["todo", "in_progress", "done"]
        status = st.selectbox("Status", status_opts, index=status_opts.index(task.get("status", "todo")), key="edit_status")
        existing_due = task.get("due_date")
        due_date = st.date_input(
            "Due Date (optional)",
            value=date.fromisoformat(existing_due) if existing_due else None,
            min_value=date.today(),
            key="edit_due",
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("Save Changes", type="primary", use_container_width=True):
            if not title.strip():
                st.error("Title is required.")
            else:
                due = str(due_date) if due_date else None
                _, err = api.update_task(
                    task["id"],
                    title=title.strip(),
                    description=description.strip(),
                    priority=priority,
                    status=status,
                    due_date=due,
                )
                if err:
                    st.error(f"Update failed: {err}")
                else:
                    st.session_state.success_msg = "Task updated!"
                    st.session_state.edit_task_data = None
                    st.session_state.page = "dashboard"
                    st.rerun()
    with c2:
        if st.button("Cancel"):
            st.session_state.edit_task_data = None
            st.session_state.page = "dashboard"
            st.rerun()


# ─── App Entry ─────────────────────────────────────────────────────────────────
page = st.session_state.page
if page == "login":
    render_login()
elif page == "register":
    render_register()
elif page == "dashboard":
    render_dashboard()
elif page == "new_task":
    render_new_task()
elif page == "edit_task":
    render_edit_task()
else:
    st.error("Unknown page state. Resetting to login.")
    st.session_state.page = "login"
    st.rerun()
