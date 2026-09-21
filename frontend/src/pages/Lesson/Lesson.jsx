import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./Lesson.css";

const Lesson = () => {
  const navigate = useNavigate();

  const [lessons, setLessons] = useState([
    {
      id: 1,
      name: "Introduction to Communication Engineering",
      duration: "12:45",
    },
    {
      id: 2,
      name: "Signals and Systems",
      duration: "18:32",
    },
    {
      id: 3,
      name: "Analog Communication",
      duration: "21:15",
    },
    {
      id: 4,
      name: "Digital Communication",
      duration: "16:40",
    },
  ]);

  const [showForm, setShowForm] = useState(false);
  const [newLesson, setNewLesson] = useState("");

  const handleCreateLesson = () => {
    if (!newLesson.trim()) {
      alert("Please enter a lesson name.");
      return;
    }

    const lesson = {
      id: lessons.length + 1,
      name: newLesson,
      duration: "00:00",
    };

    setLessons([...lessons, lesson]);
    setNewLesson("");
    setShowForm(false);
  };

  const openDashboard = (lesson) => {
    navigate("/dashboard", {
      state: {
        lesson: lesson,
      },
    });
  };

  return (
    <>
      <Navbar />

      <div className="lesson-page">

        {/* Header */}
        <div className="lesson-header">

          <div>
            <p className="course-label">COURSE</p>

            <h1>
              Communication Engineering
            </h1>

            <p className="lesson-count">
              {lessons.length} Lessons
            </p>
          </div>

          <button
            className="new-lesson-btn"
            onClick={() => setShowForm(!showForm)}
          >
            + New Lesson
          </button>

        </div>

        {/* Create Lesson Form */}
        {showForm && (
          <div className="new-lesson-form">

            <input
              type="text"
              placeholder="Enter lesson name"
              value={newLesson}
              onChange={(e) => setNewLesson(e.target.value)}
            />

            <button onClick={handleCreateLesson}>
              Create Lesson
            </button>

          </div>
        )}

        {/* Lesson Table */}
        <div className="lesson-card">

          <div className="table-header">

            <span>Lesson</span>

            <span>Duration</span>

            <span>Actions</span>

          </div>

          {lessons.map((lesson) => (

            <div
              className="lesson-row"
              key={lesson.id}
            >

              <div className="lesson-info">

                <div className="lesson-number">
                  {lesson.id}
                </div>

                <div>
                  <h3>{lesson.name}</h3>

                  <p>
                    Lesson {lesson.id}
                  </p>
                </div>

              </div>

              <div className="duration">
                {lesson.duration}
              </div>

              <div className="lesson-actions">

                <button
                  title="Analytics"
                  onClick={() => openDashboard(lesson)}
                >
                  📊
                </button>

                <button title="Share">
                  🔗
                </button>

                <button title="More Options">
                  ⋮
                </button>

              </div>

            </div>

          ))}

        </div>

      </div>
    </>
  );
};

export default Lesson;