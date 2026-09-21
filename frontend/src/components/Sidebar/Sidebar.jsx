import "./Sidebar.css";
import { NavLink } from "react-router-dom";

import {
  MdDashboard,
  MdSchool,
  MdPlayLesson,
  MdAnalytics,
} from "react-icons/md";

const Sidebar = () => {
  return (
    <div className="sidebar">

      <div className="logo">
        <h2>Tcherly</h2>
        <span>Teacher Panel</span>
      </div>

      <nav>

        <NavLink to="/dashboard">
          <MdDashboard />
          Dashboard
        </NavLink>

        <NavLink to="/courses">
          <MdSchool />
          Courses
        </NavLink>

        <NavLink to="/student-lesson">
          <MdPlayLesson />
          Student Lesson
        </NavLink>

        <NavLink to="/analytics">
          <MdAnalytics />
          Analytics
        </NavLink>

      </nav>

    </div>
  );
};

export default Sidebar;