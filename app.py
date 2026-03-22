import streamlit as st
from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown("Welcome to **PawPal+** — your pet care planning assistant.")

st.divider()

# --- Session State Initialization ---
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json()
    except (FileNotFoundError, KeyError, ValueError):
        st.session_state.owner = None

PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}
PRIORITY_EMOJI = {
    "HIGH":   "🔴 High",
    "MEDIUM": "🟡 Medium",
    "LOW":    "🟢 Low",
}

# ── Section 1: Owner & Pet Setup ──────────────────────────────────────────────
st.subheader("1. Owner & Pet Setup")

owner_name = st.text_input("Owner name", value="Jordan")
available_time = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=60)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save owner & pet"):
    pet = Pet(name=pet_name, species=species)
    owner = Owner(name=owner_name, available_minutes_per_day=int(available_time), pets=[pet])
    st.session_state.owner = owner
    owner.save_to_json()
    st.success(f"Saved! {owner_name} is caring for {pet_name} ({species}) with {available_time} min today.")

st.divider()

# ── Section 2: Add Tasks ───────────────────────────────────────────────────────
st.subheader("2. Add Tasks")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    task_time = st.text_input("Start time (HH:MM)", value="07:00")

if st.button("Add task"):
    if st.session_state.owner is None:
        st.warning("Please save an owner & pet first.")
    else:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority_str],
            time=task_time,
        )
        st.session_state.owner.pets[0].add_task(task)
        st.session_state.owner.save_to_json()
        st.success(f"Added: **{task_title}** at {task_time} ({duration} min, {priority_str} priority)")

# Display tasks sorted by priority then time
owner = st.session_state.owner
if owner and owner.all_tasks():
    scheduler = Scheduler(owner=owner)

    st.markdown("**Current tasks** (sorted by priority, then start time):")
    st.table([
        {
            "Pet":          pet.name,
            "Start":        t.time,
            "Task":         t.title,
            "Duration":     f"{t.duration_minutes} min",
            "Priority":     PRIORITY_EMOJI[t.priority.name],
            "Done":         "✓" if t.completed else "",
        }
        for pet in owner.pets
        for t in scheduler.sort_by_priority_then_time(pet.tasks)
    ])

    # Surface conflict warnings immediately after the task table
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.markdown("**Scheduling conflicts detected:**")
        for warning in conflicts:
            # Strip the leading "WARNING [PetName]: " prefix for a cleaner message
            message = warning.replace("WARNING ", "")
            st.warning(f"⚠️ {message}")
    else:
        st.success("No scheduling conflicts.")
else:
    st.info("No tasks yet. Save an owner & pet, then add tasks above.")

st.divider()

# ── Section 3: Generate Schedule ──────────────────────────────────────────────
st.subheader("3. Generate Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner & pet first.")
    elif not st.session_state.owner.all_pending_tasks():
        st.warning("No pending tasks to schedule. Add some tasks first.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner)

        # Re-surface conflicts at schedule time so they aren't missed
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.markdown("**Resolve these conflicts before finalising your plan:**")
            for warning in conflicts:
                message = warning.replace("WARNING ", "")
                st.warning(f"⚠️ {message}")

        plan = scheduler.generate_plan()

        st.success(f"Schedule ready — {sum(t.duration_minutes for t in plan.scheduled_tasks)} / {owner.available_minutes_per_day} min used")

        if plan.scheduled_tasks:
            st.markdown("**Scheduled tasks:**")
            time_elapsed = 0
            rows = []
            for t in plan.scheduled_tasks:
                rows.append({
                    "Task":         t.title,
                    "Priority":     PRIORITY_EMOJI[t.priority.name],
                    "Start (min)":  time_elapsed,
                    "End (min)":    time_elapsed + t.duration_minutes,
                    "Duration":     f"{t.duration_minutes} min",
                })
                time_elapsed += t.duration_minutes
            st.table(rows)

        if plan.skipped_tasks:
            st.markdown("**Skipped (not enough time):**")
            for t in plan.skipped_tasks:
                st.warning(f"⏭️ **{t.title}** {PRIORITY_EMOJI[t.priority.name]} needs {t.duration_minutes} min")
