# bamboodle

### Extension for pandas enabling direct processing and statistical analysis of Moodle log files
#### Developed by Nick Burkhart (nickburkhart.com)

Additional documentation will be added shortly.

This product includes GeoLite2 data created by MaxMind, available from
<a href="http://www.maxmind.com">http://www.maxmind.com</a>.

Creating a Bamboodle object from a Moodle log file CSV:
```
bb = Bamboodle(pandas.read_csv('Fall2015.csv'))
```

Adds an integer column for weekday to activity records (0 = Monday, 6 = Sunday):
```
print bb.add_weekday()
```

Counts actions taken by weekday (0 = Monday, 6 = Sunday) (groups by user automatically):
```
print bb.weekday_activity()
```

Calculates mean weekday of activity records  (0 = Monday, 6 = Sunday) (groups by user automatically):
```
print bb.mean_weekday_activity()
```

Generates GeoJSON with a point for each unique IP address; contains attributes for activity count:
```
print bb.ip_locations_geojson()
```

Retrieves "city, state, country" locations for all users in input (can be pre-filtered by user or any other characteristic, as in this example):
```
print bb.filter_user('NAME, USER').ip_locations()
```

Calculates percentage of time that user(s) is/are within the networks passed to this function, then joins grades for a specific assignment to the results (example of a two-step process):
```
ip_list = ["192.168.0.0/16","10.0.0.0/16"]
print bb.ip_networks(ip_list).load_grades('Fall2015_Grades.csv','assignment3')
```

Calculates percentage of time that user(s) is/are within the networks passed to this function
```
ip_list = ["192.168.0.0/16","10.0.0.0/16"]
print bb.filter_user('NAME, USER').ip_networks(ip_list)
```

Calculates percentage of time that user(s) is/are within the networks passed to this function, as well as K-means cluster (4 total clusters) for this attribute; grades for assignment are joined also
```
ip_list = ["192.168.0.0/16","10.0.0.0/16"]
print bb.ip_networks(ip_list).cluster("IP address in network(s)",4).load_grades('Fall2015_Grades.csv','assignment3')
```

Performs one-way ANOVA test of midterm exam score across cluster groups set up on basis of on-campus vs. off-campus IP use
```
ip_list = ["192.168.0.0/16","10.0.0.0/16"]
print bb.ip_networks(ip_list).cluster("IP address in network(s)").load_grades('Fall2015_Grades.csv','midterm').replace('-', 0).anova("midtern","cluster")
```

Performs one-way ANOVA test of 
```
print bb.mean_weekday_activity().cluster("Mean weekday").load_grades('Fall2015_Grades.csv','midterm').replace('-', 0).anova("midterm","cluster")
```

Runs an OLS regression model using midterm grades as dependent variable and (1) on-campus vs. off-campus IP use and (2) average weekday of content access as dependent variables
```
ip_list = ["192.168.0.0/16","10.0.0.0/16"]
ips = bb.ip_networks(ip_list)
ols = bb.mean_weekday_activity().load_grades('Fall2015_Grades.csv','midterm').replace('-', 0).merge(ips).ols("midterm",["Mean weekday","IP address in network(s)"])
print ols.summary()
```
