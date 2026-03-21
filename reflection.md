# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

A user should be able to do the following actions:
- Add/manage pet tasks — enter a task (e.g., "Morning walk"), its duration, and priority level
- Generate a daily schedule — trigger the scheduler to produce an ordered plan based on available time and task priorities
- View the plan with reasoning — see which tasks were chosen, when they happen, and why

It will have the following classes: 
1) Owner
Attributes: name, available_minutes_per_day
Responsibility: Represents the human user and their time constraints

2) Pet
Attributes: name, species
Responsibility: Represents the pet being cared for; could later hold species-specific needs

3) Task
Attributes: title, duration_minutes, priority (low/medium/high)
Responsibility: Encapsulates a single care activity and its scheduling weight

4) Scheduler
Attributes: owner, pet, tasks: list[Task]
Methods: generate_plan() → Plan
Responsibility: Core logic — selects and orders tasks that fit within the owner's available time, prioritizing high-priority tasks first

5) Plan
Attributes: scheduled_tasks: list[Task], skipped_tasks: list[Task]
Methods: explain() → str
Responsibility: Holds the output of a scheduling run and can produce a human-readable explanation of decisions made

Relationships between the above classes:
Owner has one Pet
Scheduler takes an Owner, a Pet, and a list of Tasks
Scheduler.generate_plan() returns a Plan

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes
1) Originally owner assumes one pet. 
owner.pet: Pet is a single object. If the scope ever grows to multiple pets, this becomes a breaking change. A list[Pet] from the start is safer, so made the change. 

2) Scheduler lost its Pet reference
In the original UML, Scheduler takes owner, pet, and tasks. Currently it only holds owner and tasks. Because Pet is already accessible via owner.pet, this is technically reachable (but it's implicit).

3) Priority originally was an unvalidated string.
Task.priority is typed as str but valid values are "low", "medium", "high". Nothing enforces this. When generate_plan() sorts by priority, a typo like "hig" silently misbehaves. So I Replaced it with an Enum ( LOW = 1, MEDIUM = 2, HIGH = 3) to make comparisons and sorting reliable.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
