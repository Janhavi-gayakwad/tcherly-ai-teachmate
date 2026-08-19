import pandas as pd
import os


# --------------------------------------------------
# 1. Locate the Excel file
# --------------------------------------------------

file_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "demonstration-of-java-programs-V5iAKY-feedback-export (1).xlsx"
)


# --------------------------------------------------
# 2. Check whether the file exists
# --------------------------------------------------

if not os.path.exists(file_path):
    print("ERROR: Excel file not found.")
    print("Expected location:")
    print(file_path)
    exit()


# --------------------------------------------------
# 3. Load the Excel workbook
# --------------------------------------------------

try:
    excel_file = pd.ExcelFile(file_path)
except Exception as e:
    print("ERROR: Could not open the Excel file.")
    print(e)
    exit()


# --------------------------------------------------
# 4. Display all sheet names
# --------------------------------------------------

print("=" * 60)
print("AVAILABLE SHEETS")
print("=" * 60)

for sheet in excel_file.sheet_names:
    print("-", sheet)


# --------------------------------------------------
# 5. Check whether CLASS FEEDBACK exists
# --------------------------------------------------

if "CLASS FEEDBACK" not in excel_file.sheet_names:
    print("\nERROR: 'CLASS FEEDBACK' sheet was not found.")
    exit()


# --------------------------------------------------
# 6. Read CLASS FEEDBACK sheet
# --------------------------------------------------

try:
    class_feedback = pd.read_excel(
        file_path,
        sheet_name="CLASS FEEDBACK"
    )
except Exception as e:
    print("\nERROR: Could not read CLASS FEEDBACK sheet.")
    print(e)
    exit()


# --------------------------------------------------
# 7. Display complete CLASS FEEDBACK data
# --------------------------------------------------

print("\n" + "=" * 60)
print("CLASS FEEDBACK DATA")
print("=" * 60)

print(class_feedback.to_string(index=False))


# --------------------------------------------------
# 8. Display column names
# --------------------------------------------------

print("\n" + "=" * 60)
print("COLUMNS")
print("=" * 60)

for column in class_feedback.columns:
    print("-", column)


# --------------------------------------------------
# 9. Display dataset size
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATASET INFORMATION")
print("=" * 60)

print("Number of rows:", class_feedback.shape[0])
print("Number of columns:", class_feedback.shape[1])


# --------------------------------------------------
# 10. Check missing values
# --------------------------------------------------

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

print(class_feedback.isnull().sum())


# --------------------------------------------------
# 11. Check data types
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)

print(class_feedback.dtypes)


# --------------------------------------------------
# 12. Basic statistical information
# --------------------------------------------------

print("\n" + "=" * 60)
print("BASIC STATISTICS")
print("=" * 60)

print(class_feedback.describe())


# --------------------------------------------------
# 13. Check duplicate rows
# --------------------------------------------------

print("\n" + "=" * 60)
print("DUPLICATE ROWS")
print("=" * 60)

print("Number of duplicate rows:",
      class_feedback.duplicated().sum())


# --------------------------------------------------
# 14. Calculate total feedback
# --------------------------------------------------

feedback_columns = [
    "Difficult",
    "Easy",
    "Boring",
    "Engaging"
]

# Check that all required columns exist
missing_columns = [
    column
    for column in feedback_columns
    if column not in class_feedback.columns
]

if missing_columns:
    print("\nERROR: Missing feedback columns:")
    print(missing_columns)
    exit()


class_feedback["Total Feedback"] = (
    class_feedback["Difficult"]
    + class_feedback["Easy"]
    + class_feedback["Boring"]
    + class_feedback["Engaging"]
)


# --------------------------------------------------
# 15. Calculate Net Difficulty
# --------------------------------------------------

class_feedback["Net Difficulty"] = (
    class_feedback["Difficult"]
    - class_feedback["Easy"]
)


# --------------------------------------------------
# 16. Calculate Net Engagement
# --------------------------------------------------

class_feedback["Net Engagement"] = (
    class_feedback["Engaging"]
    - class_feedback["Boring"]
)


# --------------------------------------------------
# 17. Display processed data
# --------------------------------------------------

print("\n" + "=" * 60)
print("PROCESSED CLASS FEEDBACK")
print("=" * 60)

print(
    class_feedback[
        [
            "Timestamp (minutes)",
            "Difficult",
            "Easy",
            "Boring",
            "Engaging",
            "Total Feedback",
            "Net Difficulty",
            "Net Engagement"
        ]
    ].to_string(index=False)
)


# --------------------------------------------------
# 18. Overall feedback totals
# --------------------------------------------------

print("\n" + "=" * 60)
print("OVERALL FEEDBACK TOTALS")
print("=" * 60)

for column in feedback_columns:
    print(
        f"{column}: "
        f"{class_feedback[column].sum()}"
    )


# --------------------------------------------------
# 19. Overall net values
# --------------------------------------------------

overall_net_difficulty = (
    class_feedback["Difficult"].sum()
    - class_feedback["Easy"].sum()
)

overall_net_engagement = (
    class_feedback["Engaging"].sum()
    - class_feedback["Boring"].sum()
)

print("\nOverall Net Difficulty:",
      overall_net_difficulty)

print("Overall Net Engagement:",
      overall_net_engagement)


# --------------------------------------------------
# 20. Find important lecture points
# --------------------------------------------------

most_difficult = class_feedback.loc[
    class_feedback["Difficult"].idxmax()
]

most_easy = class_feedback.loc[
    class_feedback["Easy"].idxmax()
]

most_boring = class_feedback.loc[
    class_feedback["Boring"].idxmax()
]

most_engaging = class_feedback.loc[
    class_feedback["Engaging"].idxmax()
]


print("\n" + "=" * 60)
print("KEY LECTURE INSIGHTS")
print("=" * 60)

print(
    "Most difficult minute:",
    most_difficult["Timestamp (minutes)"]
)

print(
    "Most easy minute:",
    most_easy["Timestamp (minutes)"]
)

print(
    "Most boring minute:",
    most_boring["Timestamp (minutes)"]
)

print(
    "Most engaging minute:",
    most_engaging["Timestamp (minutes)"]
)


# --------------------------------------------------
# 21. Finish
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATA LOADING AND INITIAL ANALYSIS COMPLETED")
print("=" * 60)