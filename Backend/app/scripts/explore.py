import pandas as pd

PATH = "data/tcherly_data.xlsx"

xl = pd.ExcelFile(PATH)

print("Sheet names:", xl.sheet_names)
print("Total sheets:", len(xl.sheet_names))

student_sheets = [
    s for s in xl.sheet_names
    if s not in ("CLASS FEEDBACK", "NO FEEDBACK STUDENTS")
]

sample_sheet = student_sheets[0]

df_student = xl.parse(sample_sheet)

print(f"\n--- {sample_sheet} ---")
print(df_student)

df_class = xl.parse("CLASS FEEDBACK")

print("\n--- CLASS FEEDBACK ---")
print(df_class.head(10))