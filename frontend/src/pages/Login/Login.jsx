import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./Login.css";

const Login = () => {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
  e.preventDefault();

  // Later: Authenticate with backend

  navigate("/courses");
};
  return (
    <>
      <Navbar />

      <div className="login-container">

        <form className="login-card" onSubmit={handleLogin}>

          <h2>Login</h2>

          <label>Email</label>

          <input
            type="email"
            placeholder="Enter Email"
            value={email}
            onChange={(e)=>setEmail(e.target.value)}
          />

          <label>Password</label>

          <div className="password-box">

            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e)=>setPassword(e.target.value)}
            />

            <button
              type="button"
              onClick={()=>setShowPassword(!showPassword)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>

          </div>

          <div className="remember">

            <input type="checkbox"/>

            <span>Remember Me</span>

          </div>

          <button className="login-btn">
            Login
          </button>

          <Link className="forgot">
            Forgot Password?
          </Link>

          <p>
            Don't have an account?
            <Link to="#">
              Register
            </Link>
          </p>

        </form>

      </div>

    </>
  );
};

export default Login;