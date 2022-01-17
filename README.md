# Clustering GPS Tracker Activity

## About

At the end of 2021, I replaced my Fitbit GPS tracker with a Garmin watch. I realized that I would no longer be able to access 3 years worth of running and biking data I accumulated on my Fitbit since I would no longer be accessing my Fitbit account. Therefore, I thought I'd turn this situation into a small machine learning project to 1) download all GPS data that Fitbit provides for each activity and 2) analyze each GPS activity and group them together using K-Means to learn about the type of activities I accumulated between 2019 and 2021.

## Usage
`**downloadRun.py**`: Python script to open Fitbit account, load all links to activities and download .tcx files that contain activity stats; script is split into two main functions:
* `download_run_links()`
  * Use Selenium Python to access Fitbit account, load all GPS activities, save links to each activity .tcx files into a text file to access later
  * Only ran once to output text file to archive links to activities of interest instead of having to run Selenium each time I wanted to know which activities were needing to be downloaded
* `download_run_files()`
  * Use Selenium Python to iterate over saved text file from above, accessing each link and downloading .txc fi;e
  * Designed to be run in chunks - checks if activity's .tcx file has already been downloaded (if yes, then link not visited)
  
`**parseRuns.py**`
