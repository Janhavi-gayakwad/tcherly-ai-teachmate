import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./TeacherDashboard.css";
import DashboardCards from "../../components/DashboardCards/DashboardCards";

const TeacherDashboard = () => {

  const navigate = useNavigate();

  const [lessons, setLessons] = useState([]);

  const [showOptions, setShowOptions] = useState(false);


  useEffect(() => {
  const savedLessons =
    JSON.parse(localStorage.getItem("teacherLessons")) || [];

  setLessons(savedLessons);
  }, []);

  return (
    <>
      <Navbar />

      <div className="dashboard-container">

        {/* COURSE HEADER */}

        <div className="course-header">

          <h2>
            Course:
            <span>
              Mathematical Foundations for Data Analytics
            </span>
          </h2>

          
          <div className="course-actions">

            <button
              className="new-lesson-btn"
              onClick={() =>
                navigate("/new-lesson")
              }
            >
              + New Lesson
            </button>


            <div className="options-wrapper">

              <button
                className="options-btn"
                onClick={() =>
                  setShowOptions(!showOptions)
                }
              >
                ⚙ Options ▾
              </button>


              {showOptions && (

                <div className="options-menu">

                  <button>
                    Edit Course
                  </button>

                  <button>
                    Course Settings
                  </button>

                  <button>
                    Delete Course
                  </button>

                </div>

              )}

            </div>

          </div>

        </div>

        <DashboardCards />
        {/* LESSONS */}

        <div className="lessons-section">

          <h2>
            Your posted lessons
          </h2>


          <table className="lessons-table">

            <thead>

              <tr>

                <th>
                  Lesson
                  <br />
                  No
                </th>

                <th>
                  Lesson Name
                </th>

                <th className="actions-heading">
                  Actions
                </th>

              </tr>

            </thead>


            <tbody>

              {lessons.length > 0 ? (

               lessons.map((lesson, index) => (
  <tr key={index}>
    <td>{lesson.lessonNo}</td>

    <td>{lesson.name}</td>

    <td className="lesson-actions">

      <button
        title="Share"
        onClick={() => {
          const link =
            window.location.origin + "/student-lesson";

          navigator.clipboard.writeText(link);

          window.open(link, "_blank");

          alert("Lesson link copied!");
        }}
      >
        ↗
      </button>

      <button
        title="Analytics"
        onClick={() => navigate("/analytics")}
      >
        ▥
      </button>

      <button title="Settings">
        ⚙ ▾
      </button>

    </td>
  </tr>
))

              ) : (

                <tr>

                  <td
                    colSpan="3"
                    className="no-lessons"
                  >
                    No lessons posted yet.
                  </td>

                </tr>

              )}

            </tbody>

          </table>

        </div>

      </div>
    </>
  );
};

export default TeacherDashboard;