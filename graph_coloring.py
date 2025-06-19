# === graph_coloring.py ===

def generate_initial_schedule(subjects, teachers, classrooms, classes, teacher_availability):
    """
    Improved version:
    - Groups teacher slots by day
    - Prefers different days for each lecture
    - Checks room capacity and conflict
    - Reports shortage if not enough slots
    """

    schedule = []
    shortages = []

    used_teacher_slots = {}
    used_classroom_slots = {}
    used_class_slots = {}
    classroom_load = {c['id']: 0 for c in classrooms}

    # Build teacher_id -> slots grouped by day
    teacher_day_slots = {}
    for row in teacher_availability:
        t_id = row['teacher_id']
        day = row['day']
        start = int(row['start_hour'])
        end = int(row['end_hour'])
        slots = []
        for hour in range(start, end):
            if hour < 12:
                slot = f"{day} {hour}AM"
            else:
                pm_hour = hour - 12 if hour > 12 else 12
                slot = f"{day} {pm_hour}PM"
            slots.append(slot)
        teacher_day_slots.setdefault(t_id, {}).setdefault(day, []).extend(slots)

    # Fallback: if teacher has no slots at all
    for t in teachers:
        if t['id'] not in teacher_day_slots:
            fallback = {}
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
                fallback[day] = [f"{day} {hour}AM" for hour in range(9, 12)]
            teacher_day_slots[t['id']] = fallback

    days_order = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    # Now, schedule each subject
    for subject in subjects:
        teacher_id = subject['teacher_id']
        class_id = subject['class_id']
        needed = int(subject['num_lectures'])
        assigned = 0

        teacher_slots_by_day = teacher_day_slots[teacher_id]

        # Try to spread over different days first
        pass_num = 0
        while assigned < needed:
            assigned_in_pass = False

            for day in days_order:
                slots = teacher_slots_by_day.get(day, [])
                for slot in slots:
                    # pick rooms big enough
                    good_rooms = [r for r in classrooms if r['capacity'] >= subject['num_students']]
                    sorted_rooms = sorted(good_rooms, key=lambda r: classroom_load[r['id']])

                    for room in sorted_rooms:
                        if used_teacher_slots.get((teacher_id, slot)):
                            continue
                        if used_classroom_slots.get((room['id'], slot)):
                            continue
                        if used_class_slots.get((class_id, slot)):
                            continue

                        # assign
                        schedule.append({
                            'subject_id': subject['id'],
                            'teacher_id': teacher_id,
                            'classroom_id': room['id'],
                            'class_id': class_id,
                            'timeslot': slot
                        })

                        used_teacher_slots[(teacher_id, slot)] = True
                        used_classroom_slots[(room['id'], slot)] = True
                        used_class_slots[(class_id, slot)] = True
                        classroom_load[room['id']] += 1

                        assigned += 1
                        assigned_in_pass = True
                        break  # done with this room

                    if assigned_in_pass:
                        break  # done with this slot

                if assigned_in_pass:
                    break  # done with this day

            if not assigned_in_pass:
                # No more free slots anywhere
                break

            pass_num += 1

        if assigned < needed:
            shortages.append({
                'subject': subject['name'],
                'needed': needed,
                'assigned': assigned
            })

    return schedule, shortages
