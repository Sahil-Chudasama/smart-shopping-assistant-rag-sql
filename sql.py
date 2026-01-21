from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()
GROQ_MODEL = os.getenv('GROQ_MODEL')
db_path = Path(__file__).parent / "db.sqlite"
client_sql = Groq()



# --- SECURITY: SQL VALIDATION ---
def is_safe_sql(query):
    """
    Checks if the generated SQL is safe to execute.
    Only allows SELECT statements and blocks destructive keywords.
    """
    forbidden_keywords = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
        "TRUNCATE", "CREATE", "REPLACE", "GRANT"
    ]

    query_upper = query.upper()

    # Rule 1: Must start with SELECT
    if not query_upper.strip().startswith("SELECT"):
        return False, "Only search queries are allowed."

    # Rule 2: Check for forbidden destructive commands
    for word in forbidden_keywords:
        if f" {word} " in f" {query_upper} " or query_upper.startswith(word):
            return False, f"Security Block: Keyword '{word}' is not allowed."

    return True, "Safe"



# --- DATABASE CONNECTION ---
def run_query(query):
    try:
        # Validate before running
        is_safe, message = is_safe_sql(query)
        if not is_safe:
            print(f"Validation Error: {message}")
            return None

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        print(f"Database Error: {e}")
        return None


sql_prompt = """You are an expert in understanding the database schema and generating SQL queries for a natural language question asked
pertaining to the data you have. The schema is provided in the schema tags. 
<schema> 
table: product 

fields: 
product_link - string (hyperlink to product)	
title - string (name of the product)	
brand - string (brand of the product)	
price - integer (price of the product in Indian Rupees)	
discount - float (discount on the product. 10 percent discount is represented as 0.1, 20 percent as 0.2, and such.)	
avg_rating - float (average rating of the product. Range 0-5, 5 is the highest.)	
total_ratings - integer (total number of ratings for the product)

</schema>
Make sure whenever you try to search for the brand name, the name can be in any case. 
So, make sure to use %LIKE% to find the brand in condition. Never use "ILIKE". 
Create a single SQL query for the question provided. 
The query should have all the fields in SELECT clause (i.e. SELECT *)

Just the SQL query is needed, nothing more. Always provide the SQL in between the <SQL></SQL> tags."""


comprehension_prompt = """You are an expert in understanding the context of the question and replying based on the data pertaining to the question provided. You will be provided with Question: and Data:. The data will be in the form of an array or a dataframe or dict. Reply based on only the data provided as Data for answering the question asked as Question. Do not write anything like 'Based on the data' or any other technical words. Just a plain simple natural language response.
The Data would always be in context to the question asked. For example is the question is “What is the average rating?” and data is “4.3”, then answer should be “The average rating for the product is 4.3”. So make sure the response is curated with the question and data. Make sure to note the column names to have some context, if needed, for your response.
There can also be cases where you are given an entire dataframe in the Data: field. Always remember that the data field contains the answer of the question asked. All you need to do is to always reply in the following format when asked about a product: 
Produt title, price in indian rupees, discount, and rating, and then product link. Take care that all the products are listed in list format, one line after the other. Not as a paragraph.
For example:
1. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
2. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
3. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>

"""

# --- Generate SQL Query ----
def generate_sql_query(question):
    chat_completion = client_sql.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": sql_prompt,
            },
            {
                "role": "user",
                "content": question,
            }
        ],
        model=os.environ['GROQ_MODEL'],
        temperature=0.2,
        max_tokens=1024
    )

    return chat_completion.choices[0].message.content


# --- Data Comprehension ----
def data_comprehension(question, context):
    chat_completion = client_sql.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": comprehension_prompt,
            },
            {
                "role": "user",
                "content": f"QUESTION: {question}. DATA: {context}",
            }
        ],
        model=os.environ['GROQ_MODEL'],
        temperature=0.2,
        # max_tokens=1024
    )

    return chat_completion.choices[0].message.content




# --- SQL CHAIN ---
def sql_chain(question):
    # 1. Generate SQL from LLM (using your existing prompt)
    raw_llm_response = generate_sql_query(question)

    # 2. Extract query using your regex pattern
    pattern = "<SQL>(.*?)</SQL>"
    matches = re.findall(pattern, raw_llm_response, re.DOTALL)

    if not matches:
        return "I couldn't find any products matching that specific request. Can you try phrasing it differently?"

    query = matches[0].strip()
    print(f"Executing: {query}")  # Debugging

    # 3. Run and Validate
    df_results = run_query(query)

    if df_results is None or df_results.empty:
        return "I'm sorry, we don't have any products in stock that match those criteria right now."

    # 4. Turn data into a natural answer
    context = df_results.to_dict(orient='records')
    return data_comprehension(question, context)





if __name__ == "__main__":
    # question = "All shoes with rating higher than 4.5 and total number of reviews greater than 500"
    # sql_query = generate_sql_query(question)
    # print(sql_query)
    question = "Show top 3 shoes in descending order of rating"
    # question = "Show me 3 running shoes for woman"
    # question = "sfsdfsddsfsf"
    answer = sql_chain(question)
    print(answer)
