/**
 * Seeds a demo course with synthetic DEBE feedback so the teacher dashboard
 * (and the TeachMate assistant) have realistic data to work with.
 *
 * Lesson patterns are modelled on the real-life examples in
 * Chavan & Mitra (2022), JLA 9(3) — section 5.1 and Appendix B.
 *
 * Usage:
 *   node data/seed-demo.js                      # create/refresh demo teacher + course
 *   node data/seed-demo.js --teacher you@x.com  # attach the demo course to an existing teacher
 *   node data/seed-demo.js --remove             # delete everything this script created
 *
 * Re-running is safe: previous demo data is removed first. Output is
 * deterministic (seeded RNG), so the same data is generated every time.
 */
require("dotenv").config();
const mongoose = require("mongoose");
const config = require("../config");
const User = require("../database/models/user");
const Student = require("../database/models/student");
const Course = require("../database/models/course");
const Lesson = require("../database/models/lesson");
const Feedback = require("../database/models/feedback");
const Bookmark = require("../database/models/bookmark");
const Log = require("../database/models/log");
const { feedbackTypes } = require("./data");

const DEMO_TEACHER = { email: "demo.teacher@tcherly.local", password: "Demo@1234", fullname: "Demo Teacher" };
const DEMO_COURSE_NAME = "CS201 - Programming & Systems (Demo)";
const STUDENT_EMAIL_DOMAIN = "demo-student.tcherly.local";
const STUDENT_COUNT = 90;
const STUDENT_PASSWORD = "Student@1234";
// Placeholder video (any public YouTube URL works; the dashboard only needs it for playback).
const DEFAULT_VIDEO = "https://www.youtube.com/watch?v=wn49bJOYAZM";

// ---------------------------------------------------------------------------
// Deterministic RNG
// ---------------------------------------------------------------------------
const mulberry32 = (seed) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const rand = mulberry32(20220924);
const chance = (p) => rand() < p;
const randInt = (min, max) => min + Math.floor(rand() * (max - min + 1));
const pickWeighted = (weights) => {
  const entries = Object.entries(weights).filter(([, w]) => w > 0);
  const total = entries.reduce((s, [, w]) => s + w, 0);
  let r = rand() * total;
  for (const [key, w] of entries) {
    if ((r -= w) <= 0) return key;
  }
  return entries[entries.length - 1][0];
};
const pickOne = (arr) => arr[Math.floor(rand() * arr.length)];

