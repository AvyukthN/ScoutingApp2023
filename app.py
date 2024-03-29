from flask import Flask, render_template, request, url_for, redirect
import gspread
from itsdangerous import NoneAlgorithm
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
import json
from multiprocessing import Value
import time
import pandas as pd
import math
import numpy as np
import os
from datetime import datetime

balls_shot = Value('i', 0)
accidents = Value('i', 0)
e1 = Value('i', 0)
e2 = Value('i', 0)

app = Flask(__name__)

def init_sheet(sheet_num):
	scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

	creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

	client = gspread.authorize(creds)

	sheet_name = "RoboLoco-Competition-Scouting"

	if sheet_num == 1:
		sheet = client.open(sheet_name).worksheet('teleop')
	if sheet_num == 2:
		sheet = client.open(sheet_name).worksheet('autonomous')

	return sheet

@app.route('/', methods=['GET', 'POST'])
def home():
	balls_shot = 0
	if request.method == 'POST':
		for key, val in request.form.items():
			if key == 'team_name':
				context = {
					'team_name': val
				}

				with open('./team_name.txt', 'w') as f:
					f.write(val)

		return redirect('/observing')
	if request.method == 'GET':
		return render_template('home.html')

def analytics_display(mode, for_search=False):
	# if mode == 'teleop':
		# sheet = init_sheet(1)
	# else:
		# sheet = init_sheet(2)
	
	# data = pd.read_csv('./observations/converted.csv')
	data = pd.read_csv('./compilation_saturday.csv')

	# data = sheet.get_all_records()

	graph_data = {}
	radar_data = {}
	high_pts = {}
	mid_pts = {}
	low_pts = {}
	dock_hash = {}
	engage_hash = {}
	cone_pts = {}
	cube_pts = {}

	name_set = set([])

	for index, row in data.iterrows():
		# print(row)
		team_name = row['team_name'] 
		if team_name not in name_set:
			name_set.add(team_name)
			graph_data.update({team_name: []})
			radar_data.update({team_name: []})
			high_pts.update({team_name: []})
			mid_pts.update({team_name: []})
			low_pts.update({team_name: []})
			dock_hash.update({team_name: []})
			engage_hash.update({team_name: []})
			cone_pts.update({team_name: []})
			cube_pts.update({team_name: []})
		
		if mode == 'teleop':
			high_pt = int(row['teleopHighCone']) + int(row['teleopHighCube'])
			mid_pt = int(row['teleopMidCone']) + int(row['teleopMidCube'])
			low_pt = int(row['teleopLowCone']) + int(row['teleopLowCube'])
			cone_pt = int(row['teleopHighCone']) + int(row['teleopMidCone'])
			cube_pt = int(row['teleopHighCube']) + int(row['teleopMidCube'])
			dock_pt = int(row[f'{mode}Dock']) if mode == 'teleop' else 0
			engage_pt = int(row[f'{mode}Engage']) if mode == 'teleop' else 0
			
			total_score = high_pt + mid_pt + low_pt 
			
			graph_data[team_name].append(total_score)
			high_pts[team_name].append(high_pt)
			mid_pts[team_name].append(mid_pt)
			low_pts[team_name].append(low_pt)
			dock_hash[team_name].append(dock_pt)
			engage_hash[team_name].append(engage_pt)
			cone_pts[team_name].append(cone_pt)
			cube_pts[team_name].append(cube_pt)

			if len(radar_data[team_name]) > 0:
				radar_data[team_name][0][0] += high_pt
				radar_data[team_name][0][1] += mid_pt
				radar_data[team_name][0][2] += low_pt
				radar_data[team_name][0][3] += dock_pt
				radar_data[team_name][0][4] += engage_pt
			else:
				radar_data[team_name].append([high_pt, mid_pt, low_pt, dock_pt, engage_pt])
		
		if mode == 'autonomous':
			high_pt = int(row['autoHighCone']) + int(row['autoHighCube'])
			mid_pt = int(row['autoMidCone']) + int(row['autoMidCube'])
			low_pt = int(row['autoLowCone']) + int(row['autoLowCube'])
			cone_pt = int(row['teleopHighCone']) + int(row['teleopMidCone'])
			cube_pt = int(row['teleopHighCube']) + int(row['teleopMidCube'])
			dock_pt = int(row[f'{mode[:4]}Dock']) if mode == 'autonomous' else 0
			engage_pt = int(row[f'{mode[:4]}Engage']) if mode == 'autonomous' else 0

			total_score = high_pt + mid_pt + low_pt 
			
			graph_data[team_name].append(total_score)
			high_pts[team_name].append(high_pt)
			mid_pts[team_name].append(mid_pt)
			low_pts[team_name].append(low_pt)
			dock_hash[team_name].append(dock_pt)
			engage_hash[team_name].append(engage_pt)
			cone_pts[team_name].append(cone_pt)
			cube_pts[team_name].append(cube_pt)
			
			if len(radar_data[team_name]) > 0:
				radar_data[team_name][0][0] += high_pt
				radar_data[team_name][0][1] += mid_pt
				radar_data[team_name][0][2] += low_pt
				radar_data[team_name][0][3] += dock_pt
				radar_data[team_name][0][4] += engage_pt
			else:
				radar_data[team_name].append([high_pt, mid_pt, low_pt, dock_pt, engage_pt])
			
			# if len(radar_data[team_name]) > 0:
			# 	radar_data[team_name][0][0] += high_goal
			# 	radar_data[team_name][0][1] += low_goal 
			# 	radar_data[team_name][0][2] += climb
			# else:
			# 	radar_data[team_name].append([high_goal, low_goal, climb])
			
	
	listify = lambda l: [[str(key), l[key]] for key in l]
	avg_listify = lambda l: [[arr[0], np.average(np.array(arr[1]))] for arr in l]
	med_listify = lambda l: [[arr[0], np.median(np.array(arr[1]))] for arr in l]
	sum_listify = lambda l: [[arr[0], np.sum(np.array(arr[1]))] for arr in l]

	graph_data_arr = []
	for key in graph_data:
		graph_data_arr.append([key, graph_data[key]])
	
	final_data = listify(graph_data)
	final_radar_data = listify(radar_data)
	high_pts_data = listify(high_pts)
	mid_pts_data = listify(mid_pts)
	low_pts_data = listify(low_pts)
	cone_pts_data = listify(cone_pts)
	cube_pts_data = listify(cube_pts)
	# climb_data = listify(climb_hash)
	high_avg_data = avg_listify(high_pts_data)
	mid_avg_data = avg_listify(mid_pts_data)
	low_avg_data = avg_listify(low_pts_data)
	cone_avg_data = avg_listify(cone_pts_data)
	cube_avg_data = avg_listify(cube_pts_data)
	# climb_avg_data = avg_listify(climb_data)
	med_data = med_listify(graph_data_arr)
	sum_data = sum_listify(graph_data_arr)
	dock_data = listify(dock_hash)
	engage_data = listify(engage_hash)

	for i in range(len(dock_data)):
		arr = dock_data[i][1]
		dock_data[i][1] = np.sum(np.array(arr))
	
	for i in range(len(engage_data)):
		arr = engage_data[i][1]
		engage_data[i][1] = np.sum(np.array(arr))

	print(dock_data)
	print(engage_data)

	sd_high = {}
	sd_mid = {}
	sd_low = {}
	sd_climb = {}

	for team in high_pts_data:
		vals = np.array(team[1])

		sd_high.update({team[0]: np.std(vals)})
	for team in mid_pts_data:
		vals = np.array(team[1])

		sd_mid.update({team[0]: np.std(vals)})
	for team in low_pts_data:
		vals = np.array(team[1])

		sd_low.update({team[0]: np.std(vals)})
	# for team in climb_data:
	# 	vals = np.array(team[1])

	# 	sd_climb.update({team[0]: np.std(vals)})

	sd_high_arr = listify(sd_high)
	sd_mid_arr = listify(sd_mid)
	sd_low_arr = listify(sd_low)
	sd_climb_arr = listify(sd_climb)

	if for_search:
		return len(final_data),final_data,final_radar_data,high_pts_data,mid_pts_data,low_pts_data,climb_data,sd_high_arr,sd_low_arr,sd_climb_arr,high_avg_data,mid_avg_data,low_avg_data,climb_avg_data,med_data,sum_data
	else:
		return render_template('analytics_display.html', 
					len=len(final_data), 
					final_data=final_data, 
					radar_data=final_radar_data, 
					high_goals_data=high_pts_data, 
					mid_pts_data=mid_pts_data,
					low_goals_data=low_pts_data,
					sd_high=sd_high_arr,
					sd_mid=sd_mid_arr,
					sd_low=sd_low_arr,
					sd_climb=sd_climb_arr,
					high_avg_data=high_avg_data,
					mid_avg_data=mid_avg_data,
					low_avg_data=low_avg_data,
					med_data=med_data,
					sum_data=sum_data,
					dock_data=dock_data,
					engage_data=engage_data,
					cone_avg_data=cone_avg_data,
					cube_avg_data=cube_avg_data
					)

