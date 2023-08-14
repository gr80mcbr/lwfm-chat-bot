from langchain.agents import initialize_agent
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
import os
import sys
import time
import logging
import random

from lwfm.base.Site import Site
from lwfm.base.JobDefn import JobDefn
from lwfm.base.JobStatus import JobStatus, JobStatusValues
from lwfm.base.SiteFileRef import SiteFileRef, FSFileRef
from lwfm.server.JobStatusSentinelClient import JobStatusSentinelClient
from langchain.utilities import GoogleSearchAPIWrapper
from pathlib import Path

#os.environ['REQUESTS_CA_BUNDLE'] = 'C:\\Users\\gr80m\\anaconda3\\envs\\langchain\\Lib\\site-packages\\certifi\\cacert.pem'
class LwfmAssistant():

	def __init__(self, tokens):
		self.site = Site.getSiteInstanceFactory("local")

		os.environ['OPENAI_API_KEY'] = tokens['openai']
		os.environ["GOOGLE_CSE_ID"] = tokens['google_cse']
		os.environ["GOOGLE_API_KEY"] = tokens['google']

		turbo_llm = ChatOpenAI(
			temperature=0,
			model_name='gpt-3.5-turbo'
		)

		search = GoogleSearchAPIWrapper()
		google_tool = Tool(
		    name="Google Search",
		    description="Search Google for recent results.",
		    func=search.run,
		)

		random_number_tool = Tool(
			name="Random Number Generator",
		    description="Useful when the user needs a random number.",
		    func=self.generate_random_integer,
		)

		command_tool = Tool(
			name="Command Tool",
			func=self.command,
			description="Useful when the user is giving a command (make sure to differentiate between a command and a job.  Input can only be the following: test, yell, whisper, build, or jumpshot"
		)

		upload_tool = Tool(
			name="Upload Tool",
			func=self.put,
			description="Useful when the user wants to upload a file.  Input should be a python dictionary with optional values for these fields: file:str, fileDestination:str, metadata:dict"
		)

		download_tool = Tool(
			name="Download Tool",
			func=self.get,
			description="Useful when the user wants to download a file.  Input should be a python dictionary with optional values for these fields: fileId:str, filePath: str, fileDestination: str"
		)

		find_tool = Tool(
			name="Find Tool",
			func=self.find,
			description="""Useful when the user wants to find a file reference.  Input should be a python dictionary 
			with optional values for these fields: fileId:str, fileName:str, metadata:dict.  The output is a FSFileRef Object that has a getId() method that can be used to download the file."""
		)

		login_tool = Tool(
			name="Login Tool",
			func=self.login,
			description="Useful when the user wants to log in"
		)

		submit_job_tool = Tool(
			name="Submit Job Tool",
			func=self.submitJob,
			description="""Useful when the user wants to submit a job.  The input 
			is a dict with optional values for these fields: entryPoint:str"""
		)

		loop_tool = Tool(
			name="Loop Tool",
			func=self.loop,
			description="""Useful when the user wants to loop.  The input will be a dictionary with an iteration int and an instruction"""
		)

		tools = [command_tool, login_tool, upload_tool, download_tool, find_tool, submit_job_tool, google_tool, random_number_tool, loop_tool]

		memory = ConversationBufferWindowMemory(
			memory_key="chat_history",
			k=10,
			return_messages=True
		)

		self.conversational_agent = initialize_agent(
			agent='chat-conversational-react-description',
			tools=tools,
			llm=turbo_llm,
			verbose=True,
			max_iterations=20,
			early_stopping_method='generate',
			memory=memory
		)

	def command(self, input=''):
		if input == "test":
			print("This is a test")
			return "This is a test."

		if input == "yell":
			print("LOUD NOISES!!!")
			return "LOUD NOISES!!!"

		if input == "whisper":
			print("shhh....I'm hunting rabbits")
			return "shhh....I'm hunting rabbits"

		if input == "build":
			print("building something just for you...")
			return "building something just for you..."

		if input == "jumpshot":
			result = "He shoots!..."
			random_number = random.randint(1, 3)
			if random_number < 3:
				result += "He scores!!!!"
			else:
				result += "He misses!"
			print(result)
			return result

	# Generate a random integer between a given range (inclusive)
	def generate_random_integer(self, input):
	    return random.randint(1, 100)

	def loop(self, loop):
		parsed_int = int(loop['iteration'])
		parsed_int = parsed_int - 1
		if parsed_int < 1:
			return "Okay stop"
		return loop['instruction'] + " again " + str(parsed_int) + " times"

	def login(self, input=''):
		self.site.getAuthDriver().login()
		print("Log in Successful")
		return("Logged in.")

	def submitJob(self, jobDict={}):
		jobDefn = JobDefn()
		if "name" in jobDict:
			jobDefn.setName(jobDict["name"])
		if "computeType" in jobDict:
			jobDefn.setComputeType(jobDict["computeType"])
		if "entryPoint" in jobDict:
			print("entryPoint: " + str(jobDict["entryPoint"]))
			jobDefn.setEntryPoint(jobDict["entryPoint"])
		if "jobArgs" in jobDict:
			jobDefn.setJobArgs(jobDict["jobArgs"])
		print("getting status")
		self.site.getAuthDriver().login()

		logging.info("login successful")
		status = self.site.getRunDriver().submitJob(jobDefn)
		context = status.getJobContext()
		status = self.site.getRunDriver().getJobStatus(context)
		while (not status.isTerminal()):
			time.sleep(15)
			print("getting status")
			status = self.site.getRunDriver().getJobStatus(context)
		print("job " + status.getJobContext().getId() + " " + status.getStatus().value)
		return "Job has completed."

	def put(self, repoDict={}):
		fileRef = FSFileRef()
		file = os.path.realpath(repoDict["file"])
		fileRef = FSFileRef.siteFileRefFromPath(file)
		if "metadata" in repoDict:
			fileRef.setMetadata(repoDict["metadata"])
		destFileRef = FSFileRef.siteFileRefFromPath(repoDict["fileDestination"])
		file_path = Path(file)
		self.site.getRepoDriver().put(file_path, destFileRef)
		print(file + " Successfully uploaded")
		return file + " Successfully uploaded"

	def get(self, repoDict={}):
		fileRef = FSFileRef()

		if "fileId" in repoDict:
			fileId = repoDict["fileId"]
			fileRef.setId(fileId)
		if "filePath" in repoDict:
			filePath = repoDict["filePath"]
			fileRef.setPath(filePath)
		if "fileDestination" in repoDict:
			fileDestination = repoDict["fileDestination"]
		
		destPath = Path(fileDestination)
		self.site.getRepoDriver().get(fileRef, destPath)
		print("File has been Successfully downloaded.")
		return "The file has been Successfully downloaded"

	def find(self, repoDict={}):
		fileRef = FSFileRef()
		if "fileId" in repoDict:
			fileRef.setId(repoDict["fileId"])
		if "name" in repoDict:
			fileRef.setName(repoDict["name"])
		if "metadata" in repoDict:
			fileRef.setMetadata(repoDict["metadata"])
		print ("File: ID: " + str(fileRef.getId()) + ", File Name: " + str(fileRef.getName()) + ", Metadata: " + str(fileRef.getMetadata()))
		return self.site.getRepoDriver().find(fileRef)

	def runChatbot(self, template=None, template_input=None):
		if template:
			if template_input:
				self.conversational_agent("I have this python dictionary which contains a list of parameter fields and values, remember it for future reference: " + str(template_input))
			user_lines = self.read_file_to_list(template)
			for line in user_lines:
				self.conversational_agent(line)
		else:
			user_responses = []
			print("Chatbot: Hello, How can I assist you today?")
			while True:
				user_input = input("User: ")
				if user_input.lower() == "exit":
					break
				elif user_input.lower() == "save":
					file_path = input("Where would you like to save the chat template file: ")
					self.write_list_to_file(file_path, user_responses)
				else:
					user_responses.append(user_input)
					self.conversational_agent(user_input)

	def read_file_to_list(self, file_path):
	    lines_list = []
	    with open(file_path, 'r') as file:
	        for line in file:
	            lines_list.append(line.strip())
	    return lines_list

	def write_list_to_file(self, file_path, lines_list):
	    with open(file_path, 'w') as file:
	        for line in lines_list:
	            file.write(line + '\n')

if __name__ == '__main__':
	print("running main")

	openai_token = sys.argv[1]
	google_token = sys.argv[2]
	google_cse_id = sys.argv[3]
	template = None
	template_input = None
	if len(sys.argv) > 4:
		template = sys.argv[4]
		if len(sys.argv) > 5:
			template_input = sys.argv[5]
		else:
			template_input = None

	tokens = {"openai":openai_token, "google":google_token, "google_cse":google_cse_id}

	os.environ['OPENAI_API_KEY'] = tokens['openai']
	os.environ["GOOGLE_CSE_ID"] = tokens['google']
	os.environ["GOOGLE_API_KEY"] = tokens['google_cse']

	chatbot = LwfmAssistant(tokens)
	for i in range(5):
		print("Running chatbot")
		template_input = {"outputFileName":"output" + str(i)}
		chatbot.runChatbot(template, template_input)