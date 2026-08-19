import pandas as pd


def clean_feedback_data(df):
    """
    Clean and validate Tcherly CLASS FEEDBACK data.
    """

    # Make a copy so the original DataFrame is not modified
    df = df.copy()

    # -----------------------------------------
    # 1. Clean column names
    # -----------------------------------------
    df.columns = df.columns.str.strip()

    # -----------------------------------------
    # 2. Required columns
    # -----------------------------------------
    required_columns = [
        "Timestamp (minutes)",
        "Difficult",
        "Easy",
        "Boring",
        "Engaging"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # -----------------------------------------
    # 3. Convert columns to numeric
    # -----------------------------------------
    for column in required_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # -----------------------------------------
    # 4. Remove rows with missing values
    # -----------------------------------------
    df = df.dropna(
        subset=required_columns
    )

    # -----------------------------------------
    # 5. Remove duplicate rows
    # -----------------------------------------
    df = df.drop_duplicates()

    # -----------------------------------------
    # 6. Remove invalid timestamps
    # -----------------------------------------
    df = df[
        df["Timestamp (minutes)"] >= 0
    ]

    # -----------------------------------------
    # 7. Remove negative feedback values
    # -----------------------------------------
    feedback_columns = [
        "Difficult",
        "Easy",
        "Boring",
        "Engaging"
    ]

    for column in feedback_columns:
        df = df[
            df[column] >= 0
        ]

    # -----------------------------------------
    # 8. Convert values to integers
    # -----------------------------------------
    df[required_columns] = df[
        required_columns
    ].astype(int)

    # -----------------------------------------
    # 9. Sort by timestamp
    # -----------------------------------------
    df = df.sort_values(
        by="Timestamp (minutes)"
    )

    # Reset index
    df = df.reset_index(drop=True)

    return df
if __name__ == "__main__":

    import os

    file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "demonstration-of-java-programs-V5iAKY-feedback-export (1).xlsx"
    )

    df = pd.read_excel(
        file_path,
        sheet_name="CLASS FEEDBACK"
    )

    print("=" * 60)
    print("BEFORE CLEANING")
    print("=" * 60)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Missing values:")
    print(df.isnull().sum().sum())
    print("Duplicates:", df.duplicated().sum())

    cleaned_df = clean_feedback_data(df)

    print("\n" + "=" * 60)
    print("AFTER CLEANING")
    print("=" * 60)

    print("Rows:", len(cleaned_df))
    print("Columns:", len(cleaned_df.columns))
    print("Missing values:")
    print(cleaned_df.isnull().sum().sum())
    print("Duplicates:", cleaned_df.duplicated().sum())

    print("\nCleaned data:")
    print(cleaned_df.to_string(index=False))