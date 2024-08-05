import json
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from statistics import mean
import requests
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from lms_backend.student_dashboard_backend.performance_bot.config import STUDENT_ROADMAP_PROMPT
from xhtml2pdf import pisa
from io import BytesIO


with open('../db/grades_data.json') as f:
    grades_data = json.load(f)

with open('../db/syllabus_data.json') as f:
    syllabus_data = json.load(f)

with open('../db/attendance_data.json') as f:
    attendance_data = json.load(f)

class FalconLLM:
    def __init__(self, model="tiiuae/falcon-180b-chat"):
        self.api_key = "Enter AI71 API Here"
        self.model = model
        self.api_url = "https://api.ai71.ai/v1/" 
        self.url = f"{self.api_url}chat/completions"

    def generate(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
             {"role": "system", "content": "You are a helpful assistant."},
             {"role": "user", "content": f"{prompt}"}
         ]
     }
        response = requests.post(self.url, headers=headers, json=payload)
        # print(response.text)
        if response.status_code == 200:
            # print(response.json())
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Falcon API request failed with status code {response.status_code}: {response.text}")
        
class CustomLLMChain:
    def __init__(self, llm, prompt):
        self.llm = llm
        self.prompt = prompt

    def run(self, query, student_id, student_name):
        prompt_text = self.prompt.format(query=query, student_id=student_id, student_name=student_name)
        #print(prompt_text)
        return self.llm.generate(prompt_text)
    
class CustomAgentExecutor:
    def __init__(self, llm_chain, tools):
        self.llm_chain = llm_chain
        self.tools = {tool.name: tool.func for tool in tools}

    def execute(self, query, student_id, student_name):
        try:
            response = json.loads(self.llm_chain.run(query, student_id, student_name))
            print(response)

        except Exception as e:
            raise Exception(f"Faced error while calling correct tool: {str(e)}")
        
        tool_name = response.get("tool")
        reason = response.get("reason")

        if tool_name in self.tools:
            tool_func = self.tools[tool_name]
            tool_response = tool_func(query, student_id)
            return {"tool": tool_name, "reason": reason, "response": tool_response}
        else:
            return {"tool": None, "reason": "No appropriate tool found", "response": ""}
    

