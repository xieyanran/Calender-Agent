"""Ladok data source -- intentionally not implemented yet.

Before writing this, I read the actual source of the `ladok3` package
(github.com/dbosk/ladok3, the only real open-source Python wrapper for
Ladok). Its whole API surface is built for staff reporting grades:
create/update/finalize results, look up a student's result history, manage
course rounds, grading rights, attestants/reporters. The closest things to
"registration" are `Student.courses()` (courses you're registered in, a
fact) and `examination_occasions_JSON` (scheduled exam sessions for a
course). Nothing in it looks like "registration window" or "registration
deadline" -- which is the actual thing we want on the calendar. It's also
unverified whether a plain student account (vs. staff/TA with grading
rights) can authenticate into this API at all.

So this needs a decision before it's worth writing code:

1. Try `ladok3` locally with your own student login and see what
   `ladok3.LadokSession(...).get_student(...)` / `.courses()` actually
   returns -- if it has no deadline-shaped data, it doesn't solve this.
2. Or: open start.ladok.se, log in, open your browser's devtools Network
   tab while viewing "My courses" / "My exams", and see what endpoint the
   student-facing site itself calls -- that may be a more direct path than
   reusing a staff-oriented library.
3. Or: registration/exam-registration deadlines are typically a handful of
   fixed dates per term -- if neither of the above pans out, just maintain
   those dates by hand in config.yaml and let the sync script write them
   as plain events, skipping automated fetching entirely.

See the plan/README for context.
"""

from __future__ import annotations

from src.normalize import Event


def fetch() -> list[Event]:
    raise NotImplementedError(
        "Ladok source not implemented -- see the module docstring for why, "
        "and the decision needed before writing it."
    )
