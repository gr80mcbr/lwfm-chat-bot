from lwfm.base.Site import Site
from lwfm.base.JobDefn import JobDefn
from lwfm.base.JobStatus import JobStatus, JobStatusValues
from lwfm.base.SiteFileRef import SiteFileRef, FSFileRef
from lwfm.server.JobStatusSentinelClient import JobStatusSentinelClient

from langchain.utilities import GoogleSearchAPIWrapper
from langchain.agents import Tool

import os
import sys
import time
import logging
import random

class UtilTool():

	def __init__(self):

		search = GoogleSearchAPIWrapper()
		self.google_tool = Tool(
		    name="Google Search",
		    description="Search Google for recent results.",
		    func=search.run,
		)

		self.random_number_tool = Tool(
			name="Random Number Generator",
		    description="Useful when the user needs a random number.",
		    func=self.generate_random_integer,
		)

		self.command_tool = Tool(
			name="Command Tool",
			func=self.command,
			description="Useful when the user is giving a command (make sure to differentiate between a command and a job.  Input can only be the following: test, yell, whisper, build, or jumpshot"
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

	