import streamlit as st
from datetime import date
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


def task_icon(title: str) -> str:
    """Return a contextual emoji based on keywords in the task title."""
    t = title.lower()
    if any(w in t for w in ("walk", "run", "exercise", "jog")):
        return "🐕"
    if any(w in t for w in ("feed", "food", "meal", "treat", "water")):
        return "🍽️"
    if any(w in t for w in ("medication", "medicine", "pill", "supplement", "drop")):
        return "💊"
    if any(w in t for w in ("groom", "brush", "bath", "wash", "coat", "nail")):
        return "✂️"
    if any(w in t for w in ("vet", "doctor", "check", "appointment")):
        return "🏥"
    if any(w in t for w in ("play", "train", "session", "enrichment", "fetch")):
        return "🎾"
    return "🐾"


def urgency_label(task: Task) -> str:
    """Return a human-readable urgency label based on due date."""
    if task.due_date is None:
        return "—"
    days = (task.due_date - date.today()).days
    if days < 0:
        return f"🚨 Overdue ({abs(days)}d ago)"
    if days == 0:
        return "🔥 Due today"
    if days <= 3:
        return f"⚡ {days}d left"
    if days <= 7:
        return f"📅 {days}d left"
    return f"🗓️ {days}d left"


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

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    task_time = st.text_input("Start time (HH:MM)", value="07:00")
with col5:
    due_date_input = st.date_input("Due date (optional)", value=None)

if st.button("Add task"):
    if st.session_state.owner is None:
        st.warning("Please save an owner & pet first.")
    else:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority_str],
            time=task_time,
            due_date=due_date_input if due_date_input else None,
        )
        st.session_state.owner.pets[0].add_task(task)
        st.session_state.owner.save_to_json()
        st.success(f"Added: {task_icon(task_title)} **{task_title}** at {task_time} ({duration} min, {PRIORITY_EMOJI[priority_str.upper()]})")

# Display tasks sorted by priority then time
owner = st.session_state.owner
if owner and owner.all_tasks():
    scheduler = Scheduler(owner=owner)

    # At-a-glance metrics
    all_tasks = owner.all_tasks()
    pending = owner.all_pending_tasks()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total tasks", len(all_tasks))
    m2.metric("Pending", len(pending))
    m3.metric("Completed", len(all_tasks) - len(pending))

    st.markdown("**Current tasks** (sorted by priority, then start time):")
    st.dataframe(
        [
            {
                "Pet":        pet.name,
                "Start":      t.time,
                "Task":       f"{task_icon(t.title)} {t.title}",
                "Duration":   f"{t.duration_minutes} min",
                "Priority":   PRIORITY_EMOJI[t.priority.name],
                "Due":        urgency_label(t),
                "Score":      f"{scheduler.task_score(t):.1f}",
                "Done":       "✓" if t.completed else "",
            }
            for pet in owner.pets
            for t in scheduler.sort_by_priority_then_time(pet.tasks)
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("💡 **Score** = priority value (1–3) × urgency multiplier (1.0–3.0). Higher score → scheduled first in weighted mode.")

    # Surface conflict warnings immediately after the task table
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.markdown("**Scheduling conflicts detected:**")
        for warning in conflicts:
            message = warning.replace("WARNING ", "")
            st.warning(f"⚠️ {message}")
    else:
        st.success("No scheduling conflicts.")
else:
    st.info("No tasks yet. Save an owner & pet, then add tasks above.")

st.divider()

# ── Section 3: Generate Schedule ──────────────────────────────────────────────
st.subheader("3. Generate Schedule")

use_weighted = st.toggle(
    "Use weighted scoring (priority × urgency)",
    value=False,
    help="When ON, tasks due soon receive a score boost and may be scheduled ahead of higher-priority tasks with no due date.",
)
if use_weighted:
    st.info("**Weighted mode:** score = priority value × urgency multiplier. A 🟢 Low task due *today* (score 3.0) beats a 🟡 Medium task with no due date (score 2.0).")

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

        plan = scheduler.generate_weighted_plan() if use_weighted else scheduler.generate_plan()

        # Summary metrics
        time_used = sum(t.duration_minutes for t in plan.scheduled_tasks)
        budget = owner.available_minutes_per_day
        s1, s2, s3 = st.columns(3)
        s1.metric("Scheduled", len(plan.scheduled_tasks), help="Tasks that fit in your time budget")
        s2.metric("Skipped", len(plan.skipped_tasks), help="Tasks that didn't fit")
        s3.metric("Time used", f"{time_used} / {budget} min")

        # Time budget progress bar
        progress_pct = min(time_used / budget, 1.0)
        st.progress(progress_pct, text=f"Time budget: {time_used} / {budget} min used")

        if plan.scheduled_tasks:
            st.markdown("**Scheduled tasks:**")
            time_elapsed = 0
            rows = []
            for t in plan.scheduled_tasks:
                row = {
                    "Task":        f"{task_icon(t.title)} {t.title}",
                    "Priority":    PRIORITY_EMOJI[t.priority.name],
                    "Start (min)": time_elapsed,
                    "End (min)":   time_elapsed + t.duration_minutes,
                    "Duration":    f"{t.duration_minutes} min",
                }
                if use_weighted:
                    row["Score"] = f"{scheduler.task_score(t):.1f}"
                    row["Due"] = urgency_label(t)
                rows.append(row)
                time_elapsed += t.duration_minutes
            st.dataframe(rows, use_container_width=True, hide_index=True)

        if plan.skipped_tasks:
            st.markdown("**Skipped (not enough time):**")
            for t in plan.skipped_tasks:
                st.warning(f"⏭️ {task_icon(t.title)} **{t.title}** {PRIORITY_EMOJI[t.priority.name]} — needs {t.duration_minutes} min")
