import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./NewLesson.css";

const NewLesson = () => {
  const navigate = useNavigate();

  const [lessonName, setLessonName] = useState("");
  const [description, setDescription] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [duration, setDuration] = useState("");

  const handleCreateLesson = (e) => {
    e.preventDefault();

    // Validate lesson name
    if (!lessonName.trim()) {
      alert("Please enter lesson name.");
      return;
    }

    // Get existing lessons
    const lessons =
      JSON.parse(localStorage.getItem("teacherLessons")) || [];

    // Automatically calculate lesson number
    const nextLessonNo = lessons.length + 1;

    // Create new lesson
    const newLesson = {
      id: Date.now(),
      lessonNo: nextLessonNo,
      name: lessonName,
      description: description,
      videoUrl: videoUrl,
      duration: duration,
    };

    // Add new lesson to existing lessons
    lessons.push(newLesson);

    // Save all lessons
    localStorage.setItem(
      "teacherLessons",
      JSON.stringify(lessons)
    );

    alert("Lesson created successfully!");

    // Go back to dashboard
    navigate("/dashboard");
  };

  return (
    <>
      <Navbar />

      <div className="new-lesson-page">
        <div className="new-lesson-card">

          <div className="new-lesson-header">
            <h2>Create a New Lesson</h2>

            <p>
              Add the details of your lesson below.
            </p>
          </div>

          <form
            className="lesson-form"
            onSubmit={handleCreateLesson}
          >

            {/* Lesson Name */}
            <div className="form-group">
              <label>Lesson Name</label>

              <input
                type="text"
                value={lessonName}
                onChange={(e) =>
                  setLessonName(e.target.value)
                }
                placeholder="Enter lesson name"
              />
            </div>

            {/* Description */}
            <div className="form-group">
              <label>Lesson Description</label>

              <textarea
                rows="5"
                value={description}
                onChange={(e) =>
                  setDescription(e.target.value)
                }
                placeholder="Enter lesson description"
              />
            </div>

            {/* Video URL */}
            <div className="form-group">
              <label>Lesson Video URL</label>

              <input
                type="text"
                value={videoUrl}
                onChange={(e) =>
                  setVideoUrl(e.target.value)
                }
                placeholder="Enter video URL"
              />
            </div>

            {/* Duration */}
            <div className="form-group">
              <label>Duration</label>

              <input
                type="text"
                value={duration}
                onChange={(e) =>
                  setDuration(e.target.value)
                }
                placeholder="Example: 45 minutes"
              />
            </div>

            {/* Buttons */}
            <div className="form-buttons">

              <button
                type="button"
                className="cancel-btn"
                onClick={() =>
                  navigate("/dashboard")
                }
              >
                Cancel
              </button>

              <button
                type="submit"
                className="create-btn"
              >
                Create Lesson
              </button>

            </div>

          </form>

        </div>
      </div>
    </>
  );
};

export default NewLesson;