// ---------------------------------------------------------------------------
// Lesson profiles
//
// Each segment covers minutes [from, to) of the video.
//   rate     – probability that a student clicks at all in a given minute
//   weights  – relative likelihood of each DEBE state
//   mode     – "exclusive": a student keeps one state for the whole segment
//              (low Venn overlap); "mixed": states drawn per click, with
//              `overlap` chance of also reporting a second state
//   reasons  – sub-reason weights per state (keys from data/data.js)
//   others   – free-text "Other" reasons per state
// ---------------------------------------------------------------------------
const LESSONS = [
  {
    name: "Demonstration of Java Programs",
    desc: "Java installation, Hello World, a 1-D array program (TestArray) and a 3-D array program (a3DArray).",
    minutes: 30,
    watchRate: 0.62,
    segments: [
      {
        label: "S1: installation, environment variables, compile & run",
        from: 0, to: 6, rate: 0.13, mode: "exclusive",
        weights: { difficult: 0.22, easy: 0.33, boring: 0.2, engaging: 0.25 },
        reasons: {
          difficult: { "ne-bg": 3, "unclear-pres": 2, "too-fast": 1 },
          easy: { "ak-co": 4, "easy-co": 3, "good-exp": 1 },
          boring: { "too-easy": 4, "too-slow-repetitive": 2 },
          engaging: { "good-exp": 2, "pres-style": 2, "interesting-topic": 1 },
        },
      },
      {
        label: "S2: two simple Java programs (Hello World)",
        from: 6, to: 16, rate: 0.16, mode: "mixed", overlap: 0.45,
        weights: { difficult: 0.3, easy: 0.18, boring: 0.1, engaging: 0.42 },
        reasons: {
          difficult: { "ne-exp": 3, "lang-barrier": 2, "ne-bg": 1 },
          easy: { "good-exp": 3, "easy-co": 2 },
          boring: { "too-easy": 2, "pres-style": 1 },
          engaging: { "interesting-egs": 4, "good-exp": 3, "intellectually-chlg": 1 },
        },
      },
      {
        label: "S3: TestArray program (1-D arrays)",
        from: 16, to: 22, rate: 0.22, mode: "mixed", overlap: 0.3,
        weights: { difficult: 0.46, easy: 0.06, boring: 0.32, engaging: 0.16 },
        reasons: {
          difficult: { "ne-exp": 4, "too-fast": 3, "co-difficult": 2, "unclear-pres": 1 },
          easy: { "ak-co": 1 },
          boring: { "too-difficult": 4, "pres-style": 2, "co-not-meaningful": 1 },
          engaging: { "intellectually-chlg": 2, "good-exp": 1 },
        },
        others: { difficult: ["Code on screen is too small to read", "Could not follow the loop logic"] },
      },
      {
        label: "S4: a3DArray program (3-D arrays)",
        from: 22, to: 30, rate: 0.24, mode: "mixed", overlap: 0.5,
        weights: { difficult: 0.48, easy: 0.04, boring: 0.16, engaging: 0.32 },
        reasons: {
          difficult: { "co-difficult": 4, "ne-exp": 3, "too-fast": 2 },
          easy: { "good-exp": 1 },
          boring: { "too-difficult": 2, "too-slow-repetitive": 1 },
          engaging: { "intellectually-chlg": 4, "interesting-egs": 2, "good-exp": 2 },
        },
      },
    ],
    bookmarks: [
      {
        topic: "TestArray program - engagement flips",
        time_from: 16, time_to: 22,
        feedback_type: ["difficult", "boring"],
        linechart_feedback: ["net_difficult", "net_engaging"],
        questions: [{ name: "Why did engagement drop when the array program started?", action: "Check whether the jump from Hello World to arrays was too steep." }],
        actions: [{ question: 0, action: "Revisited array indexing in the live class with a whiteboard trace.", future_action: "Add a short worked example between S2 and S3 in the next offering." }],
      },
    ],
  },
  {
    name: "Segmented and Paged Memory",
    desc: "Segmentation with schematics and animations, paging, and a closing comparison triggered by a question.",
    minutes: 8,
    watchRate: 0.95,
    segments: [
      {
        label: "Segmented memory explained with a schematic and animation",
        from: 0, to: 3, rate: 0.24, mode: "mixed", overlap: 0.35,
        weights: { difficult: 0.12, easy: 0.4, boring: 0.08, engaging: 0.4 },
        reasons: {
          difficult: { "ne-bg": 2, "too-fast": 1 },
          easy: { "good-exp": 4, "teacher-easy": 3, "easy-co": 1 },
          boring: { "too-easy": 1 },
          engaging: { "pres-style": 4, "good-exp": 4, "interesting-topic": 1 },
        },
      },
      {
        label: "Paging: page tables and address translation",
        from: 3, to: 7, rate: 0.12, mode: "exclusive",
        weights: { difficult: 0.4, easy: 0.15, boring: 0.3, engaging: 0.15 },
        reasons: {
          difficult: { "unclear-pres": 3, "ne-exp": 2, "lang-barrier": 1 },
          easy: { "ak-co": 2 },
          boring: { "too-slow-repetitive": 3, "pres-style": 2 },
          engaging: { "interesting-topic": 1 },
        },
      },
      {
        label: "Trigger question + bullet-point summary (segmented vs paged)",
        from: 7, to: 8, rate: 0.55, mode: "mixed", overlap: 0.25,
        weights: { difficult: 0.04, easy: 0.3, boring: 0.03, engaging: 0.63 },
        reasons: {
          difficult: { "too-fast": 1 },
          easy: { "good-exp": 5, "teacher-easy": 2 },
          boring: { "too-easy": 1 },
          engaging: { "good-exp": 5, "intellectually-chlg": 2, "interesting-topic": 1 },
        },
      },
    ],
    bookmarks: [],
  },
  {
    name: "Pentium 4 Case Study",
    desc: "Lecture capture: Pentium 4 pipeline and NetBurst microarchitecture, ending with a bullet-point recap.",
    minutes: 14,
    watchRate: 0.7,
    segments: [
      {
        label: "Introduction and architecture overview",
        from: 0, to: 4, rate: 0.1, mode: "exclusive",
        weights: { difficult: 0.25, easy: 0.3, boring: 0.2, engaging: 0.25 },
        reasons: {
          difficult: { "ne-bg": 2, "lang-barrier": 1 },
          easy: { "ak-co": 2, "good-exp": 1 },
          boring: { "pres-style": 2 },
          engaging: { "interesting-topic": 2 },
        },
        others: { boring: ["Voice is too low"], difficult: ["Cannot hear properly"] },
      },
      {
        label: "NetBurst pipeline stages (audio quality poor)",
        from: 4, to: 10, rate: 0.15, mode: "mixed", overlap: 0.3,
        weights: { difficult: 0.38, easy: 0.07, boring: 0.4, engaging: 0.15 },
        otherRate: 0.35,
        reasons: {
          difficult: { "unclear-pres": 3, "co-difficult": 2, "lang-barrier": 2 },
          easy: { "ak-co": 1 },
          boring: { "pres-style": 4, "too-slow-repetitive": 2, "co-not-meaningful": 1 },
          engaging: { "intellectually-chlg": 1 },
        },
        others: {
          difficult: ["Cannot hear properly", "Voice is not clearly audible", "Sound quality is low"],
          boring: ["Voice is too low", "Voice is not clear", "Audio keeps cutting"],
        },
      },
      {
        label: "Numbered bullet-point recap of key features",
        from: 10, to: 14, rate: 0.22, mode: "mixed", overlap: 0.3,
        weights: { difficult: 0.1, easy: 0.38, boring: 0.1, engaging: 0.42 },
        reasons: {
          difficult: { "too-fast": 1 },
          easy: { "good-exp": 4, "teacher-easy": 3 },
          boring: { "too-easy": 1 },
          engaging: { "good-exp": 3, "pres-style": 2 },
        },
      },
    ],
    bookmarks: [
      {
        topic: "Audio problems in the pipeline section",
        time_from: 4, time_to: 10,
        feedback_type: ["boring", "difficult"],
        linechart_feedback: ["boring", "difficult"],
        questions: [{ name: "Are students bored by the content, or by the recording quality?", action: "Read the 'Other' reasons for this segment." }],
        actions: [],
      },
    ],
  },
];

