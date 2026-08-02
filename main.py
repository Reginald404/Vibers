from datetime import date, timedelta

CONFIG = {
    "anchor_date": date(2026, 8, 3),
    "anchor_cycle_day": 1,
    "cycle_length": 7,
    "default_window_days": 42,
}

# "2026-08-04": "suspended"  format
exceptions = {}


def generate_schedule(num_calendar_days=None):

    if num_calendar_days is None:
        num_calendar_days = CONFIG["default_window_days"]

    schedule = []
    cycle_day = CONFIG["anchor_cycle_day"]
    current = CONFIG["anchor_date"]
    scanned = 0

    while scanned < num_calendar_days:
        if current.weekday() < 5:
            key = current.isoformat()
            status = exceptions.get(key)

            if status == "suspended":
                schedule.append({
                    "date": key, "weekday": current.strftime("%a"),
                    "cycle_day": None, "status": "suspended",
                })
            else:
                schedule.append({
                    "date": key, "weekday": current.strftime("%a"),
                    "cycle_day": cycle_day, "status": "normal",
                })
                cycle_day = cycle_day % CONFIG["cycle_length"] + 1

        current += timedelta(days=1)
        scanned += 1

    return schedule


def mark_suspended(date_str):
    exceptions[date_str] = "suspended"
    print(f"{date_str} marked as suspended.")


def print_schedule(days=20):
    schedule = generate_schedule(days)
    print(f"\n{'Date':<12} {'Day':<4} {'Cycle':<10} {'Status':<10}")
    print("-" * 40)
    for e in schedule:
        cycle_label = f"Day {e['cycle_day']}" if e["cycle_day"] else "--"
        print(
            f"{e['date']:<12} {e['weekday']:<4} {cycle_label:<10} {e['status']:<10}")


def main():
    menu = """
==== Cycle-Day Scheduler (POC) ====
1. View schedule
2. Mark a date suspended
0. Exit
"""
    while True:
        print(menu)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            try:
                n = input("How many calendar days to show? [20]: ").strip()
                print_schedule(int(n) if n else 20)
            except ValueError:
                print_schedule()

        elif choice == "2":
            d = input("Date to suspend (YYYY-MM-DD): ").strip()
            mark_suspended(d)

        elif choice == "0":
            break

        else:
            print("Not a valid option.")


if __name__ == "__main__":
    main()
