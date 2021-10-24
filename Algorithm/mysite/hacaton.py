#!/usr/bin/env python
# coding: utf-8

# In[1]:
import numpy as np
import acopyHacaton
import osm
import skfuzzy as fuzz
import math
import json
import pickle
import copy
from time import time, ctime
import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import aiohttp
import asyncio


bing_api_key = "AggS79ZbDJxZXzWLLakzUU9nntfgU-1WBBjC37_X-Vhk4hpowzAx7Gs4y9Cc8Vyc"

async def get_bing_time(source: tuple, dest: list):
    url = 'https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix'
    params = {
        'key': bing_api_key
    }
    destinations = [ { "latitude": item_dest[0], "longitude": item_dest[1] }  for item_dest in dest]
    json_post = {
        'timeUnit': 'second',
        'distanceUnit': 'kilometer',
        'travelMode': 'driving',
        "origins": [
            {
                "latitude": source[0],
                "longitude": source[1]
            }
        ],
        "destinations": destinations
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params, json=json_post) as resp:
            result  = await resp.json()
            result_return = [0] * len(dest)
            # if len(result['resourceSets']) < 1:
            #     print(result['resourceSets'])
            #     print(json_post)
            for item_result in result['resourceSets'][0]['resources'][0]['results']:
                result_return[item_result['destinationIndex']] = {
                    'duration': item_result['travelDuration'],
                    'distance': item_result['travelDistance'] * 1000
                }
            return result_return

def get_distance_matrix(edges: dict, nodes: dict):
    n = len(edges)
    batch_size = 100
    array_tasks = []
    prom_array = []
    for key, value in edges.items():
        array_coords = []
        array_ids = []
        for key2, value2 in value.items():
            array_coords.append((nodes[key2]['lat'], nodes[key2]['lon']))
            array_ids.append(key2)
        get_bing_time((nodes[key]['lat'], nodes[key]['lon']), array_coords)
        prom_array.append((key, array_ids))
    it = 0
    itog_time = 0
    itog_distance = 0
    while it < n:
        current_it = it
        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        batch_array = array_tasks[it:it+batch_size]
        res = loop.run_until_complete(asyncio.gather(*batch_array))
        for task in res:
            for num, item in enumerate(task):
                edges[prom_array[current_it][0]][prom_array[current_it][1][num]]['time'] = item['duration']
                edges[prom_array[current_it][0]][prom_array[current_it][1][num]]['distance'] = item['distance']
                itog_time += item['duration']
                itog_distance += item['distance']
                # answers.append(item['duration'])
                # mileages.append(item['distance'])
            current_it += 1
        # answers.extend(loop.run_until_complete(asyncio.gather(*batch_array)))
        it += batch_size
    return itog_time, itog_distance 


# In[4]:


# def claster_addresses()
# In[5]:

def calculate_path(addreses_for_algo, edges, nodes, count_kamaz, count_tractor, start_point):
    solver = acopyHacaton.LiteSolver(rho=.011, q=1, iter_without_record=1500)
    colony = acopyHacaton.LiteColony(alpha=1, beta=1.1)
    num_to_id = {}
    id_to_num = {}
    destination_edges = {}
    for num, item in enumerate(addreses_for_algo):
        id_to_num[item['id']] = num
        num_to_id[num] = item['id']
        item['num'] = num
        if item['id'] in edges:
            for key in edges[item['id']]:
                destination_edges.setdefault(item['id'], {}).setdefault(key, 1)
    G = acopyHacaton.LiteGrath(len(addreses_for_algo), dijkstra = {}, destination_edges = destination_edges, start_point = start_point, addreses_for_algo = addreses_for_algo, edges = copy.deepcopy(edges), nodes = nodes, count_kamaz = count_kamaz, count_tractor = count_tractor, num_to_id = num_to_id, id_to_num = id_to_num)
    for item in addreses_for_algo:
        G.add_node(data = item)
    tour = solver.solve(G, colony, gen_size = 1, limit=2)
    return tour

