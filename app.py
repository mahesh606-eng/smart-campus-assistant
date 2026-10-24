
from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path
from contextlib import contextmanager

app = Flask(__name__)
DATABASE = Path(__file__).resolve().parent / "campus.db"


# ---------------- DATABASE CONNECTION ----------------

@contextmanager
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def rows_to_list(rows):
    """Convert SQLite rows into JSON-friendly dictionaries."""
    return [dict(row) for row in rows]


# ---------------- DATABASE INITIALIZATION ----------------

def initialize_database():
    with get_db() as db:

        # Existing table: preserved
        db.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL
            )
        """)

        # Existing table: preserved
        db.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL
            )
        """)

        # New table: class timetable
        db.execute("""
            CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                subject TEXT NOT NULL,
                room TEXT NOT NULL,
                faculty TEXT NOT NULL
            )
        """)

        # New table: exam schedules
        db.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                venue TEXT NOT NULL,
                notes TEXT NOT NULL
            )
        """)

        # New table: library information
        db.execute("""
            CREATE TABLE IF NOT EXISTS library_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                details TEXT NOT NULL
            )
        """)

        # Seed existing announcements only if the table is empty.
        if db.execute(
            "SELECT COUNT(*) FROM announcements"
        ).fetchone()[0] == 0:

            db.executemany(
                """
                INSERT INTO announcements (title, message)
                VALUES (?, ?)
                """,
                [
                    (
                        "Welcome to Smart Campus",
                        "Your campus information assistant is ready."
                    ),
                    (
                        "Library Information",
                        "Sample library hours are Monday to Saturday, "
                        "9:00 AM to 5:00 PM. Confirm with your college."
                    ),
                    (
                        "Academic Reminder",
                        "Contact your department for assignment deadlines."
                    ),
                ],
            )

        # Seed existing FAQs only if the table is empty.
        if db.execute(
            "SELECT COUNT(*) FROM faqs"
        ).fetchone()[0] == 0:

            db.executemany(
                """
                INSERT INTO faqs (question, answer)
                VALUES (?, ?)
                """,
                [
                    (
                        "library",
                        "The sample library hours are Monday to Saturday, "
                        "9:00 AM to 5:00 PM. Please confirm with your college."
                    ),
                    (
                        "timetable",
                        "Ask for the timetable or a specific weekday to view the supplied college schedule."
                    ),
                    (
                        "exam",
                        "Open the Exams section to view the sample exam schedule."
                    ),
                    (
                        "attendance",
                        "Contact your department for the applicable attendance rules."
                    ),
                    (
                        "contact",
                        "Visit your department office for verified contact information."
                    ),
                    (
                        "hello",
                        "Hello! Welcome to Smart Campus Assistant. How can I help?"
                    ),
                ],
            )

        # Install the supplied college timetable once. The migration marker
        # ensures this update replaces only old timetable rows and does not
        # overwrite the timetable on every subsequent application start.
        db.execute("""
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        timetable_version = db.execute(
            "SELECT value FROM app_metadata WHERE key = ?",
            ("timetable_version",)
        ).fetchone()

        if not timetable_version or timetable_version["value"] != "MIT-AIDS-5SEM-2026-v1":
            college_timetable = [
                ('Monday', '08:30 AM', '09:30 AM', 'Computer Networks (CN)', 'AD-401', 'Prof. Chandana S (CNS)'),
                ('Monday', '09:30 AM', '10:30 AM', 'Theory of Computation (TOC)', 'AD-401', 'Prof. Mamatha D (MD)'),
                ('Monday', '10:30 AM', '11:00 AM', 'TEA BREAK', 'Campus', '—'),
                ('Monday', '11:00 AM', '12:00 PM', 'Cloud Computing (CC)', 'AD-401', 'Dr. Swarnalatha K (SK)'),
                ('Monday', '12:00 PM', '01:00 PM', 'Software Engineering & Project Management (SEPM)', 'AD-401', 'Prof. Madhuri B (MB)'),
                ('Monday', '01:00 PM', '01:45 PM', 'LUNCH BREAK', 'Campus', '—'),
                ('Monday', '01:45 PM', '02:35 PM', 'Research Methodology (RM)', 'AD-401', 'Dr. GS Madhan Kumar (GSM)'),
                ('Monday', '02:35 PM', '03:25 PM', 'NPTEL', 'AD-401', 'Not specified'),
                ('Monday', '03:25 PM', '04:15 PM', 'FREE', '—', '—'),
                ('Tuesday', '08:30 AM', '09:30 AM', 'Environmental Studies & E-waste Management (ENV)', 'AD-401', 'Prof. Mahadev Prasad N (MPN)'),
                ('Tuesday', '09:30 AM', '10:30 AM', 'Software Engineering & Project Management (SEPM)', 'AD-401', 'Prof. Madhuri B (MB)'),
                ('Tuesday', '10:30 AM', '11:00 AM', 'TEA BREAK', 'Campus', '—'),
                ('Tuesday', '11:00 AM', '12:00 PM', 'Research Methodology (RM)', 'AD-401', 'Dr. GS Madhan Kumar (GSM)'),
                ('Tuesday', '12:00 PM', '01:00 PM', 'Theory of Computation (TOC)', 'AD-401', 'Prof. Mamatha D (MD)'),
                ('Tuesday', '01:00 PM', '01:45 PM', 'LUNCH BREAK', 'Campus', '—'),
                ('Tuesday', '01:45 PM', '04:15 PM', 'CN LAB (B1) / DV LAB (B2)', 'College Lab', 'CN Lab: Prof. Chandana S (CNS); DV Lab: Prof. Mohammed Shamail Farhan (MSF)'),
                ('Wednesday', '08:30 AM', '09:30 AM', 'Computer Networks (CN)', 'AD-401', 'Prof. Chandana S (CNS)'),
                ('Wednesday', '09:30 AM', '10:30 AM', 'Theory of Computation (TOC)', 'AD-401', 'Prof. Mamatha D (MD)'),
                ('Wednesday', '10:30 AM', '11:00 AM', 'TEA BREAK', 'Campus', '—'),
                ('Wednesday', '11:00 AM', '12:00 PM', 'Cloud Computing (CC)', 'AD-401', 'Dr. Swarnalatha K (SK)'),
                ('Wednesday', '12:00 PM', '01:00 PM', 'Environmental Studies & E-waste Management (ENV)', 'AD-401', 'Prof. Mahadev Prasad N (MPN)'),
                ('Wednesday', '01:00 PM', '01:45 PM', 'LUNCH BREAK', 'Campus', '—'),
                ('Wednesday', '01:45 PM', '04:15 PM', 'MINI PROJECT', 'Project Work Area', 'Dr. GS Madhan Kumar (GSM)'),
                ('Thursday', '08:30 AM', '09:30 AM', 'Software Engineering & Project Management (SEPM)', 'AD-401', 'Prof. Madhuri B (MB)'),
                ('Thursday', '09:30 AM', '10:30 AM', 'Theory of Computation (TOC)', 'AD-401', 'Prof. Mamatha D (MD)'),
                ('Thursday', '10:30 AM', '11:00 AM', 'TEA BREAK', 'Campus', '—'),
                ('Thursday', '11:00 AM', '12:00 PM', 'Computer Networks (CN)', 'AD-401', 'Prof. Chandana S (CNS)'),
                ('Thursday', '12:00 PM', '01:00 PM', 'Cloud Computing (CC)', 'AD-401', 'Dr. Swarnalatha K (SK)'),
                ('Thursday', '01:00 PM', '01:45 PM', 'LUNCH BREAK', 'Campus', '—'),
                ('Thursday', '01:45 PM', '04:15 PM', 'PLACEMENT ACTIVITY', 'Placement Area', 'Not specified'),
                ('Friday', '08:30 AM', '09:30 AM', 'Research Methodology (RM)', 'AD-401', 'Dr. GS Madhan Kumar (GSM)'),
                ('Friday', '09:30 AM', '10:30 AM', 'Theory of Computation (TOC) - Tutorials', 'AD-401', 'Prof. Mamatha D (MD)'),
                ('Friday', '10:30 AM', '11:00 AM', 'TEA BREAK', 'Campus', '—'),
                ('Friday', '11:00 AM', '12:00 PM', 'Software Engineering & Project Management (SEPM)', 'AD-401', 'Prof. Madhuri B (MB)'),
                ('Friday', '12:00 PM', '01:00 PM', 'Cloud Computing (CC)', 'AD-401', 'Dr. Swarnalatha K (SK)'),
                ('Friday', '01:00 PM', '01:45 PM', 'LUNCH BREAK', 'Campus', '—'),
                ('Friday', '01:45 PM', '04:15 PM', 'CN LAB (B2) / DV LAB (B1)', 'College Lab', 'CN Lab: Prof. Chandana S (CNS); DV Lab: Prof. Mohammed Shamail Farhan (MSF)'),
            ]

            # Replace timetable entries only; announcements, FAQs, exams, and
            # library records are not modified by this timetable migration.
            db.execute("DELETE FROM timetable")
            db.executemany(
                """
                INSERT INTO timetable
                (day, start_time, end_time, subject, room, faculty)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                college_timetable,
            )
            db.execute(
                """
                INSERT INTO app_metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                ("timetable_version", "MIT-AIDS-5SEM-2026-v1"),
            )

        # Seed clearly labelled demonstration exams.
        if db.execute(
            "SELECT COUNT(*) FROM exams"
        ).fetchone()[0] == 0:

            db.executemany(
                """
                INSERT INTO exams
                (subject, exam_date, start_time, venue, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        "Computer Networks",
                        "2026-11-02",
                        "10:00 AM",
                        "Exam Hall A",
                        "DEMO ONLY - not an official exam date"
                    ),
                    (
                        "Database Management",
                        "2026-11-04",
                        "10:00 AM",
                        "Exam Hall B",
                        "DEMO ONLY - not an official exam date"
                    ),
                    (
                        "Software Engineering",
                        "2026-11-06",
                        "02:00 PM",
                        "Exam Hall A",
                        "DEMO ONLY - not an official exam date"
                    ),
                    (
                        "Operating Systems",
                        "2026-11-09",
                        "10:00 AM",
                        "Exam Hall C",
                        "DEMO ONLY - not an official exam date"
                    ),
                ],
            )

        # Seed library information only when it is empty.
        if db.execute(
            "SELECT COUNT(*) FROM library_info"
        ).fetchone()[0] == 0:

            db.executemany(
                """
                INSERT INTO library_info (title, details)
                VALUES (?, ?)
                """,
                [
                    (
                        "Opening Hours",
                        "Monday to Saturday: 9:00 AM to 5:00 PM "
                        "(sample hours; confirm with your college)."
                    ),
                    (
                        "Location",
                        "Main College Library (sample location)."
                    ),
                    (
                        "Borrowing Rules",
                        "Carry your student ID. Loan periods, book limits, "
                        "and fines must be confirmed with the librarian."
                    ),
                    (
                        "Library Facilities",
                        "Sample facilities: reading space, textbooks, "
                        "reference materials, and study areas."
                    ),
                ],
            )


# ---------------- HOME DASHBOARD ----------------

@app.route("/")
def home():
    with get_db() as db:
        announcements = db.execute(
            "SELECT * FROM announcements ORDER BY id DESC"
        ).fetchall()

    # Keep the existing dashboard template working.
    return render_template(
        "index.html",
        announcements=announcements
    )


# ---------------- ANNOUNCEMENTS API ----------------

@app.route("/api/announcements")
def get_announcements():
    with get_db() as db:
        announcements = db.execute(
            "SELECT * FROM announcements ORDER BY id DESC"
        ).fetchall()

    return jsonify({
        "count": len(announcements),
        "announcements": rows_to_list(announcements)
    })


# ---------------- TIMETABLE API ----------------

@app.route("/api/timetable")
def get_timetable():
    day = request.args.get("day", "").strip()

    valid_days = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    if day and day.lower() not in [d.lower() for d in valid_days]:
        return jsonify({
            "error": "Invalid day. Use Monday through Sunday."
        }), 400

    with get_db() as db:
        if day:
            timetable = db.execute(
                """
                SELECT * FROM timetable
                WHERE LOWER(day) = LOWER(?)
                ORDER BY id
                """,
                (day,)
            ).fetchall()
        else:
            timetable = db.execute(
                """
                SELECT * FROM timetable
                ORDER BY
                    CASE day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                        ELSE 8
                    END,
                    id
                """
            ).fetchall()

    return jsonify({
        "count": len(timetable),
        "sample_data": False,
        "source": "User-provided MIT Thandavapura AI & DS 5th-semester timetable",
        "college": "Maharaja Institute of Technology Thandavapura",
        "department": "Artificial Intelligence and Data Science",
        "semester": "5th Semester, 2026-2027 (22 Scheme)",
        "coordinator": "Prof. Madhuri B",
        "coordinator_room": "AD-401",
        "timetable": rows_to_list(timetable)
    })


# ---------------- EXAMS API ----------------

@app.route("/api/exams")
def get_exams():
    with get_db() as db:
        exams = db.execute(
            "SELECT * FROM exams ORDER BY exam_date, start_time"
        ).fetchall()

    return jsonify({
        "count": len(exams),
        "sample_data": True,
        "exams": rows_to_list(exams)
    })


# ---------------- LIBRARY API ----------------

@app.route("/api/library")
def get_library():
    with get_db() as db:
        information = db.execute(
            "SELECT * FROM library_info ORDER BY id"
        ).fetchall()

    return jsonify({
        "count": len(information),
        "sample_data": True,
        "library": rows_to_list(information)
    })


# ---------------- CHATBOT API ----------------

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "reply": "Please enter a question."
        }), 400

    message = message.strip()

    if len(message) > 500:
        return jsonify({
            "reply": "Please keep your question under 500 characters."
        }), 400

    question = message.lower()

    # Answer timetable questions using the supplied college schedule.
    timetable_intent = any(word in question for word in [
        "timetable", "class schedule", "class time", "today's class",
        "classes on", "class on", "schedule for", "what class",
        "which class", "my classes", "college schedule"
    ])

    if timetable_intent:
        days = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]
        day = next((d for d in days if d.lower() in question), None)

        with get_db() as db:
            if day:
                records = db.execute(
                    """
                    SELECT day, start_time, end_time, subject, room, faculty
                    FROM timetable
                    WHERE LOWER(day) = LOWER(?)
                    ORDER BY id
                    """,
                    (day,)
                ).fetchall()
            else:
                records = db.execute(
                    """
                    SELECT day, start_time, end_time, subject, room, faculty
                    FROM timetable
                    ORDER BY
                        CASE day
                            WHEN 'Monday' THEN 1
                            WHEN 'Tuesday' THEN 2
                            WHEN 'Wednesday' THEN 3
                            WHEN 'Thursday' THEN 4
                            WHEN 'Friday' THEN 5
                            WHEN 'Saturday' THEN 6
                            WHEN 'Sunday' THEN 7
                            ELSE 8
                        END,
                        id
                    LIMIT 12
                    """
                ).fetchall()

        if records:
            heading = (
                f"{day} timetable at MIT Thandavapura:"
                if day else
                "MIT Thandavapura AI & DS 5th-semester timetable (first entries):"
            )
            lines = [
                f"{r['start_time']}–{r['end_time']}: {r['subject']} "
                f"(Room: {r['room']}; Faculty: {r['faculty']})"
                for r in records
            ]
            reply = heading + "\n" + "\n".join(lines)
            reply += (
                "\n\nThis is based on the timetable you supplied. "
                "Please verify uncertain subject codes and classroom details "
                "against the original college timetable."
            )
            return jsonify({"reply": reply, "response": reply})

    if any(word in question for word in [
        "exam", "exams", "exam date", "exam schedule"
    ]):
        with get_db() as db:
            records = db.execute(
                """
                SELECT subject, exam_date, start_time, venue, notes
                FROM exams ORDER BY exam_date LIMIT 5
                """
            ).fetchall()

        if records:
            reply = "Sample exam schedule (not official):\n"
            reply += "\n".join(
                f"{r['subject']}: {r['exam_date']} at "
                f"{r['start_time']}, {r['venue']}."
                for r in records
            )
            return jsonify({"reply": reply, "response": reply})

    if any(word in question for word in [
        "library", "book borrowing", "library timing", "library hours"
    ]):
        with get_db() as db:
            records = db.execute(
                "SELECT title, details FROM library_info ORDER BY id"
            ).fetchall()

        if records:
            reply = "Sample library information:\n"
            reply += "\n".join(
                f"{r['title']}: {r['details']}"
                for r in records
            )
            return jsonify({"reply": reply, "response": reply})

    if any(word in question for word in [
        "announcement", "announcements", "campus news", "notice"
    ]):
        with get_db() as db:
            records = db.execute(
                """
                SELECT title, message FROM announcements
                ORDER BY id DESC LIMIT 5
                """
            ).fetchall()

        if records:
            reply = "Latest campus announcements:\n"
            reply += "\n".join(
                f"{r['title']}: {r['message']}"
                for r in records
            )
            return jsonify({"reply": reply, "response": reply})

    # Preserve the existing FAQ-based chatbot as a fallback.
    with get_db() as db:
        faqs = db.execute(
            "SELECT * FROM faqs ORDER BY id"
        ).fetchall()

    for faq in faqs:
        keyword = faq["question"].lower().strip()

        if keyword and keyword in question:
            return jsonify({"reply": faq["answer"]})

    return jsonify({
        "reply": (
            "I couldn't find a verified answer in the campus knowledge base. "
            "Please contact your department for assistance."
        )
    })


# ---------------- HEALTH CHECK ----------------

@app.route("/api/health")
def health():
    return jsonify({
        "status": "running",
        "application": "Smart Campus Assistant",
        "timetable": "MIT Thandavapura AI & DS 5th-semester schedule"
    })


# Initialize the database before the server starts.
initialize_database()


if __name__ == "__main__":
    app.run(debug=True)