const FIRST_NAMES = ["Aarav", "Diya", "Rohan", "Ananya", "Vihaan", "Isha", "Kabir", "Meera", "Arjun", "Sara", "Aditya", "Riya", "Kunal", "Neha", "Yash", "Pooja", "Siddharth", "Tanvi", "Harsh", "Sneha", "Omkar", "Priya", "Nikhil", "Aisha", "Varun", "Kavya", "Rahul", "Shruti", "Dev", "Nisha"];
const LAST_NAMES = ["Patil", "Sharma", "Iyer", "Deshmukh", "Kulkarni", "Reddy", "Nair", "Joshi", "Gupta", "Shah", "Mehta", "Rao"];

// ---------------------------------------------------------------------------
// Feedback generation
// ---------------------------------------------------------------------------
const makeDetails = (state, segment) => {
  const otherRate = segment.otherRate || 0.06;
  const others = segment.others && segment.others[state];
  if (others && chance(otherRate)) return { other: pickOne(others) };
  if (chance(0.15)) return { none: true };
  const reasons = segment.reasons && segment.reasons[state];
  if (!reasons) return { none: true };
  const key = pickWeighted(reasons);
  if (!feedbackTypes[state][key]) throw new Error(`Unknown reason "${key}" for state "${state}"`);
  return { [state]: key };
};

