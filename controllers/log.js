const Student = require("../database/models/student");
const Lesson = require("../database/models/lesson");
const Log = require("../database/models/log");
const { isValidObjectId } = require("../handlers/misc");
const { onLogFail } = require("../utils/log");

/** @type { import('express').RequestHandler } */
const logInteraction = async (req, res) => {
  const { action, date_client } = req.body;
  const { id } = req.params;

  const query = {};
  if (isValidObjectId(id)) query._id = id;
  else query.id = id;

  try {
    const user_id = req.user ? req.user._id : null;

    const lesson = await Lesson.findOne(query);
    const student = await Student.findOne({ _id: user_id });

    if (lesson && student) {
      const data = {
        student: student._id,
        lesson: lesson._id,
        action: action,
        date_client: date_client,
      };

      data.duration = req.body.duration || 0;

      try {
        await new Log(data).save();

        return res.send({ success: true });
      } catch (error) {
        onLogFail(data);
      }
    }
    return res.send({ success: false });
  } catch (error) {
    console.log(error);
    return res.status(500).send({ success: false });
  }
};

// Logged actions we analyse -> name in the summary. Seeks are logged at the position the student
// landed on, so a "rewind" at minute 18 means a student jumped back to re-watch from minute 18.
const BEHAVIOUR_ACTIONS = { pause: "pauses", backward_seek: "rewinds", forward_seek: "skips" };

/**
 * Viewing behaviour for the lesson's owner (TeachMate uses it): pauses, jumps back (rewinds) and jumps
 * forward (skips) per video minute, plus how far each student got. Optional ?min=&max= adds a summary of
 * that window with each student counted once. Pauses include the automatic pause when a student clicks
 * a feedback button.
 * @type { import('express').RequestHandler }
 */
const getViewingBehaviour = async (req, res) => {
  const { id } = req.params;
  const query = isValidObjectId(id) ? { _id: id } : { id };

  try {
    const lesson = await Lesson.findOne(query);
    if (!lesson) return res.status(404).send({ success: false, message: "Lesson not found" });

    const minutes = lesson.minutes || Math.ceil((lesson.seconds || 0) / 60);
    const lengthSeconds = lesson.seconds || minutes * 60;
    const toMinute = (seconds) => Math.min(Math.max(Math.ceil((Number(seconds) || 0) / 60), 1), Math.max(minutes, 1));
    const hasWindow = req.query.min !== undefined && req.query.max !== undefined;
    const windowStart = parseInt(req.query.min, 10) || 0;
    const windowEnd = parseInt(req.query.max, 10) || minutes;

    const perMinute = Array.from({ length: minutes }, (_, i) => ({ minute: i + 1, pauses: new Set(), rewinds: new Set(), skips: new Set(), counts: { pauses: 0, rewinds: 0, skips: 0 } }));
    const totals = { pauses: 0, rewinds: 0, skips: 0 };
    const windowStudents = { pauses: new Set(), rewinds: new Set(), skips: new Set() };
    const windowCounts = { pauses: 0, rewinds: 0, skips: 0 };
    const furthest = {};

    const logs = await Log.find({ lesson: lesson._id }, { student: 1, action: 1, duration: 1 }).lean();
    logs.forEach((log) => {
      const student = String(log.student);
      furthest[student] = Math.max(furthest[student] || 0, Number(log.duration) || 0);
      const key = BEHAVIOUR_ACTIONS[log.action];
      if (!key || !minutes) return;
      const minute = toMinute(log.duration);
      perMinute[minute - 1][key].add(student);
      perMinute[minute - 1].counts[key] += 1;
      totals[key] += 1;
      if (hasWindow && minute > windowStart && minute <= windowEnd) {
        windowStudents[key].add(student);
        windowCounts[key] += 1;
      }
    });

    const students = Object.keys(furthest);
    const nearEnd = lengthSeconds * 0.9;
    const reachedEnd = students.filter((s) => furthest[s] >= nearEnd).length;
    const stoppedAt = Array.from({ length: minutes }, () => 0);
    students.filter((s) => furthest[s] < nearEnd).forEach((s) => (stoppedAt[toMinute(furthest[s]) - 1] += 1));

    const summary = (sets, counts) =>
      Object.keys(BEHAVIOUR_ACTIONS).reduce((acc, action) => {
        const key = BEHAVIOUR_ACTIONS[action];
        return { ...acc, [key]: counts[key], [`${key}_students`]: sets[key].size };
      }, {});

    return res.send({
      success: true,
      behaviour: {
        minutes,
        students_with_logs: students.length,
        watched: (lesson.watched || []).length,
        totals,
        reached_end: reachedEnd,
        reached_end_pct: students.length ? Math.round((1000 * reachedEnd) / students.length) / 10 : 0,
        per_minute: perMinute.map((m) => ({ minute: m.minute, ...summary(m, m.counts) })),
        stopped_at: stoppedAt.map((count, i) => ({ minute: i + 1, students: count })).filter((s) => s.students),
        window: hasWindow ? { start_min: windowStart, end_min: windowEnd, ...summary(windowStudents, windowCounts) } : null,
      },
    });
  } catch (error) {
    console.log(error);
    return res.status(500).send({ success: false, message: "Internal server error" });
  }
};

module.exports = {
  logInteraction,
  getViewingBehaviour,
};
