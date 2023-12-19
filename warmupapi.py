from fastapi import FastAPI
import openai
import time
import json
from pydantic import BaseModel


openai.api_type = "azure"
openai.api_base = "https://sproutsai-gpt.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = '564db3f7e88b433a94110af1a5e52d4b'


app = FastAPI()

class Resume_parser(BaseModel):
    Job_parser : dict
    
class candidate_response(BaseModel):
    Answer : list

def warmup_question_genreation(criteria,skills):
   
   
    response_format = '''{
    "criteria_tag": f"{criteria}",
    "skills_tag" : f"{skills}"
    "type_of_question": "warmup question",
                        }'''
    n = 0
    while n < 3:
        try:
            response = openai.ChatCompletion.create(
                    engine = 'gpt4-sproutsai',
                    messages=[
                        {"role": "system", "content": f"""Your role is skill finding by the way of creating warmup questions. 
                            I have a list of skill under some criteria and I have many questions on each skill. You need to find which skill candidate know 

                    Generate a simple warmup questions that cover the following aspects:
                            
                    1. Don't create a question like Can you briefly describe your experience?
                    2. The generated question should be in a general format for the {criteria} and {skills}.
                    3. The motive of asking the question is to assess the candidate's overall suitability for the position based on the {criteria}.
                    4. Generate one question.

                    
                    """},
                        
                        {"role": "user", "content": f"Give the response in JSON format, which is strictly a list of {response_format}. Use \" instead of ' for the response keys."},

                    ],

                    temperature=0.2,
                    max_tokens=3500,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0

                )
            
            print(response['choices'][0]['message']['content'])
            
            return json.loads(response['choices'][0]['message']['content'])
        except Exception as e:
            n+=1
            time.sleep(60)
    return "Error with openai api"

def warmup_validation(criteria, skills, answer):
    output = {}
    response_format =  [
        {
            "skills": 'skill1',
            "reason": "Give reason why you picked the skill"
        },
        {
            "skills": 'skill2',
            "reason": "Give reason why you picked the skill"
        } ]
    
    n = 0
    while n < 3:
        try:
            response = openai.ChatCompletion.create(
                engine='gpt4-sproutsai',
                messages=[
                    {
                        "role": "system",
                        "content": f"""Your role is to find the skill from the answer: {answer}.
                                If the answer is incomplete or irrelevant, then return []
                                If the candidate answers like "I know this skill" or "I have experience in these skills" and the skill is available in {skills}, then only consider the skill.
                                If the answer is meaningless or insufficient, please respond in a reason section like "he doesn't have knowledge of that skill".
                                There is no need to add skills if that is not on the list of skills {skills}.
                                If the answer is "I don't know these skills" like that, then don't consider those skills in{response_format}"""
                    },
                    {"role": "user", "content": f"Give the response in JSON format, which is strictly a list of {response_format}. Use \" instead of ' for the response keys."},
                ],
                temperature=0.2,
                max_tokens=1000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0)
            time.sleep(5)
            
            response_content = response['choices'][0]['message']['content']
            response_content = json.loads(response_content)
            output["criteria"] = criteria
            output["skills"] = response_content
            print(output)
            return output
        except Exception as e:
            n += 1
            time.sleep(25)
    return "Error with openai api"

@app.post("/warmup_question_generation")
def warmup_question_generation(payload : Resume_parser):
    jobparser = payload.Job_parser
    criteria_skill_dictionary = {}
    for i in jobparser['question_selection_data']['criterias']:
        if i['criteria'] in criteria_skill_dictionary:
            criteria_skill_dictionary[i['criteria']].append(i['skill'])
        else:
            criteria_skill_dictionary[i['criteria']] =  [i['skill']]

    print(criteria_skill_dictionary)
    op = []
    for i in criteria_skill_dictionary:
        x = warmup_question_genreation(i,criteria_skill_dictionary[i])
        op.append(x)
    return op

@app.post("/warmup_answer_validation")
def warmup_question_validation(payload : candidate_response):
    print('start')
    candidate_response = payload.Answer
    result = []
    print(candidate_response)
    for i in candidate_response:
        print(i)
        validation_gpt = warmup_validation(i['criteria'],i['skills'],i['answer'])
        result.append(validation_gpt)
        
    return result