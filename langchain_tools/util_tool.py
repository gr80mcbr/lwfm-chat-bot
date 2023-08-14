from lwfm.base.Site import Site
from lwfm.base.JobDefn import JobDefn
from lwfm.base.JobStatus import JobStatus, JobStatusValues
from lwfm.base.SiteFileRef import SiteFileRef, FSFileRef
from lwfm.server.JobStatusSentinelClient import JobStatusSentinelClient

import os
import sys
import time
import logging
import random

class LwfmTool():

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

	