const generateLessonFeedback = (lessonSpec, lesson, students, lessonStart) => {
  const feedbacks = [];
  const logs = [];
  const watchers = students.filter(() => chance(lessonSpec.watchRate));
  const seconds = lessonSpec.minutes * 60;

  watchers.forEach((student) => {
    // How chatty this student is (some click a lot, most click occasionally).
    const activity = 0.35 + rand() * 1.3;
    const startedAt = lessonStart + randInt(0, 3 * 24 * 3600) * 1000;
    const at = (sec) => new Date(startedAt + sec * 1000 + randInt(0, 400) * 1000);

    logs.push({ student: student._id, lesson: lesson._id, action: "lesson_joined", date_client: at(0) });
    logs.push({ student: student._id, lesson: lesson._id, action: "play", duration: 0, date_client: at(0) });

    lessonSpec.segments.forEach((segment) => {
      const stance = pickWeighted(segment.weights);

      for (let minute = segment.from; minute < segment.to; minute++) {
        if (!chance(Math.min(0.95, segment.rate * activity))) continue;

        const states = new Set();
        if (segment.mode === "exclusive") {
          states.add(chance(0.85) ? stance : pickWeighted(segment.weights));
        } else {
          states.add(pickWeighted(segment.weights));
          if (chance(segment.overlap || 0)) states.add(pickWeighted(segment.weights));
        }

        states.forEach((state) => {
          const sec = Math.min(seconds - 6, Math.max(6, minute * 60 + randInt(1, 59)));
          feedbacks.push({
            seconds: sec,
            [state]: true,
            details: makeDetails(state, segment),
            lesson: lesson._id,
            student_id: student._id,
            ip: "127.0.0.1",
            date_client: at(sec),
          });
          // Clicking a DEBE button pauses the video; the student resumes afterwards.
          logs.push({ student: student._id, lesson: lesson._id, action: "pause", duration: sec, date_client: at(sec) });
          logs.push({ student: student._id, lesson: lesson._id, action: "play", duration: sec, date_client: at(sec + 20) });
          if (state === "difficult" && chance(0.3)) {
            logs.push({ student: student._id, lesson: lesson._id, action: "backward_seek", duration: Math.max(0, sec - randInt(15, 60)), date_client: at(sec + 25) });
          }
          if (state === "boring" && chance(0.3)) {
            logs.push({ student: student._id, lesson: lesson._id, action: "forward_seek", duration: Math.min(seconds, sec + randInt(20, 90)), date_client: at(sec + 25) });
          }
        });
      }
    });

    logs.push({ student: student._id, lesson: lesson._id, action: "lesson_leave", duration: seconds, date_client: at(seconds) });
  });

  // Roughly chronological insertion, like real traffic.
  feedbacks.sort((a, b) => a.date_client - b.date_client);
  return { watchers, feedbacks, logs };
};

// ---------------------------------------------------------------------------
// Cleanup
// ---------------------------------------------------------------------------
const removeDemoData = async () => {
  const courses = await Course.find({ name: DEMO_COURSE_NAME });
  const lessonIds = courses.flatMap((c) => c.lessons);
  const lessons = await Lesson.find({ _id: { $in: lessonIds } });
  const bookmarkIds = lessons.flatMap((l) => l.bookmarks);

  await Feedback.deleteMany({ lesson: { $in: lessonIds } });
  await Log.deleteMany({ lesson: { $in: lessonIds } });
  await Bookmark.deleteMany({ _id: { $in: bookmarkIds } });
  await Lesson.deleteMany({ _id: { $in: lessonIds } });
  // TeachMate (FastAPI) conversations about these lessons
  await mongoose.connection.collection("teachmate_conversations").deleteMany({ lesson_id: { $in: lessonIds.map(String) } });
  await Course.deleteMany({ _id: { $in: courses.map((c) => c._id) } });
  const students = await Student.deleteMany({ email: new RegExp(`@${STUDENT_EMAIL_DOMAIN.replace(/\./g, "\\.")}$`) });
  const teacher = await User.deleteOne({ email: DEMO_TEACHER.email });

  console.log(`Removed ${courses.length} demo course(s), ${lessons.length} lesson(s), ${students.deletedCount} student(s), ${teacher.deletedCount} demo teacher.`);
};

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const parseArgs = (argv) => {
  const args = { teacher: null, remove: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--teacher") args.teacher = argv[++i];
    else if (argv[i] === "--remove") args.remove = true;
    else if (argv[i] === "--help" || argv[i] === "-h") args.help = true;
  }
  return args;
};

