import pandas as pd
import re
import xml.etree.ElementTree as et
import numpy as np
import os

DOWNLOADS = '/Users/EdwinReyesHerrera/Downloads'
RUN_FOLDER = "/Users/EdwinReyesHerrera/Documents/Python_Projects/Fitbit Runs/Fitbit TCX Files"


def parse_tcx(file):
    """
    Function to read .tcx files and extract each datapoint into dataframe row
    :param file: path to a .tcx file
    :return: dataframe that contains all data points collected by Fitbit watch
    """

    # Staging dataframe
    run_df = pd.DataFrame(columns=['file_name', 'id', 'type', 'calories', 'time', 'latitude',
                                   'longitude', 'altitude', 'distance', 'heart_rate'])

    # Loading tcx file
    file_id = re.sub('.tcx', '', file)
    tcx_file = et.parse(file)
    root = tcx_file.getroot()

    ns = {
        'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
    }

    # Getting activity type & date of activity
    activity_type = root.find('./tcx:Activities/tcx:Activity', namespaces=ns).get("Sport")
    activity_date = root.find('./tcx:Activities/tcx:Activity/tcx:Id', namespaces=ns).text

    # Getting total calories for activity
    try:
        total_calories = root.find('./tcx:Activities/tcx:Activity/tcx:Lap/tcx:Calories', namespaces=ns).text
    except AttributeError:
        total_calories = '0'

    df_row = []
    activity = root.findall('./tcx:Activities/tcx:Activity/tcx:Lap/tcx:Track', namespaces=ns)
    # There were some tcx files that were downloaded that didn't contain any GPS data
    if len(activity) > 0:
        for lap in activity:
            # Grabbing each data point watch made during an activity & its relevant stats
            for track_point in lap.findall('./tcx:Trackpoint', namespaces=ns):
                try:
                    df_row.extend([file_id, activity_date, activity_type])
                    df_row.append(total_calories)
                    df_row.append(track_point.find('./tcx:Time', namespaces=ns).text)
                    df_row.append(track_point.find('./tcx:Position/tcx:LatitudeDegrees', namespaces=ns).text)
                    df_row.append(track_point.find('./tcx:Position/tcx:LongitudeDegrees', namespaces=ns).text)
                    df_row.append(track_point.find('./tcx:AltitudeMeters', namespaces=ns).text)
                    df_row.append(track_point.find('./tcx:DistanceMeters', namespaces=ns).text)
                    df_row.append(track_point.find('./tcx:HeartRateBpm/tcx:Value', namespaces=ns).text)
                except AttributeError:
                    df_row.append('0')
                finally:
                    run_df.loc[len(run_df)] = df_row  # Appending each track point stats as row
                    df_row.clear()
    else:
        # For tcx files that didn't return any GPS data
        df_row = [file_id, activity_date, activity_type, total_calories, activity_date, 0, 0, 0, 0, 0]
        run_df.loc[len(run_df)] = df_row

    # Changing field data types
    run_df = run_df.astype({'calories': 'float', 'time': 'str', 'latitude': 'float', 'longitude': 'float',
                            'altitude': 'float', 'distance': 'float', 'heart_rate': 'float'})

    # Removing extra rows at the end of activity that have no info if activity was paused on watch
    # before it was officially ended
    run_df = run_df.loc[0:run_df['distance'].idxmax()]

    return run_df


def summarize_run(df):
    """
    Function to summarize a parsed dataframe further if only interested in high-level stats
    Add description for function
    :param df: dataframe to aggregate
    :return: dataframe with one row that gives summarized stats of activity
    """

    # Converting altitude to feet & distance to miles, both from meters
    df = df.assign(altitude=df['altitude'] * 3.28084,
                   distance=df['distance'] * 0.000621371,
                   time=df['time'].replace(to_replace='\\.\\d+-\\d+:\\d+$|T', value=' ', regex=True),
                   )
    # Implementing 'lag' to stage elev. gain/loss
    df = df.assign(prev_elev=df['altitude'].shift(1),
                   time=pd.to_datetime(df['time'])
                   )
    # New fields for elev. gain vs elev. loss
    df = df.assign(elev_gain=np.where(df['altitude'] - df['prev_elev'] > 0, df['altitude'] - df['prev_elev'], 0),
                   elev_loss=np.where(df['altitude'] - df['prev_elev'] < 0, df['altitude'] - df['prev_elev'], 0))

    # Creating new field to get amount of time elapsed between track points
    # Running total of elapsed time to get total time elapsed at each track point
    df['prev_time'] = df['time'].shift(1)
    df['elapsed_time'] = (df['time'] - df['prev_time'])
    df['elapsed_time'] = df['elapsed_time'].fillna(pd.Timedelta(seconds=0))
    df['elapsed_time'] = df['elapsed_time'].cumsum()

    # Creating field to get average pace at each track point
    df['pace'] = df['elapsed_time'] / df['distance']

    if len(df) == 1:  # tcx files that returned no GPS data
        df = df.groupby(['file_name', 'type']).agg(
            {
                'time': ['min', 'max'],
                'elev_gain': 'sum',
                'elev_loss': 'sum',
                'heart_rate': ['sum', 'min', 'max'],
                'distance': 'max',
                'pace': 'min',
                'calories': 'max'
            }
        ).reset_index()

        # Renaming fields
        df.columns = df.columns.get_level_values(0)
        df.columns = ['file', 'type', 'start_time', 'end_time', 'total_elev_gain',
                      'total_elev_loss', 'avg_BPM', 'min_heartrate', 'max_heartrate',
                      'total_dist', 'best_pace', 'total_calories']
        df['total_time'] = 0
        df['avg_pace'] = 0

    else:
        df = df.groupby(['file_name', 'type']).agg(
            {
                'time': ['min', 'max'],
                'elev_gain': 'sum',
                'elev_loss': 'sum',
                'heart_rate': ['mean', 'min', 'max'],
                'distance': 'max',
                'pace': 'min',
                'calories': 'max'
            }
        ).reset_index()

        df.columns = df.columns.get_level_values(0)
        df.columns = ['file', 'type', 'start_time', 'end_time', 'total_elev_gain',
                      'total_elev_loss', 'avg_BPM', 'min_heartrate', 'max_heartrate',
                      'total_dist', 'best_pace', 'total_calories']

        # Duration of activity
        df['total_time'] = df['end_time'] - df['start_time']

        # Converting total time to total minutes and total minutes as decimal
        df['total_time'] = df['total_time'].dt.total_seconds() / 60

        # Overall average pace for activity
        df['avg_pace'] = df['total_time'] / df['total_dist']

        # Converting best pace during run to total minutes and total minutes as decimal
        df['best_pace'] = df['best_pace'].dt.total_seconds() / 60

    return df


################################################
# Creating csv file to summarize each activity #
################################################

# List of all tcx files downloaded
tcx_files = os.listdir(RUN_FOLDER)
tcx_files.sort()

# Collecting all summarized Fitbit Activities into list
summarized_dfs = []
for f in tcx_files:
    if f.endswith('.tcx'):
        loop_df = summarize_run(parse_tcx('{}/{}'.format(RUN_FOLDER, f)))
        summarized_dfs.append(loop_df)
        print('{} Successful : {}/{} Completed'.format(f, tcx_files.index(f) + 1, len(tcx_files)))

# Concatenating all summarized activities into one dataframe and saving to csv file
final_df = pd.concat(summarized_dfs, ignore_index=True)
final_df.to_csv('fitbit_activities.csv')