# In[6]:
# @csrf_exempt
def main_function(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        count_kamaz = json_data['kamaz']
        count_tractor = json_data['tractor']
        start_point = {'lat': "52.6175510", 'lon': "39.5284553", 'id': "875930696" }
        minimization_machine = json_data['minimization_machine']
        current_time = json_data['current_time']
        start_time = json_data['start_time']
        finish_time = json_data['finish_time']

        edges, nodes = osm.get_graph()
        array_nodes = list(nodes.values())

        array_coords = [(float(i['lat']), float(i['lon'])) for i in array_nodes]
        num_to_id = {}
        id_to_num = {}
        num = 0
        for key, value in nodes.items():
            id_to_num[key] = num
            num_to_id[num] = key
            num += 1        
        print('Api start')
        with open('Cashe/hacaton.pickle', 'rb') as f:
            obj = pickle.load(f)
        edges = obj['edges']
        nodes = obj['nodes']
        total_time = obj['total_time']
        total_distance = obj['total_distance']
        # total_time, total_distance = get_distance_matrix(edges, nodes)
        # with open('Cashe/hacaton.pickle', 'wb') as f:
        #     pickle.dump({
        #         'edges': edges,
        #         'nodes': nodes,
        #         'total_time': total_time,
        #         'total_distance': total_distance
        #     }, f)
        print('Api finish')
        prom_time_load = start_time.split(':')
        start_time = float(prom_time_load[0]) + float(prom_time_load[1]) / 60
        prom_time_load = finish_time.split(':')
        finish_time = float(prom_time_load[0]) + float(prom_time_load[1]) / 60
        prom_time_load = current_time.split(':')
        current_time = float(prom_time_load[0]) + float(prom_time_load[1]) / 60

        machine_time = max(0, finish_time - max(current_time, start_time))

        if minimization_machine == True:
            ncenters = math.ceil((total_time / 3600) / machine_time) if total_time % (3600 * machine_time) != 0 else math.ceil((total_time / 3600) / machine_time) + 1
        else:
            ncenters = count_kamaz + count_tractor

        ncenters = min(ncenters, count_kamaz + count_tractor)
        
        print('Cluster start')
        cntr, u, u0, d, jm, p, fpc = fuzz.cluster.cmeans(np.array(array_coords).T, ncenters, 2, error=0.0000001, maxiter=10000000)

        cluster_membership = np.argmax(u, axis=0)

        print('Cluster finish')
       

        cars = []
        success = True
        for machine in range(ncenters):
            print("Machine %s" % (str(machine)))
            addreses_for_algo = [start_point]
            for num, cluster in enumerate(cluster_membership):
                if cluster == machine and array_nodes[num]['id'] != start_point['id']:
                    addreses_for_algo.append(array_nodes[num])
                    # addreses_for_algo[-1]['num_total'] = num

            answer_machine = calculate_path(addreses_for_algo, edges, nodes, count_kamaz, count_tractor, start_point)
            if answer_machine.itog == False:
                success = False
            coords = []
            for node in answer_machine.nodes:
                coords.append({
                    'lat': nodes[node]['lat'],
                    'lon': nodes[node]['lon']
                })
                
            cars.append({
                'path': coords,
                'time': answer_machine.cost,
                'distance': answer_machine.total_distance,
            })
        print('Main algo finish')
        if success:
            itog = {
                'cars': cars,
                'current_time': json_data['current_time'],
                'status': 200,
                'snow_removal_is_over': True,
                'error': {} 
            }
        else:
            itog = {
                'cars': cars,
                'current_time': json_data['current_time'],
                'snow_removal_is_over': False,
                'status': 200,
                'error': {} 
            }
        print('Programm finish')
        return True, itog


@csrf_exempt
def main_controller(request):
    try:
        json_data = json.loads(request.body)
        # answerAPI = json_data['answerAPI']
        ans, itog = main_function(request)
        # if answerAPI['auth'] == '123':
        #     ans_req = requests.post(answerAPI['url'], json=itog)
        # else:
        #     ans_req = requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
        # print(ans_req)
        # with open('Answers/main.json', 'w') as outfile:
        #     json.dump(ans_req.text, outfile)
        # print(ans_req.text)
        if ans == True:
            return JsonResponse({ 'status': 200 })
        else:
            return JsonResponse({ 'status': 400 })
    except Exception as e:
        print('Error')
        print(str(e))
        json_data = json.loads(request.body)
        # info_id = json_data['id']
        # info_date = json_data['date']
        # answerAPI = json_data['answerAPI']
        # error = {
        #     "type": 5,
        #     "message": "Server error"
        # }
        # itog = {
        #     'info': {},
        #     'id': info_id,
        #     'date': info_date,
        #     'status': 400,
        #     'error': error
        # }
        # ans = requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
        # print(ans)
        # with open('Answers/main.json', 'w') as outfile:
        #     json.dump(ans.text, outfile)
        # print(ans.text)
        raise
        return JsonResponse({ 'status': 400 })