const main = async () => {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log("Usage: node data/seed-demo.js [--teacher <email>] [--remove]");
    return;
  }

  await mongoose.connect(config.db.uri, config.db.options);
  console.log(`Connected to ${config.db.uri}`);

  await removeDemoData();
  if (args.remove) return;

  // Teacher
  let teacher;
  if (args.teacher) {
    teacher = await User.findOne({ email: args.teacher });
    if (!teacher) throw new Error(`No teacher account with email ${args.teacher}. Register it first or omit --teacher.`);
    if (teacher.feature_level !== "advanced") {
      teacher.feature_level = "advanced";
      await teacher.save();
    }
  } else {
    teacher = new User({
      email: DEMO_TEACHER.email,
      fullname: DEMO_TEACHER.fullname,
      organization: "Tcherly Demo",
      mode: "online",
      feature_level: "advanced",
      contact_for_research: false,
      tour: { dashboard: 1 },
      verified: true,
    });
    teacher.password = await teacher.hashPassword(DEMO_TEACHER.password);
    await teacher.save();
  }

  // Students (hash once; bcrypt with 13 rounds is slow)
  const studentHash = await new Student().hashPassword(STUDENT_PASSWORD);
  const studentDocs = Array.from({ length: STUDENT_COUNT }).map((_, i) => ({
    email: `student${String(i + 1).padStart(2, "0")}@${STUDENT_EMAIL_DOMAIN}`,
    name: `${FIRST_NAMES[i % FIRST_NAMES.length]} ${LAST_NAMES[(i * 7) % LAST_NAMES.length]}`,
    password: studentHash,
  }));
  const students = await Student.insertMany(studentDocs);

  // Course + lessons
  const course = await new Course({ name: DEMO_COURSE_NAME, user: teacher._id, lessons: [] }).save();
  const baseTime = Date.now() - 21 * 24 * 3600 * 1000;

  const summary = [];
  for (let li = 0; li < LESSONS.length; li++) {
    const spec = LESSONS[li];
    const slug = spec.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") + "-demo" + (li + 1);
    const lesson = new Lesson({
      id: slug,
      name: spec.name,
      desc: spec.desc,
      user: teacher._id,
      course: course._id,
      youtube_link: spec.youtube_link || DEFAULT_VIDEO,
      seconds: spec.minutes * 60,
      minutes: spec.minutes,
      watched: [],
      bookmarks: [],
    });

    const { watchers, feedbacks, logs } = generateLessonFeedback(spec, lesson, students, baseTime + li * 7 * 24 * 3600 * 1000);
    lesson.watched = watchers.map((s) => String(s._id));

    for (const bm of spec.bookmarks) {
      const bookmark = await new Bookmark({ threshold: 0, ...bm }).save();
      lesson.bookmarks.push(bookmark._id);
    }

    await lesson.save();
    await Feedback.insertMany(feedbacks);
    await Log.insertMany(logs);
    course.lessons.push(lesson._id);

    const responders = new Set(feedbacks.map((f) => String(f.student_id))).size;
    summary.push({ lesson: spec.name, slug, minutes: spec.minutes, watched: watchers.length, responded: responders, clicks: feedbacks.length, logs: logs.length });
  }
  await course.save();

  console.table(summary);
  console.log(`\nCourse: ${DEMO_COURSE_NAME}`);
  if (args.teacher) {
    console.log(`Attached to existing teacher: ${teacher.email}`);
  } else {
    console.log(`Teacher login: ${DEMO_TEACHER.email} / ${DEMO_TEACHER.password}`);
  }
  console.log(`Student logins: student01..student${STUDENT_COUNT}@${STUDENT_EMAIL_DOMAIN} / ${STUDENT_PASSWORD}`);
};

main()
  .catch((error) => {
    console.error(error.message || error);
    process.exitCode = 1;
  })
  .finally(() => mongoose.disconnect());
