from langchain.agents import initialize_agent
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
import os

#os.environ['REQUESTS_CA_BUNDLE'] = 'C:\\Users\\gr80m\\anaconda3\\envs\\langchain\\Lib\\site-packages\\certifi\\cacert.pem'
os.environ['OPENAI_API_KEY'] = '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'

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

upload_tool = Tool(
	name="Upload Tool",
	func=fake_upload,
	description="Useful when the user wants to upload a file.  Input should be a python dictionary with values for these fields: fileName, filePath, storageLocation"
)

tools = [life_tool, command_tool, upload_tool]

memory = ConversationBufferWindowMemory(
	memory_key="chat_history",
	k=3,
	return_messages=True
)

conversational_agent = initialize_agent(
	agent='chat-conversational-react-description',
	tools=tools,
	llm=turbo_llm,
	verbose=True
	,
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

