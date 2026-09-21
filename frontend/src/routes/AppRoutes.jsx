import { Routes, Route } from "react-router-dom";

import Login from "../pages/Login/Login";
import Home from "../pages/Home/Home";
import CourseSelection from "../pages/CourseSelection/CourseSelection";
import Lesson from "../pages/Lesson/Lesson";
import TeacherDashboard from "../pages/TeacherDashboard/TeacherDashboard";
import NewLesson from "../pages/NewLesson/NewLesson";
import LessonAnalytics from "../pages/LessonAnalytics/LessonAnalytics";
import StudentLesson from "../pages/StudentLesson/StudentLesson";

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />

      <Route path="/login" element={<Login />} />

      <Route path="/courses" element={<CourseSelection />} />

      <Route path="/lessons" element={<Lesson />} />

      <Route path="/dashboard" element={<TeacherDashboard />} />

      <Route path="/new-lesson" element={<NewLesson />} />

      <Route path="/analytics" element={<LessonAnalytics />} />

      <Route path="/student-lesson" element={<StudentLesson />} />
    </Routes>
  );
};

export default AppRoutes;