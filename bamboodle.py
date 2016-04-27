#!/usr/bin/python
# coding: utf-8

import pandas
import csv
import geoip2.database
import netaddr
import geojson
import numpy as np
import scipy
import statsmodels.api as sm
from sklearn.cluster import KMeans
from matplotlib import pyplot
from beeswarm import *

class Bamboodle(pandas.DataFrame):
	# CLASS SETUP
	@property
	def _constructor(self):
		return Bamboodle
	def __init__(self, *args, **kw):
		super(Bamboodle, self).__init__(*args, **kw)
		self.username_field = 'User full name'
		self.time_field = 'Time'
		
	# PRIVATE METHODS
	# Tests whether IP falls within array of CIDR blocks (i.e. "128.97.0.0/16")
	def __ip_in_networks(self, ip, networks):
		in_network = False
		for network in networks:
			if netaddr.IPAddress(ip) in netaddr.IPNetwork(network):
				in_network = True
		if in_network is True: return 1
		else: return 0
	
	# PUBLIC METHODS
	# Subcategory: FILTERING METHODS
	# Returns data frame filtered by date/time
	def filter_datetime(self,start,end):
		return self[(self["Time"] >= start) & (self["Time"] < end)]
	# Returns data frame filtered by username
	def filter_user(self,user):
		return self[(self["User full name"] == user)]
	# Returns data frame filtered by activity
	def filter_fieldsearch(self,field,search):
		return self[(self[field].str.contains(search))]
		
	# Subcategory: STATISTICAL TESTS AND ANALYSIS
	# One-way analysis of variance test (ANOVA)
	def anova(self,column,group_by):
		grouped = self.groupby(self[group_by])[column]
		groups = []
		for name, group in grouped:
			groups.append(list(group))
		f, p = scipy.stats.f_oneway(*groups)
		return f, p
	# Ordinary least squares (OLS) regression
	def ols(self,dependent,independents):
		y = np.asarray(self[dependent]).astype(float)
		X = np.asarray(self[independents]).astype(float)
		X = sm.add_constant(X)
		return sm.OLS(y,X).fit()
		
	# Subcategory: CLUSTERING METHODS
	# Returns K-means cluster numbers for observations based on selected column(s)
	def cluster(self,column,clusters=5):
		km = KMeans(n_clusters=clusters, init='random')
		km.fit(self[column].dropna().as_matrix().reshape(-1, 1))
		b = self[[self.username_field, column]].dropna()
		b['cluster'] = km.labels_
		return b.sort([column])
		
	# Subcategory: GRADE TOOLS
	# Returns specified grades (or all grades) for students from external file
	def load_grades(self,grade_path,grade_to_select=None):
		df = pandas.read_csv(grade_path)
		full_names = []
		for index, row in df.iterrows():
			full_names.append(row["Last name"] + ", " + row["First name"])
		df[self.username_field] = full_names
		if grade_to_select is not None:
			grade_df = df[[self.username_field,grade_to_select]]
		else:
			grade_df = df
		return self.merge(grade_df, left_on=self.username_field, right_on=self.username_field, how='inner')
	
	# Subcategory: LISTS OF UNIQUE ENTRIES
	# Returns list of full names of all unique users
	def unique_users(self):
		return self[self.username_field].unique()
	def unique_ips(self):
		return self["IP address"].unique()
		
	# Subcategory: METRICS RELATED TO COUNTS AND CHARACTERISTICS OF LOG ENTRIES
	def add_weekday(self):
		b = pandas.DatetimeIndex(self['Time'])
		self['weekday'] = b.weekday
		return self
	def weekday_activity(self):
		b = self.add_weekday()
		grouped_by_student = self["weekday"].groupby(self[self.username_field])
		activity_by_student = {}
		for student, group in grouped_by_student:
			activity_by_student[student] = group.value_counts()
		return activity_by_student
	def mean_weekday_activity(self):
		b = self.add_weekday()
		grouped_by_student = self["weekday"].groupby(self[self.username_field])
		mean_weekday_by_student = []
		for student, group in grouped_by_student:
			mean_weekday_by_student.append([student,np.average(group.values)])
		b = Bamboodle(mean_weekday_by_student)
		b.columns = [self.username_field,"Mean weekday"]
		return b
	
		
	# Subcategory: METRICS RELATED TO IP ADDRESSES
	# Returns value between 0 and 1 indicating the percentage of access requests that fall within the specified networks for all users
	def ip_networks(self,networks):
		grouped_by_student = self["IP address"].groupby(self[self.username_field])
		ips_by_student = {}
		average_by_student = {}
		for student, group in grouped_by_student:
			ips_by_student[student] = []
			ips = group.unique()
			for ip in ips:
				try:
					# Checks if IP address is valid
					netaddr.ip.IPAddress(ip)
					ips_by_student[student].append(self.__ip_in_networks(ip,networks))
				except:
					pass
		for student, in_network in ips_by_student.iteritems():
			average_by_student[student] = np.average(in_network)
		in_network_list = []
		for student, avg in average_by_student.iteritems():
			in_network_list.append([student,avg])
		b = Bamboodle(in_network_list)
		b.columns = [self.username_field,"IP address in network(s)"]
		return b
	# Returns list of unique IP geolocated cities for all users
	def ip_locations(self):
		locations_by_user = {}
		ipreader = geoip2.database.Reader('lib/GeoLite2-City.mmdb')
		grouped_by_student = self["IP address"].groupby(self[self.username_field])
		for user, group in grouped_by_student:
			locations_by_user[user] = []
			ips = group.unique()
			for ip in ips:
				try:
					# Checks if IP address is valid
					netaddr.ip.IPAddress(ip)
					ipresponse = ipreader.city(ip)
					loc_string = ipresponse.city.name + ", " + ipresponse.subdivisions.most_specific.name + ", " + ipresponse.country.name
					if loc_string not in locations_by_user[user]:
						locations_by_user[user].append(loc_string)
				except:
					pass
		return locations_by_user
	# Returns GeoJSON of unique IP geolocated points for all users
	def ip_locations_geojson(self):
		locations_by_user = {}
		ipreader = geoip2.database.Reader('lib/GeoLite2-City.mmdb')
		ips = self["IP address"]
		ip_counts = ips.value_counts()
		features = []
		for ip, count in ip_counts.iteritems():
			try:
				# Checks if IP address is valid
				netaddr.ip.IPAddress(ip)
				ipresponse = ipreader.city(ip)
				features.append(geojson.Feature(geometry=geojson.Point((ipresponse.location.longitude, ipresponse.location.latitude)), properties={ "loc_name": ipresponse.city.name + ", " + ipresponse.subdivisions.most_specific.name + ", " + ipresponse.country.name, "count": count }))
			except:
				pass
		feature_collection = geojson.FeatureCollection(features)
		return geojson.dumps(feature_collection, sort_keys=True)
	
	# Subcategory: VISUALIZATION METHODS
	# Box Plot
	def draw_box(self,columns,path=None):
		plot = self[columns].plot.box()
		if path is not None:
			fig = plot.get_figure()
			fig.savefig(path)
	# Swarm plot
	def draw_swarm(self,columns,path=None):
		values = []
		for column in self[columns]:
			values.append(self[column].values)
		fig = pyplot.figure()
		ax = fig.add_subplot(111)
		beeswarm(values, method="square", labels=columns, ax=ax)
		if path is not None:
			fig.savefig(path)
	