import { Link } from "react-router-dom";
import "./Navbar.css";

const Navbar = () => {
  return (
    <nav className="navbar">

      <div className="logo">
        <span className="logo-red">Tcherly</span>
        <span className="logo-black"> Feedback</span>

        <span className="beta">Beta</span>
      </div>

      <div className="nav-links">

        <Link to="/">Home</Link>

        <Link to="/dashboard">Dashboard</Link>

        <Link to="#">Research</Link>

        <Link to="#">Guidelines</Link>

        <div className="profile">
          👤
        </div>

      </div>

    </nav>
  );
};

export default Navbar;