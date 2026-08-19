import pandas as pd
import numpy as np


FEEDBACK_COLS = [
    "Difficult",
    "Easy",
    "Boring",
    "Engaging"
]


EXCLUDED_SHEETS = {
    "CLASS FEEDBACK",
    "NO FEEDBACK STUDENTS"
}


def load_long_format(path: str) -> pd.DataFrame:
    """Load all student sheets into one long-format DataFrame."""

    xl = pd.ExcelFile(path)

    student_sheets = [
        s for s in xl.sheet_names
        if s not in EXCLUDED_SHEETS
    ]

    all_rows = []

    for sheet in student_sheets:

        df = xl.parse(sheet)

        # Fill student information downward
        df["Student Unique ID"] = (
            df["Student Unique ID"].ffill()
        )

        df["Student Name"] = (
            df["Student Name"].ffill()
        )

        # Convert feedback columns into rows
        melted = df.melt(
            id_vars=[
                "Timestamp (seconds)",
                "Student Unique ID",
                "Student Name"
            ],
            value_vars=FEEDBACK_COLS,
            var_name="feedback_type",
            value_name="flag"
        )

        # Keep only actual feedback clicks
        melted = melted[melted["flag"] == 1]

        # Keep required columns
        all_rows.append(
            melted[
                [
                    "Timestamp (seconds)",
                    "Student Unique ID",
                    "Student Name",
                    "feedback_type"
                ]
            ]
        )

    # Combine all students
    long_df = pd.concat(
        all_rows,
        ignore_index=True
    )

    # Rename columns
    long_df = long_df.rename(
        columns={
            "Timestamp (seconds)": "timestamp_sec",
            "Student Unique ID": "student_id",
            "Student Name": "student_name"
        }
    )

    # Remove exact duplicate feedback records
    long_df = long_df.drop_duplicates(
        subset=[
            "student_id",
            "timestamp_sec",
            "feedback_type"
        ]
    )

    return long_df


def save_long_format(
    long_df: pd.DataFrame,
    output_path: str
):
    """Save combined student feedback as an Excel file."""

    # Sort the data for easier reading
    output_df = long_df.sort_values(
        by=[
            "timestamp_sec",
            "student_name"
        ]
    ).reset_index(drop=True)

    # Save as Excel
    output_df.to_excel(
        output_path,
        index=False
    )

    print(
        f"\nLong-format data saved to: {output_path}"
    )


def aggregate_per_minute(
    long_df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate feedback into one-minute intervals."""

    df = long_df.copy()

    # Convert seconds to 1-based minutes.
    # Tcherly CLASS FEEDBACK matches ceiling(seconds / 60).
    df["minute"] = np.ceil(
        df["timestamp_sec"] / 60
    ).astype(int)

    # Ignore minute 0 if timestamp is exactly 0
    df = df[df["minute"] >= 1]

    # Count one feedback per student,
    # per minute, per feedback type.
    df = df.drop_duplicates(
        subset=[
            "student_id",
            "minute",
            "feedback_type"
        ]
    )

    pivot = (
        df.groupby(
            ["minute", "feedback_type"]
        )
        .size()
        .unstack(fill_value=0)
        .reindex(
            columns=FEEDBACK_COLS,
            fill_value=0
        )
        .reset_index()
    )

    # Net difficulty
    pivot["net_difficulty"] = (
        pivot["Difficult"]
        - pivot["Easy"]
    )

    # Net engagement
    pivot["net_engagement"] = (
        pivot["Engaging"]
        - pivot["Boring"]
    )

    return pivot


def validate_against_class_feedback(
    per_minute: pd.DataFrame,
    path: str
):

    xl = pd.ExcelFile(path)

    class_feedback = xl.parse(
        "CLASS FEEDBACK"
    )

    merged = per_minute.merge(
        class_feedback,
        left_on="minute",
        right_on="Timestamp (minutes)",
        suffixes=("_mine", "_official")
    )

    # Compare all feedback categories
    merged["diff_match"] = (
        merged["Difficult_mine"]
        == merged["Difficult_official"]
    )

    merged["easy_match"] = (
        merged["Easy_mine"]
        == merged["Easy_official"]
    )

    merged["boring_match"] = (
        merged["Boring_mine"]
        == merged["Boring_official"]
    )

    merged["engaging_match"] = (
        merged["Engaging_mine"]
        == merged["Engaging_official"]
    )

    print("\n--- VALIDATION ---")

    print(
        merged[
            [
                "minute",
                "Difficult_mine",
                "Difficult_official",
                "Easy_mine",
                "Easy_official",
                "Boring_mine",
                "Boring_official",
                "Engaging_mine",
                "Engaging_official"
            ]
        ].to_string(index=False)
    )

    print(
        "\nAll minutes match on Difficult:",
        merged["diff_match"].all()
    )

    print(
        "All minutes match on Easy:",
        merged["easy_match"].all()
    )

    print(
        "All minutes match on Boring:",
        merged["boring_match"].all()
    )

    print(
        "All minutes match on Engaging:",
        merged["engaging_match"].all()
    )

    return merged


if __name__ == "__main__":

    PATH = "data/tcherly_data.xlsx"

    # --------------------------------------------------
    # DAY 3
    # --------------------------------------------------

    print("\n========== DAY 3 ==========")

    long_df = load_long_format(PATH)

    print("\nFirst 15 rows:")
    print(long_df.head(15))

    print(
        "\nTotal feedback events:",
        len(long_df)
    )

    print("\nCounts by feedback type:")
    print(
        long_df["feedback_type"].value_counts()
    )

    # --------------------------------------------------
    # SAVE LONG FORMAT DATA
    # --------------------------------------------------

    save_long_format(
        long_df,
        "data/tcherly_long_format.xlsx"
    )

    # --------------------------------------------------
    # DAY 4
    # --------------------------------------------------

    print("\n========== DAY 4 ==========")

    per_minute = aggregate_per_minute(
        long_df
    )

    print("\nPer-minute data:")

    print(
        per_minute.head(15).to_string(index=False)
    )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    validate_against_class_feedback(
        per_minute,
        PATH
    )