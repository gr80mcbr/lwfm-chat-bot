from langchain.agents import initialize_agent
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
import os

from lwfm.base.Site import Site
from lwfm.base.JobDefn import JobDefn
from lwfm.base.JobStatus import JobStatus, JobStatusValues
from lwfm.base.SiteFileRef import SiteFileRef, FSFileRef
from lwfm.server.JobStatusSentinelClient import JobStatusSentinelClient

#os.environ['REQUESTS_CA_BUNDLE'] = 'C:\\Users\\gr80m\\anaconda3\\envs\\langchain\\Lib\\site-packages\\certifi\\cacert.pem'
os.environ['OPENAI_API_KEY'] = ''

turbo_llm = ChatOpenAI(
	temperature=0,
	model_name='gpt-3.5-turbo'
)

def meaning_of_life(input=''):
	print("The meaning of life is 42")
	return "The meaning of life is 42"

def command(input=''):
	if input == "test":
		print("This is a test")
		return "This is a test."

	if input == "yell":
		print("LOUD NOISES!!!")
		return "LOUD NOISES!!!"

	if input == "whisper":
		print("shhh....I'm hunting rabbits")
		return "shhh....I'm hunting rabbits"

def fake_upload(input={}):
	processing = True
	fileName = ""
	filePath = ""
	storageLocation = ""
	while processing:
		print(str(input))
		if input["fileName"]:
			fileName = input["fileName"]
		else:
			print("Must provide file name")
			processing = False

		if input["filePath"]:
			filePath = input["filePath"]
		else: 
			print("Must provide file path")
			processing = False

		if input["storageLocation"]:
			storageLocation = input["storageLocation"]
		else:
			print("Must provide storage")
			processing = False
		processing = False
	print("uploading " + filePath + " as " + fileName + " to " + storageLocation)

def login(site="local"):
	site = site.getSiteInstanceFactory(site)
	site.getAuthDriver().login()
	print("Log in Successful")

def submitJob(site="local", jobDict={}) :
	site = site.getSiteInstanceFactory(site)
	jobDefn = JobDefn()
    if "name" is in jobDict:
    	jobDefn.setName(jobDict["name"])
    if "computeType" is in jobDict:
    	jobDefn.setComputeType(jobDict["computeType"])
    if "entryPoint" is in jobDict:
    	jobDefn.setEntryPoint(jobDict["entryPoint"])
    if "jobArgs" is in jobDict:
    	jobDefn.setJobArgs(jobDict["jobArgs"])
	site.getRunDriver().submitJob(jobDefn, parentContext)

def put(site="local", repoDict={}):
	site = site.getSiteInstanceFactory(site)
	fileRef = FSFileRef()
	if "file" is in repoDict:
		file = os.path.realpath(repoDict["file"])
	    fileRef = FSFileRef.siteFileRefFromPath(file)
		if "metadata" is in repoDict:
			fileRef.setMetadata(repoDict["metadata"])
	site.getRepoDriver().put(file, destFileRef)
	print(file + " Successfully uploaded")

def get(site="local", fileId="", dest=""):
	site = site.getSiteInstanceFactory(site)
	fileRef = FSFileRef()
	fileRef.setId(fileId)
    destPath = Path(dest)
    site.getRepoDriver().get(fileRef, destPath)
    print("File has been Successfully downloaded.")

def find(site="local", repoDict={})
	site = site.getSiteInstanceFactory(site)
	fileRef = FSFileRef()
	if "fileId" is in repoDict:
    	fileRef.setId(repoDict["fileId"])
    if "name" is in repoDict:
    	fileRef.setId(repoDict["name"])
    if "metadata" is in repoDict:
    	fileRef.setId(repoDict["metadata"])
    print ("File: ID: " + fileRef.getId() + ", File Name: " + fileRef.getName() + ", Metadata: " + str(fileRef.getMetadata()))
    return site.getRepoDriver().find(fileRef)

life_tool = Tool(
	name="Meaning of Life",
	func=meaning_of_life,
	description="Useful for when you need to answer a question about the meaning of life."
)

command_tool = Tool(
	name="Command Tool",
	func=command,
	description="Useful when the user is giving a command.  Input should be either test, yell, or whisper"
)

# upload_tool = Tool(
# 	name="Upload Tool",
# 	func=fake_upload,
# 	description="Useful when the user wants to upload a file.  Input should be a python dictionary with values for these fields: fileName, filePath, storageLocation"
# )

upload_tool = Tool(
	name="Upload Tool",
	func=put,
	description="Useful when the user wants to upload a file.  Input should be an optional string for the site and a python dictionary with values for these fields: file:str, metadata:dict"
)

download_tool = Tool(
	name="Download Tool",
	func=get,
	description="Useful when the user wants to download a file.  Input should be an optional string for the site, a string for the file id, and a string for the destination path"
)

find_tool = Tool(
	name="Find Tool",
	func=find,
	description="""Useful when the user wants to find a file reference.  Input should be an optional string for the site and a python dictionary 
	with values for these fields: fileId:str, fileName:str, metadata:dict.  The output is a FSFileRef Object that has a getId() method that can be used to download the file."""
)

login_tool = Tool(
	name="Login Tool",
	func=login,
	description="Useful when the user wants to log into to an application called lwfm.  The input is an optional string for the site"
)

submit_job_tool = Tool(
	name="Submit Job Tool",
	func=submitJob,
	description="""Useful when the user wants to submit a job.  The inputs are an optional str for the site, 
	and a dict with values for these fields: name:str, computeType:str, entryPoint:str, jobArgs:dict"""
)

tools = [life_tool, command_tool, login_tool, upload_tool, download_tool, find_tool, submit_job_tool]

memory = ConversationBufferWindowMemory(
	memory_key="chat_history",
	k=3,
	return_messages=True
)

conversational_agent = initialize_agent(
	agent='chat-conversational-react-description',
	tools=tools,
	llm=turbo_llm,
	verbose=True,
	max_iterations=3,
	early_stopping_method='generate',
	memory=memory
)
print("Chatbot: Hello, How can I assist you today?")
while True:
	user_input = input("User: ")
	if user_input == "exit":
		break
	conversational_agent(user_input)