@app.route('/analytics_teleop', methods=['GET', 'POST'])
def analytics_display_teleop():
	return analytics_display('teleop')

@app.route('/analytics_auto', methods=['GET'])
def analytics_display_auto():
	return analytics_display('autonomous')

@app.route('/analytics_search', methods=['GET', 'POST'])
def analytics_search():
	data = analytics_display('teleop', True)
	auto_data = analytics_display('autonomous', True)

	print(data)

	final_data = data[1]
	high_goals_data = data[3]
	low_goals_data = data[4]
	climb_data = data[5]
	high_avg = data[9]
	low_avg = data[10]
	climb_avg = data[11]
	
	a_final_data = auto_data[1]
	# a_high_goals_data = auto_data[3]
	# a_low_goals_data = auto_data[4]
	# a_climb_data = auto_data[5]
	a_high_avg = auto_data[9]
	a_low_avg = auto_data[10]
	a_climb_avg = auto_data[11]


	idx = 0
	if request.method == 'POST':
		for key, val in request.form.items():
			if key == 'team_name':
				team_name = val
				context = {
					'team_name': val
				}

		for i in range(len(final_data)):
			if final_data[i][0] == team_name:
				idx = i

		for i in range(len(high_avg)):
			if high_avg[i][0] == team_name:
				high_idx = i
		
		for i in range(len(low_avg)):
			if low_avg[i][0] == team_name:
				low_idx = i
		
		for i in range(len(final_data)):
			if climb_avg[i][0] == team_name:
				climb_idx = i
		
		for i in range(len(a_high_avg)):
			if a_high_avg[i][0] == team_name:
				a_high_idx = i
		
		for i in range(len(a_low_avg)):
			if a_low_avg[i][0] == team_name:
				a_low_idx = i
		
		# for i in range(len(a_climb_avg)):
		#	  if a_hig_avg[i][0] == team_name:
		#		  a_high_idx = i

		high_avg_pts = high_avg[high_idx][1]
		low_avg_pts = low_avg[low_idx][1]
		climb_avg_pts = climb_avg[climb_idx][1]

		levels = [0, 4, 6, 10, 15]
		proximity = []
		for i in range(len(levels)):
			proximity.append(abs(levels[i] - climb_avg_pts))
		
		print(proximity)

		closest_idx = None
		min_dist = float('inf')
		for i in range(len(proximity)):
			if proximity[i] < min_dist:
				closest_idx = i
				min_dist = proximity[i]
		
		print(closest_idx)

		# prox_hash = {0: 'NONE', 1: 'LOW', 2: 'MID', 3: 'HIGH', 4: 'TRAVERSAL'}

		return render_template('analytics_search.html', final_data=final_data, 
														idx=idx,
														high_goals_data=high_goals_data,
														low_goals_data=low_goals_data,
														climb_data=climb_data,
														high_avg=high_avg_pts,
														low_avg=low_avg_pts,
														climb_avg=climb_avg_pts,
														climb_level=closest_idx,
														team_name=team_name
														)
	
	return render_template('analytics_search.html', final_data=final_data, 
													idx=idx,
													high_goals_data=high_goals_data,
													low_goals_data=low_goals_data,
													climb_data=climb_data)

