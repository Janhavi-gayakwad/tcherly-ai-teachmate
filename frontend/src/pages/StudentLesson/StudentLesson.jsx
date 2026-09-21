import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar/Navbar";
import "./StudentLesson.css";

const StudentLesson = () => {
  const [lesson, setLesson] = useState(null);

  const [selectedFeedback, setSelectedFeedback] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("teacherLesson");

    if (saved) {
      setLesson(JSON.parse(saved));
    }
  }, []);

  const handleFeedback = (type) => {
    setSelectedFeedback(type);

    alert(`Feedback Submitted : ${type}`);
  };

  if (!lesson) {
    return (
      <>
        <Navbar />

        <div className="empty-page">
          No lesson available.
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />

      <div className="student-page">

        <div className="video-section">

          <div className="video-player">

            <div className="play-btn">
              ▶
            </div>

          </div>

        </div>

        <div className="lesson-info">

          <h1>{lesson.name}</h1>

          <p>{lesson.description}</p>

          <p>

            <strong>Duration:</strong>

            {lesson.duration}

          </p>

        </div>

        <div className="feedback-card">

          <h2>How are you feeling?</h2>

          <div className="feedback-grid">

            <button
              className={
                selectedFeedback === "Difficult"
                  ? "active difficult"
                  : "difficult"
              }
              onClick={() => handleFeedback("Difficult")}
            >
              Difficult
            </button>

            <button
              className={
                selectedFeedback === "Easy"
                  ? "active easy"
                  : "easy"
              }
              onClick={() => handleFeedback("Easy")}
            >
              Easy
            </button>

            <button
              className={
                selectedFeedback === "Boring"
                  ? "active boring"
                  : "boring"
              }
              onClick={() => handleFeedback("Boring")}
            >
              Boring
            </button>

            <button
              className={
                selectedFeedback === "Engaging"
                  ? "active engaging"
                  : "engaging"
              }
              onClick={() => handleFeedback("Engaging")}
            >
              Engaging
            </button>

          </div>

        </div>

      </div>
    </>
  );
};

export default StudentLesson;