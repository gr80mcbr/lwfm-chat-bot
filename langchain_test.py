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

#os.environ['REQUESTS_CA_BUNDLE'] = 'C:\\Users\\gr80m\\anaconda3\\envs\\langchain\\Lib\\site-packages\\certifi\\cacert.pem'
class ChatBot():

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

		command_tool = Tool(
			name="Command Tool",
			func=self.command,
			description="Useful when the user is giving a command.  Input can only be the following: test, yell, whisper, build, or jumpshot"
		)

		upload_tool = Tool(
			name="Upload Tool",
			func=self.put,
			description="Useful when the user wants to upload a file.  Input should be a python dictionary with optional values for these fields: file:str, metadata:dict"
		)

		download_tool = Tool(
			name="Download Tool",
			func=self.get,
			description="Useful when the user wants to download a file.  Input should be a python dictionary with optional values for these fields: fileId:str, fileDestination: str"
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
			is a dict with optional values for these fields: name:str, computeType:str, entryPoint:str, jobArgs:dict"""
		)

		tools = [command_tool, login_tool, upload_tool, download_tool, find_tool, submit_job_tool, google_tool]

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
			max_iterations=10,
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
		print("getting context")
		context = status.getJobContext()
		print("getting status")
		status = self.site.getRunDriver().getJobStatus(context)
		print("this is the status: " + str(status.isTerminal()))
		while (not status.isTerminal()):
			time.sleep(15)
			print("getting status")
			status = self.site.getRunDriver().getJobStatus(context)
		print("job " + status.getJobContext().getId() + " " + status.getStatus().value)
		return "Job has completed."

	def put(self, repoDict={}):
	    fileRef = FSFileRef()
	    if "file" in repoDict:
	        file = os.path.realpath(repoDict["file"])
	        fileRef = FSFileRef.siteFileRefFromPath(file)
	        if "metadata" in repoDict:
	            fileRef.setMetadata(repoDict["metadata"])
	    destFileRef = FSFileRef.siteFileRefFromPath(os.path.expanduser('~'))
	    self.site.getRepoDriver().put(file, destFileRef)
	    print(file + " Successfully uploaded")
	    return file + " Successfully uploaded"

	def get(self, repoDict={}):
		if "fileId" in repoDict:
			fileId = repoDict["fileId"]
		if "fileDestination" in repoDict:
			fileDestination = repoDict["fileDestination"]
		fileRef = FSFileRef()
		fileRef.setId(fileId)
		destPath = Path(fileDestination)
		self.site.getRepoDriver().get(fileRef, destPath)
		print("File has been Successfully downloaded.")
		return "The file has been Successfully downloaded"

	def find(self, repoDict={}):
		fileRef = FSFileRef()
		if "fileId" in repoDict:
			fileRef.setId(repoDict["fileId"])
		if "name" in repoDict:
			fileRef.setId(repoDict["name"])
		if "metadata" in repoDict:
			fileRef.setId(repoDict["metadata"])
		print ("File: ID: " + fileRef.getId() + ", File Name: " + fileRef.getName() + ", Metadata: " + str(fileRef.getMetadata()))
		return self.site.getRepoDriver().find(fileRef)

	def runChatbot(self):
		print("Chatbot: Hello, How can I assist you today?")
		while True:
			user_input = input("User: ")
			if user_input == "exit":
				break
			self.conversational_agent(user_input)

if __name__ == '__main__':
	print("running main")
	openai_token = sys.argv[1]
	google_token = sys.argv[2]
	google_cse_id = sys.argv[3]

	tokens = {"openai":openai_token, "google":google_token, "google_cse":google_cse_id}

	os.environ['OPENAI_API_KEY'] = tokens['openai']
	os.environ["GOOGLE_CSE_ID"] = tokens['google']
	os.environ["GOOGLE_API_KEY"] = tokens['google_cse']

	ChatBot(tokens).runChatbot()