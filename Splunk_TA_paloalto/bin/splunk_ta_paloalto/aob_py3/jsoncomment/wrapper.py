#!/bin/python
# coding: utf-8

##########################################################################################################################################

# A Class to simulate dynamic inheritance of Modules and Classes
class GenericWrapper:
	def __init__(self, wrapped):
		self.wrapped = wrapped

	# Fallback lookup for undefined methods
	def __getattr__(self, name):
		return getattr(self.wrapped, name)

##########################################################################################################################################
