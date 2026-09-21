import Navbar from "../../components/Navbar/Navbar";
import "./LessonAnalytics.css";

const LessonAnalytics = () => {
  return (
    <>
      <Navbar />

      <div className="analytics-page">

        {/* =====================================
            TOP TITLE
        ====================================== */}

        <div className="analytics-title">
          <span>Tcherly Teacher Dashboard</span>

          <span className="beta-badge">Beta</span>

          <span className="lesson-title">
            Graph Colouring Problem
          </span>

          <button className="tour-btn">
            Take tour
          </button>
        </div>


        {/* =====================================
            MAIN DASHBOARD
        ====================================== */}

        <div className="analytics-dashboard">

          {/* LEFT VIDEO + GRAPH */}
          <div className="left-panel">

            {/* VIDEO */}
            <div className="video-box">

              <div className="video-header">
                Graph Colouring
              </div>

              <div className="video-content">

                <div className="play-circle">
                  ▶
                </div>

                <div className="video-text">
                  Graph colouring problem
                </div>

              </div>

            </div>


            {/* TIMELINE */}
            <div className="timeline">

              <span>0</span>

              <div className="timeline-line">
                <div className="timeline-progress"></div>
              </div>

              <span>5</span>

            </div>


            {/* PARTICIPATION GRAPH */}
            <div className="chart-card">

              <h3>Student Participation</h3>

              <div className="fake-chart">

                <div className="y-label">Number of students</div>

                <div className="chart-area">

                  <div className="horizontal-line line1"></div>
                  <div className="horizontal-line line2"></div>
                  <div className="horizontal-line line3"></div>
                  <div className="horizontal-line line4"></div>

                  <div className="green-graph"></div>

                  <div className="red-graph"></div>

                </div>

                <div className="x-label">
                  Time in minutes
                </div>

              </div>


              {/* LEGEND */}
              <div className="graph-legend">

                <span>
                  <i className="legend-box difficult"></i>
                  Net Difficulty
                </span>

                <span>
                  <i className="legend-box engaging"></i>
                  Net Engagement
                </span>

              </div>

            </div>

          </div>


          {/* =====================================
              CENTER PANEL
          ====================================== */}

          <div className="center-panel">

            {/* SAVE ANALYSIS */}

            <div className="save-analysis">

              <h3>Save Your Analysis</h3>

              <div className="selected-range">

                <span>Selected range:</span>

                <b>0</b>

                <span>min</span>

                <strong>−</strong>

                <b>5</b>

                <span>min</span>

                <input
                  type="text"
                  defaultValue="Graph colouring problem 1"
                />

              </div>


              <div className="feedback-selection">

                <span>Select feedback:</span>

                <label>
                  <input type="checkbox" />
                  Difficult
                </label>

                <label>
                  <input type="checkbox" />
                  Easy
                </label>

                <label>
                  <input type="checkbox" />
                  Boring
                </label>

                <label>
                  <input type="checkbox" />
                  Engaging
                </label>

                <button>
                  Add Bookmark
                </button>

              </div>

            </div>


            {/* DEBE INTERACTIONS */}

            <div className="debe-card">

              <h3>DEBE Interactions</h3>

              <div className="bubbles">

                <div className="bubble difficult-bubble">
                  14
                </div>

                <div className="small-bubble">
                  2
                </div>

                <div className="bubble engaging-bubble">
                  26
                </div>

                <div className="small-bubble second">
                  2
                </div>

              </div>

              <div className="bubble-labels">
                <span>Difficult − Easy</span>
                <span>Boring − Engaging</span>
              </div>

            </div>


            {/* DEBE DISTRIBUTION */}

            <div className="distribution-card">

              <h3>DEBE Distribution</h3>

              <div className="distribution">

                <div className="distribution-top">
                  Difficult
                  <strong>8%</strong>
                </div>

                <div className="distribution-center">
                  <div className="axis-horizontal"></div>
                  <div className="axis-vertical"></div>

                  <div className="center-point"></div>
                </div>

                <div className="distribution-bottom">
                  <strong>26%</strong>
                  Easy
                </div>

              </div>

              <div className="distribution-side left">
                Boring
                <strong>4%</strong>
              </div>

              <div className="distribution-side right">
                Engaging
                <strong>49%</strong>
              </div>

            </div>


            {/* FEEDBACK CHECKBOXES */}

            <div className="feedback-types">

              <label>
                <input type="checkbox" />
                Difficult
              </label>

              <label>
                <input type="checkbox" />
                Easy
              </label>

              <label>
                <input type="checkbox" />
                Boring
              </label>

              <label>
                <input type="checkbox" />
                Engaging
              </label>

            </div>

          </div>


          {/* =====================================
              RIGHT PANEL
          ====================================== */}

          <div className="right-panel">

            {/* STUDENT PARTICIPATION */}

            <div className="participation-card">

              <h3>Student Participation</h3>

              <div className="response-header">

                <span>
                  Responses between
                </span>

                <b>0</b>

                <span>−</span>

                <b>5</b>

                <span>min</span>

              </div>


              <div className="response-bars">

                <div>

                  <span>34 / 53</span>

                  <div className="bar">
                    <div className="bar-fill first"></div>
                  </div>

                </div>


                <div>

                  <span>53 / 62</span>

                  <div className="bar">
                    <div className="bar-fill second-fill"></div>
                  </div>

                </div>

              </div>

            </div>


            {/* DEBE REASONS */}

            <div className="reasons-card">

              <h3>DEBE Reasons</h3>

              <div className="reason-columns">

                <div className="reason difficult">

                  <h4>Difficult</h4>

                  <div>None</div>

                  <div>I'm missing basics</div>

                </div>


                <div className="reason easy">

                  <h4>Easy</h4>

                  <div>Good explanation</div>

                  <div>None</div>

                  <div>Neat presentation</div>

                </div>


                <div className="reason boring">

                  <h4>Boring</h4>

                  <div>
                    Too slow or repetitive teaching
                  </div>

                </div>


                <div className="reason engaging">

                  <h4>Engaging</h4>

                  <div>Good explanation</div>

                  <div>None</div>

                  <div>Interesting examples...</div>

                </div>

              </div>

            </div>


            {/* OTHER REASONS */}

            <div className="other-reasons">

              <h3>Other Reasons</h3>

              <div className="other-reason">
                Explained very well and very helpful..!
              </div>

            </div>

          </div>

        </div>


        {/* =====================================
            BOTTOM TABLES
        ====================================== */}

        <div className="bottom-section">

          {/* QUESTIONS */}

          <div className="bottom-table">

            <div className="table-header">

              <span>No.</span>

              <span>
                Question (or finding) based on analysis
              </span>

              <span>What can be done?</span>

              <button>
                Add Question
              </button>

            </div>


            <div className="table-row">

              <span>1</span>

              <span>XYZ</span>

              <span>ABC</span>

              <span>
                ✎ &nbsp; 🗑
              </span>

            </div>

          </div>


          {/* ACTIONS */}

          <div className="bottom-table">

            <div className="table-header">

              <span>No.</span>

              <span>
                What action have I taken?
              </span>

              <span>
                Any future action items?
              </span>

              <button>
                Add Action
              </button>

            </div>

          </div>

        </div>

      </div>
    </>
  );
};

export default LessonAnalytics;