class PerformanceBot:
    def __init__(self):
        self.falcon_llm = FalconLLM()

    # Function to find student data
    def get_student_data(self, student_id):
        for student in grades_data['students']:
            if student['id'] == student_id.lower():
                return student
        return None
    
    def get_attendance_data(self, student_id):
        for student in attendance_data['students']:
            if student['id'].lower() == student_id.lower():
                return student['attendance']
        return None

    # Tool for personal question
    def generic_question_tool(self, query, student_id):

        summary_prompt = (
            f"User has asked the following query : {query}. Based on the following data : {grades_data} answer the query. The data contains the grades of all the class students in different subjects and the class average. "
        )
        response_text = self.falcon_llm.generate(summary_prompt)
        return response_text
    # Tool for overall question
    def overall_question_tool(self, query, student_id):
        student_data = self.get_student_data(student_id)
        #student_data = {id: 1, name : name, subjects : {english : {scores, average }, class_avergae = 80}}

        if not student_data:
            return "Record not found!"

        student_name = student_data.get("name")
        summary_prompt = (
            f"Generate a performance summary of student with name {student_name} wrt the overall class performance. Here is the data: {json.dumps(student_data)}. "
            "Include a table with subject names and averages, and a brief summary of how is the student performing in comparison to other students. End the summary with a recommendation for the student"
        )
        response_text = self.falcon_llm.generate(summary_prompt)
        return response_text

    # Tool for subject-wise question
    def subject_wise_question_tool(self, query, student_id):
        prompt_to_get_subject = (f"User has raised doubts about their performance in a particular subject in their studies. Identify which education subject is it: {json.dumps(query)}. The possible subjects could be one out of these - [math, science, english, computer]. Respond with a JSON object containing two keys: 'subject' and 'reason'. The 'subject' key should be the name of subject and the 'reason' key should explain why that subject was chosen.")
        subject = self.falcon_llm.generate(prompt_to_get_subject)
        subject = ((json.loads(subject)).get('subject')).lower()
        student_data = self.get_student_data(student_id)
        student_name = student_data['name']
        #student_data = {id: 1, name : name, subjects : {english : {scores, average }, class_avergae = 80}}
        
        if student_data and subject in student_data['subjects']:
            subject_scores = student_data['subjects'][subject]['scores']
            subject_average = student_data['subjects'][subject]['average']
            subject_summary = {
                "student_name": student_name,
                "subject": subject,
                "scores": subject_scores,
                "average": subject_average
            }
            summary_prompt = (
                f"""Generate a performance summary for the subject with the following data: {json.dumps(subject_summary)}. Include a table with the subject name, average, scores. Generate this result in HTML format. Use <table class="table table-striped table-bordered text-dark"> for tables. 
                Below the table add two headings in strong tag - 'Summary' and 'Recommendation'. Summary should be the summary of student's performance in that subject and recommendation should be a recommendation for the student to be better in the subject. Also add line break between new headings"""
            )
            response_text = self.falcon_llm.generate(summary_prompt)
            response_text = response_text.replace('\t', " ")
            response_text = response_text.replace('\n', " ")
            return response_text
        else:
            return f"Sorry, I couldn't find any data for {student_name} in {subject}."
        
    def student_roadmap_tool(self, query, student_id):
        student_data = self.get_student_data(student_id)
        student_name = student_data['name']
        
        if not student_data:
            return f"Sorry, I couldn't find any data for {student_id}."
        
        today = datetime.date.today()
        
        roadmap = {"covered": {}, "to_be_covered": {}, "recommendation": ""}

        for subject, details in syllabus_data['subjects'].items():
            roadmap["covered"][subject] = []
            roadmap["to_be_covered"][subject] = []

            for topic in details['topics']:
                expected_completion_date = datetime.datetime.strptime(topic['expected_completion_date'], '%Y-%m-%d').date()
                if expected_completion_date <= today:
                    roadmap["covered"][subject].append(topic['topic'])
                else:
                    roadmap["to_be_covered"][subject].append(topic['topic'])
        
        # print(roadmap)
        student_summary = {
            "name": student_name,
            "subjects": student_data['subjects'],
            "class_average": student_data['class_average'],
            "roadmap": roadmap,
            "important_dates": syllabus_data['important_dates']
        }

        summary_prompt = (f"{STUDENT_ROADMAP_PROMPT}. Here is the performance data of a student: {json.dumps(student_summary)}.")
        
        response_text = self.falcon_llm.generate(summary_prompt)
        response_text = response_text.replace('\t', " ")
        response_text = response_text.replace('\n', " ")
        self.save_text_to_pdf(response_text)
        return response_text
    
    def save_text_to_pdf(self, html_content):
        pdf_output = BytesIO()
        css_styles = """
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        </style>
        """
        head_tag_end_index = html_content.find('</head>')
        html_content_with_styles = html_content[:head_tag_end_index] + css_styles + html_content[head_tag_end_index:]

        pisa.CreatePDF(html_content_with_styles, dest=pdf_output, encoding='utf-8')
        with open("roadmap.pdf", "wb") as pdf_file:
            pdf_file.write(pdf_output.getvalue())

        return None
    
    def student_attendance_summary(self, query, student_id):
        attendance_data = self.get_attendance_data(student_id)
        
        if not attendance_data:
            return f"Sorry, I couldn't find any attendance data for {student_id}."
        
        summary_prompt = (
            f"Here is the attendance summary for the student: {json.dumps(attendance_data)}. "
            "Provide a brief summary and any recommendations if necessary based on student's attencance data."
            "Generate your answer in bullet points with recimmendation at the end"
        )
    
        response_text = self.falcon_llm.generate(summary_prompt)
        return response_text

    def handle_query(self, query, student_id, student_name, agent_executor):
        response = agent_executor.execute(query, student_id, student_name)
        return response

    def run_performance_bot(self, query, student_id):

        roadmap_tool = Tool(
            name="student_roadmap_tool",
            func=self.student_roadmap_tool,
            description="Creates a roadmap for a student based on their performance."
        )

        overall_tool = Tool(
            name="overall_question_tool",
            func=self.overall_question_tool,
            description="Fetches data for a specific student with respect to all students."
        )

        subject_wise_tool = Tool(
            name="subject_wise_question_tool",
            func=self.subject_wise_question_tool,
            description="Fetches data for student in a specific subject."
        )

        attendance_tool = Tool(
            name="attendance_tool",
            func=self.student_attendance_summary,
            description="Fetches data for a specific student's attendance."
        )

        generic_query_tool = Tool(
            name="generic_query_tool",
            func=self.generic_question_tool,
            description="Fetches data for generic queries"
        )


        tools = [roadmap_tool, overall_tool, subject_wise_tool, attendance_tool, generic_query_tool]
        try:
            student_data = self.get_student_data(student_id)
            student_name = student_data['name']

        except:
            return f"Sorry, I couldn't find any data for {student_id}."
        
        prompt_to_get_user = (f"User {student_name} has raised a query: {query}. You need to identify if the question is solely about {student_name} or if it involves mention of any other person other than {student_name}.\n"
                              "For eg. query: 'How is my performance' indicates question is about the user \n"
                              "However, query: 'How is Sakshi's performance' mentions 'Sakshi' istead of the user. \n" 
                              "Respond with a JSON object containing two keys: 'verdict' and 'reason'. \n"
                              "The 'verdict' key should be 'yes' if the question is completely about the user. It should be 'no' if it involves any other person. \n" 
                              "The 'reason' key should explain why that subject was chosen.")
        user = self.falcon_llm.generate(prompt_to_get_user)
        # print(user)
        user = ((json.loads(user)).get('verdict')).lower()
        

        if user == "yes":

            prompt_template = PromptTemplate(
                    input_variables=["query", "student_id", "student_name"],
                    template=(
                        "User has asked a query: {query}\n\n"
                        "Decide whether to call the student_roadmap_tool, attendance_tool, overall_question_tool, or subject_wise_question_tool. \n"
                        "If the query is about the performance of student, in a specific subject then select subject_wise_question_tool.\n"
                        "If the query is about the attendance of student, then select attendance_tool.\n"
                        "If the query is about learning roadmap of student, then select student_roadmap_tool.\n"
                        "If the query is about the overall performance of the student, then select overall_question_tool.\n"
                        "Respond with a JSON object containing two keys: 'tool' and 'reason'. The 'tool' key should be one of "
                        "['student_roadmap_tool', 'overall_question_tool', 'subject_wise_question_tool', 'attendance_tool] and the 'reason' key should explain why that tool was chosen."
                    )
                )
            
            chain = CustomLLMChain(llm=self.falcon_llm, prompt=prompt_template)
            agent_executor = CustomAgentExecutor(llm_chain=chain, tools=tools)
            response = self.handle_query(query, student_id, student_name, agent_executor)
            return response["response"]
        
        else:
            response = self.generic_question_tool(query = query, student_id = student_id)
            return response
    

    def prettify_summary(self, summary):
        summary_prompt = (
                f"Generate a summary text based on the following data: {summary}"
            )
        response_text = self.falcon_llm.generate(summary_prompt)
        return response_text

    
    def run_performance_bot_support(self, query, student_id):
        performance = self.run_performance_bot(query, student_id)
        summary = self.prettify_summary(performance)
        return summary

# ******* sample code *******    
# if __name__ == "__main__":
#     pb = PerformanceBot()
#     query = "How is my chlid performing in class?"
#     response = pb.run_performance_bot(query, "1")
#     print(response)