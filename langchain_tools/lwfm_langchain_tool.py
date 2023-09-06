from lwfm.base.Site import Site
from lwfm.base.JobDefn import JobDefn
from lwfm.base.JobStatus import JobStatus, JobContext, JobStatusValues
from lwfm.base.SiteFileRef import SiteFileRef, FSFileRef
from lwfm.server.JobStatusSentinelClient import JobStatusSentinelClient

from langchain.agents import Tool

import os
import sys
import time
import logging
from pathlib import Path

class LwfmTool():

	def __init__(self):
		self.site = Site.getSiteInstanceFactory("local")
		self.jobContext = JobContext()

		self.upload_tool = Tool(
			name="Upload Tool",
			func=self.put,
			description="Useful when the user wants to upload a file.  Input should be a python dictionary with optional values for these fields: file:str, fileDestination:str, metadata:dict"
		)

		self.download_tool = Tool(
			name="Download Tool",
			func=self.get,
			description="Useful when the user wants to download a file.  Input should be a python dictionary with optional values for these fields: filePath: str, fileDestination: str"
		)

		self.find_tool = Tool(
			name="Find Tool",
			func=self.find,
			description="""Useful when the user wants to find a file reference.  Input should be a python dictionary 
			with optional values for these fields: fileId:str, fileName:str, metadata:dict.  The output is a FSFileRef Object that has a getId() method that can be used to download the file."""
		)

		self.login_tool = Tool(
			name="Login Tool",
			func=self.login,
			description="Useful when the user wants to log in"
		)

		self.submit_job_tool = Tool(
			name="Submit Job Tool",
			func=self.submitJob,
			description="""Useful when the user wants to submit a job.  The input 
			is a dict with optional values for these fields: entryPoint:str"""
		)

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
		status = self.site.getRunDriver().submitJob(jobDefn, self.jobContext)
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
		self.site.getRepoDriver().put(file_path, destFileRef, self.jobContext)
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
		self.site.getRepoDriver().get(fileRef, destPath, self.jobContext)
		print("File has been Successfully downloaded.")
		return "The file has been Successfully downloaded"

	def find(self, repoDict={}):
		fileRef = FSFileRef()
		if "name" in repoDict:
			fileRef.setName(repoDict["name"])
		if "metadata" in repoDict:
			fileRef.setMetadata(repoDict["metadata"])
		print ("File: ID: " + str(fileRef.getId()) + ", File Name: " + str(fileRef.getName()) + ", Metadata: " + str(fileRef.getMetadata()))
		return self.site.getRepoDriver().find(fileRef)

	