@app.route('/observing', methods=['GET', 'POST'])
def observation():
	with open('./team_name.txt', 'r') as f:
		name = f.read()

	context = {
		'team_name': name
	}
	
	if request.method == 'POST':
		for key, val in request.form.items():
			if key == "notes":
				notes = val

		with open('./team_name.txt', 'r') as f:
			name = f.read()
		
		now_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')

		data = {
			'time': now_time,
			'team_name': name,
			'high_col': request.json['high_col'],
			'mid_col': request.json['mid_col'],
			'low_col': request.json['low_col'],
			'high_col_auto': request.json['high_col_auto'],
			'mid_col_auto': request.json['mid_col_auto'],
			'low_col_auto': request.json['low_col_auto'],
			'high_pts': request.json['high_pts'],
			'mid_pts': request.json['mid_pts'],
			'low_pts': request.json['low_pts'],
			'match_number': request.json['match_number'],
			'notes': request.json['notes']
		}

		if request.json['side'] == "right":
			temp_h_col = data['high_col']
			temp_l_col = data['low_col']

			data['low_col'] = temp_h_col
			data['high_col'] = temp_l_col



		def sum_arr(arr: list) -> int:
			total = 0
			for i in range(len(arr)):
				total += arr[i]

			return total

		def get_link_pts(arr: list) -> int:
			link_pts = 0

			arr_str = ''.join(arr)
			arr_str = arr_str.split('0')
			for i in range(len(arr_str)):
				subarr = list(arr_str[i])
				subarr = [int(_) for _ in subarr]  
				total = sum_arr(subarr)
				if total > 2:
					multiplier = (total - (total % 3)) / 3
					link_pts += (5 * multiplier)

			return link_pts

		high_link_pts = get_link_pts(data['high_col'])
		mid_link_pts = get_link_pts(data['mid_col'])
		low_link_pts = get_link_pts(data['low_col'])
		high_link_auto_pts = get_link_pts(data['high_col_auto'])
		mid_link_auto_pts = get_link_pts(data['mid_col_auto'])
		low_link_auto_pts = get_link_pts(data['low_col_auto'])

		high_pts = np.sum(np.array(list(map(int, data['high_col']))))
		mid_pts = np.sum(np.array(list(map(int, data['mid_col']))))
		low_pts = np.sum(np.array(list(map(int, data['low_col']))))
		high_auto_pts = np.sum(np.array(list(map(int, data['high_col_auto']))))
		mid_auto_pts = np.sum(np.array(list(map(int, data['mid_col_auto']))))
		low_auto_pts = np.sum(np.array(list(map(int, data['low_col_auto']))))

		print("HIGHIWEPOIWJEPFOIWEJF")
		print(high_pts)

		total_norm_pts = high_pts + high_auto_pts + mid_pts + mid_auto_pts + low_pts + low_auto_pts 
		total_link_pts = high_link_pts + high_link_auto_pts + mid_link_pts + mid_link_auto_pts + low_link_pts + low_link_auto_pts
		total_pts = total_norm_pts + total_link_pts

		csv_data = {
			'time': now_time,
			'team_name': name,
			'high': high_pts * 5,
			'high-auto': high_auto_pts * 6,
			'mid': mid_pts * 3,
			'mid-auto': mid_auto_pts * 4,
			'low': low_pts * 2,
			'low-auto': low_auto_pts * 3,
			'high_link_pts': high_link_pts,
			'mid_link_pts': mid_link_pts,
			'low_link_pts': low_link_pts,
			'high_link_pts_auto': high_link_auto_pts,
			'mid_link_pts_auto': mid_link_auto_pts,
			'low_link_pts_auto': low_link_auto_pts,
			'total_pts': total_pts,
			'engaged': request.json['engaged'],
			'engaged_auto': request.json['engaged_auto'],
			'docked': request.json['docked'],
			'docked_auto': request.json['docked_auto'],
			'match_number': request.json['match_number'],	
			'defense_bot': request.json['defense_bot'],
			'no_move': request.json['no_move'],
			'park': request.json['park'],
			'mobility': request.json['mobility'],
			'notes': request.json['notes']
		}

		data['high_link_pts'] = high_link_pts
		data['mid_link_pts'] = mid_link_pts
		data['low_link_pts'] = low_link_pts
		data['high_link_auto_pts'] = high_link_auto_pts
		data['mid_link_auto_pts'] = mid_link_auto_pts
		data['low_link_auto_pts'] = low_link_auto_pts
		
		csv_data['high_link_pts'] = high_link_pts
		csv_data['mid_link_pts'] = mid_link_pts
		csv_data['low_link_pts'] = low_link_pts
		csv_data['high_link_auto_pts'] = high_link_auto_pts
		csv_data['mid_link_auto_pts'] = mid_link_auto_pts
		csv_data['low_link_auto_pts'] = low_link_auto_pts

		print(request.json)

		# sheets API update calls
		# CHECK MULTIPLIERS FOR AUTO HERE
		# data['high_goal'] # *= 2		  
		# data['auto_high'] # *= 4
		# data['auto_low'] # *= 2

		df = pd.DataFrame([csv_data])
		print(df)

		# df.to_csv(csv_filename, index=False, header=write_header, mode=file_mode)
		df.to_csv(f'./observations/{now_time}.csv')
		print('done')

		return redirect(url_for('home'))
	elif request.method == 'GET':
		return render_template('observing.html', **context) 

if __name__ == '__main__':
	app.run(debug=True)
	# app.run(host='0.0.0.0', port=5000, debug=True)
