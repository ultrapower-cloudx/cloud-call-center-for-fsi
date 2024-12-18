import pandas as pd

excel_file = "FAQ-lender.xlsx"

df = pd.read_excel(excel_file)

for index, row in df.iterrows():
    question = row['question']
    answer = row['answer']
    #print(f"'question:{question}','answer:{answer}'")
    
    print(f"## Question: {question}")
    print(f"Answer: {answer}")
    print("\n")
    