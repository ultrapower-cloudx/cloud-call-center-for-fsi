import pandas as pd

md_file = './FAQ-broker-spanish.md.txt'
question_word = "Pregunta:"
answer_word = "Respuesta:"


# md_file = './FAQ-broker-indonesia.md.txt'
# question_word = "Pertanyaan:"
# answer_word = "Jawaban:"


# md_file = './FAQ-lender.spanish.md.txt'
# question_word = "Pregunta:"
# answer_word = "Respuesta:"

# md_file = './FAQ-lender.indonesia.md.txt'
# question_word = "Pertanyaan:"
# answer_word = "Jawaban:"


question = None
answer_lines = []

header = "question,answer"
#print(header)

df_rows = []

with open(md_file, 'r') as input_file:
    for line in input_file:
       if line.startswith("##"):
           
           if len(answer_lines) > 0:
               #print(f"\"{question}\",\"{'\n'.join(answer_lines)}\"")
               df_rows.append([question, '\n'.join(answer_lines)])
           
           question = line.replace("##", "").replace(question_word, "").strip()
           answer_lines = []
       else:
           line = line.replace(answer_word, "").strip() if line.startswith(answer_word) else line.strip()
           answer_lines.append(line.strip()) if len(line.strip()) > 0 else None


if len(answer_lines) > 0:
    #print(f"\"{question}\",\"{'\n'.join(answer_lines)}\"")
    df_rows.append([question, '\n'.join(answer_lines)])
    


df = pd.DataFrame(df_rows, columns=['question', 'answer'])

df.to_excel(f"{md_file}.xlsx", index=False)

print(f"Excel file created: {md_file}.xlsx")

