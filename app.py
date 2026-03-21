import streamlit as st
from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown("Welcome to **PawPal+** — your pet care planning assistant.")

st.divider()

# --- Session State Initialization ---
# st.session_state persists across reruns so Owner/Pet data is not wiped on each button click.
if "owner" not in st.session_state:
    st.session_state.owner = None

# ── Section 1: Owner & Pet Setup ──────────────────────────────────────────────
st.subheader("1. Owner & Pet Setup")

owner_name = st.text_input("Owner name", value="Jordan")
available_time = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=60)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save owner & pet"):
    pet = Pet(name=pet_name, species=species)
    # Owner.add_pet() adds the pet to owner.pets
    owner = Owner(name=owner_name, available_minutes_per_day=int(available_time), pets=[pet])
    st.session_state.owner = owner
    st.success(f"Saved! {owner_name} is caring for {pet_name} ({species}) with {available_time} min today.")

st.divider()

# ── Section 2: Add Tasks ───────────────────────────────────────────────────────
st.subheader("2. Add Tasks")

# Map the string values from the selectbox to the Priority enum
PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    if st.session_state.owner is None:
        st.warning("Please save an owner & pet first.")
    else:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority_str],
        )
        # Pet.add_task() appends the Task to pet.tasks
        st.session_state.owner.pets[0].add_task(task)
        st.success(f"Added task: {task_title}")

# Display all current tasks across all pets
owner = st.session_state.owner
if owner and owner.all_tasks():
    st.write("Current tasks:")
    st.table([
        {"pet": pet.name, "task": t.title, "duration (min)": t.duration_minutes, "priority": t.priority.name}
        for pet in owner.pets
        for t in pet.tasks
    ])
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
        # Scheduler.generate_plan() sorts by priority and fits tasks into the time budget
        scheduler = Scheduler(owner=st.session_state.owner)
        plan = scheduler.generate_plan()
        st.success("Schedule generated!")
        st.text(plan.explain())
