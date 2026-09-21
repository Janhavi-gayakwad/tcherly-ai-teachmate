import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./CourseSelection.css";

const CourseSelection = () => {
  const navigate = useNavigate();

  const [courses] = useState([
    "Communication Engineering Assessment",
    "Communication Engineering",
    "Mathematical Foundations for Data Analytics",
    "Analysis of Algorithms",
  ]);

  const [selectedCourse, setSelectedCourse] = useState("");
  const [newCourse, setNewCourse] = useState("");

  const handleNext = () => {
    if (selectedCourse || newCourse.trim()) {
      navigate("/lessons");
    } else {
      alert("Please select or create a course.");
    }
  };

  return (
    <>
      <Navbar />

      <div className="course-container">
        <div className="course-card">

          <h2>Select a Course</h2>

          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
          >
            <option value="">Choose One</option>

            {courses.map((course, index) => (
              <option key={index} value={course}>
                {course}
              </option>
            ))}
          </select>

          <div className="divider">OR</div>

          <h2>Create a Course</h2>

          <input
            type="text"
            placeholder="Enter Course Name"
            value={newCourse}
            onChange={(e) => setNewCourse(e.target.value)}
          />

          <button onClick={handleNext}>
            Next
          </button>

        </div>
      </div>
    </>
  );
};

export default CourseSelection;