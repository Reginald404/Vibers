import calendar
import sqlite3
from datetime import date, timedelta, datetime

CONFIG = {
    "anchor_date": date(2026, 10, 1),
    "anchor_cycle_day": 1,
    "cycle_length": 7,
    "default_window_days": 42,
}

BLOCKS = ["Time Block 1", "Time Block 2"]

con = sqlite3.connect("scheduler.db")
con.execute("CREATE TABLE IF NOT EXISTS suspended (date TEXT PRIMARY KEY)")
con.execute("CREATE TABLE IF NOT EXISTS appointments "
            "(date TEXT, block TEXT, student TEXT, PRIMARY KEY (date, block))")
con.commit()


def generate_schedule(num_calendar_days=None):
    if num_calendar_days is None:
        num_calendar_days = CONFIG["default_window_days"]

    suspended = {row[0] for row in con.execute("SELECT date FROM suspended")}

    schedule = []
    cycle_day = CONFIG["anchor_cycle_day"]
    current = CONFIG["anchor_date"]
    scanned = 0

    while scanned < num_calendar_days:
        if current.weekday() < 5:
            key = current.isoformat()

            if key in suspended:
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
    con.execute("INSERT OR IGNORE INTO suspended VALUES (?)", (date_str,))
    con.commit()
    print(f"{date_str} marked as suspended.")


def unmark_suspended(date_str):
    cur = con.execute("DELETE FROM suspended WHERE date = ?", (date_str,))
    con.commit()
    if cur.rowcount:
        print(f"{date_str} is no longer suspended.")
    else:
        print(f"{date_str} was not suspended.")


def booked_name(date_str, block):
    row = con.execute("SELECT student FROM appointments WHERE date = ? AND block = ?",
                      (date_str, block)).fetchone()
    return row[0] if row else None


def print_schedule(days=20):
    schedule = generate_schedule(days)
    print(
        f"\n{'Date':<12} {'Day':<4} {'Cycle':<8} {'Time Block 1':<16} {'Time Block 2':<16}")
    print("-" * 60)
    for e in schedule:
        if e["status"] == "suspended":
            print(f"{e['date']:<12} {e['weekday']:<4} {'--':<8} suspended")
            continue
        b1 = booked_name(e["date"], BLOCKS[0]) or "open"
        b2 = booked_name(e["date"], BLOCKS[1]) or "open"
        print(
            f"{e['date']:<12} {e['weekday']:<4} {'Day ' + str(e['cycle_day']):<8} {b1:<16} {b2:<16}")


def print_month_grid():
    today = datetime.today()
    text = f"{today.year}-{today.month}"
    try:
        year, month = int(text[:4]), int(text[5:7])
        last_day = date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, IndexError):
        print("Not a valid month.")
        return
    span = (last_day - CONFIG["anchor_date"]).days + 1
    info = {e["date"]: e for e in generate_schedule(max(span, 0))}

    print(f"\n{calendar.month_name[month]} {year}".center(42))
    print("".join(f"{name:<6}" for name in [
          "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]))
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(year, month):
        line = ""
        for day in week:
            if day == 0:
                line += " " * 6
                continue
            e = info.get(date(year, month, day).isoformat())
            if e is None:
                line += f"{day:>2}    "
            elif e["status"] == "suspended":
                line += f"{day:>2} --  "
            else:
                line += f"{day:>2} D{e['cycle_day']}  "
        print(line)
    print("D = cycle day, -- = suspended")


def book_block():
    date_str = input("Date (YYYY-MM-DD): ").strip()

    # only allow dates that are normal school days in the schedule
    valid = {e["date"]
             for e in generate_schedule(365) if e["status"] == "normal"}
    if date_str not in valid:
        print("That date is not an open weekday.")
        return

    for i, name in enumerate(BLOCKS, 1):
        taken = booked_name(date_str, name)
        print(f"{i}. {name}: {taken or 'open'}")
    choice = input("Block number: ").strip()
    if choice not in ("1", "2"):
        print("Not a valid block.")
        return

    student = input("Student name: ").strip()
    if not student:
        print("A name is required.")
        return

    try:
        con.execute("INSERT INTO appointments VALUES (?, ?, ?)",
                    (date_str, BLOCKS[int(choice) - 1], student))
        con.commit()
        print("Booked.")
    except sqlite3.IntegrityError:
        print("That block is already booked.")


def cancel_booking():
    date_str = input("Date (YYYY-MM-DD): ").strip()

    found = []
    for name in BLOCKS:
        student = booked_name(date_str, name)
        if student:
            found.append(name)
            print(f"{len(found)}. {name}: {student}")
    if not found:
        print("No bookings on that date.")
        return

    choice = input("Booking number to cancel: ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(found):
        print("Not a valid booking.")
        return

    con.execute("DELETE FROM appointments WHERE date = ? AND block = ?",
                (date_str, found[int(choice) - 1]))
    con.commit()
    print("Booking cancelled.")


def main():
    menu = """
==== Cycle-Day Scheduler ====
1. View schedule
2. View month grid
3. Mark a date suspended
4. Un-suspend a date
5. Book a time block
6. Cancel a booking
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
            print_month_grid()

        elif choice == "3":
            d = input("Date to suspend (YYYY-MM-DD): ").strip()
            mark_suspended(d)

        elif choice == "4":
            d = input("Date to un-suspend (YYYY-MM-DD): ").strip()
            unmark_suspended(d)

        elif choice == "5":
            book_block()

        elif choice == "6":
            cancel_booking()

        elif choice == "0":
            break

        else:
            print("Not a valid option.")


if __name__ == "__main__":
    main()
