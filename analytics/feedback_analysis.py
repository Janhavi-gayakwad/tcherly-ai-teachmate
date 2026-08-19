import pandas as pd


# --------------------------------------------------
# Overall feedback totals
# --------------------------------------------------

def get_overall_feedback(df):
    """
    Return total feedback counts for the whole lecture.
    """

    return {
        "Difficult": int(df["Difficult"].sum()),
        "Easy": int(df["Easy"].sum()),
        "Boring": int(df["Boring"].sum()),
        "Engaging": int(df["Engaging"].sum())
    }


# --------------------------------------------------
# Net difficulty
# --------------------------------------------------

def get_net_difficulty(df):
    """
    Net Difficulty = Difficult - Easy
    """

    return int(
        df["Difficult"].sum()
        - df["Easy"].sum()
    )


# --------------------------------------------------
# Net engagement
# --------------------------------------------------

def get_net_engagement(df):
    """
    Net Engagement = Engaging - Boring
    """

    return int(
        df["Engaging"].sum()
        - df["Boring"].sum()
    )


# --------------------------------------------------
# Most difficult minute
# --------------------------------------------------

def get_most_difficult_minute(df):

    row = df.loc[
        df["Difficult"].idxmax()
    ]

    return {
        "minute": int(row["Timestamp (minutes)"]),
        "count": int(row["Difficult"])
    }


# --------------------------------------------------
# Most easy minute
# --------------------------------------------------

def get_most_easy_minute(df):

    row = df.loc[
        df["Easy"].idxmax()
    ]

    return {
        "minute": int(row["Timestamp (minutes)"]),
        "count": int(row["Easy"])
    }


# --------------------------------------------------
# Most boring minute
# --------------------------------------------------

def get_most_boring_minute(df):

    row = df.loc[
        df["Boring"].idxmax()
    ]

    return {
        "minute": int(row["Timestamp (minutes)"]),
        "count": int(row["Boring"])
    }


# --------------------------------------------------
# Most engaging minute
# --------------------------------------------------

def get_most_engaging_minute(df):

    row = df.loc[
        df["Engaging"].idxmax()
    ]

    return {
        "minute": int(row["Timestamp (minutes)"]),
        "count": int(row["Engaging"])
    }


# --------------------------------------------------
# Complete analytics summary
# --------------------------------------------------

def generate_feedback_summary(df):

    return {
        "overall_feedback": get_overall_feedback(df),

        "net_difficulty": get_net_difficulty(df),

        "net_engagement": get_net_engagement(df),

        "most_difficult": get_most_difficult_minute(df),

        "most_easy": get_most_easy_minute(df),

        "most_boring": get_most_boring_minute(df),

        "most_engaging": get_most_engaging_minute(df)
    }


# --------------------------------------------------
# Test the analysis module
# --------------------------------------------------

if __name__ == "__main__":

    import os

    from data_cleaning import clean_feedback_data

    file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "demonstration-of-java-programs-V5iAKY-feedback-export (1).xlsx"
    )

    # Load Excel data
    df = pd.read_excel(
        file_path,
        sheet_name="CLASS FEEDBACK"
    )

    # Clean data
    cleaned_df = clean_feedback_data(df)

    # Generate analytics
    summary = generate_feedback_summary(cleaned_df)

    # Display results
    print("=" * 60)
    print("TCHERLY FEEDBACK ANALYSIS")
    print("=" * 60)

    print("\nOverall Feedback:")
    for key, value in summary["overall_feedback"].items():
        print(f"{key}: {value}")

    print("\nNet Difficulty:",
          summary["net_difficulty"])

    print("Net Engagement:",
          summary["net_engagement"])

    print("\nMost Difficult:")
    print(
        f"Minute {summary['most_difficult']['minute']} "
        f"({summary['most_difficult']['count']} students)"
    )

    print("\nMost Easy:")
    print(
        f"Minute {summary['most_easy']['minute']} "
        f"({summary['most_easy']['count']} students)"
    )

    print("\nMost Boring:")
    print(
        f"Minute {summary['most_boring']['minute']} "
        f"({summary['most_boring']['count']} students)"
    )

    print("\nMost Engaging:")
    print(
        f"Minute {summary['most_engaging']['minute']} "
        f"({summary['most_engaging']['count']} students)"
    )