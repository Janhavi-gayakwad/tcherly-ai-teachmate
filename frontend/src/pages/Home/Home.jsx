import Navbar from "../../components/Navbar/Navbar";
import "./Home.css";
import { useNavigate } from "react-router-dom";
import { FaArrowRight } from "react-icons/fa";
import heroImage from "../../assets/images/hero.png";

const Home = () => {
  const navigate = useNavigate();   

  return (
    <>
      <Navbar />

      <section className="hero">
        <div className="hero-left">
          <h1>
            Feedback to help teachers improve teaching practices
          </h1>

          <p>
            Collection and analysis of student feedback made easy
          </p>

          <button
            className="hero-btn"
            onClick={() => navigate("/login")}
          >
            Get Started
            <FaArrowRight />
          </button>
        </div>

        <div className="hero-right">
          <img src={heroImage} alt="Teacher" />
        </div>
      </section>
    </>
  );
};

export default Home;