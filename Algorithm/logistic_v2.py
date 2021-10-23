#!/usr/bin/env python
# coding: utf-8

# In[1]:
import numpy as np
import acopyClean
import math
import json
import pickle
import copy
from time import time, ctime
from class3DpackingProPypy import Packing3D
import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import aiohttp
import asyncio
from itertools import combinations
from genalgo import Chromosome, GenAlgo
import googlemaps

# from pyinstrument import Profiler

working_day = 8 * 60
average_profit = 1000
petrol_minuta = 3
wear_minuta = 1
zp_driver_minuta = 3
average_speed_kmch = 50
# time_loading = 20
# time_unloading = 10
const_weight_time = 4

const_volume = 0.3
time_between_cluster = 12 * 60
time_around_points = 8 * 60 # было 5 * 60

bing_api_key = "AoQplxTPyZQmXqh_KqTSJ2-kpOXs21oGNMzlTDRarZLllT9lclGcbtpqTC3wjCIa"

# In[2]:

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

def get_distance_matrix(array_coords: list, typeAPI: str):
    batch_size = 1000
    n = len(array_coords)
    if typeAPI == 'google':
        batch_size = 100
        array_tasks = [ get_google_time(i, j) for j in array_coords for i in array_coords]
    elif typeAPI == 'bing':
        batch_size = 10
        array_tasks = [ get_bing_time(i, array_coords) for i in array_coords]
    else:
        array_tasks = [ get_sputnic_time(i, j) for j in array_coords for i in array_coords]
    it = 0
    answers = []
    mileages = []
    while it < n*n:
        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        batch_array = array_tasks[it:it+batch_size]
        res = loop.run_until_complete(asyncio.gather(*batch_array))
        for task in res:
            try:
                for item in task:
                    answers.append(item['duration'])
                    mileages.append(item['distance'])
            except:
                answers.append(task['duration'])
                mileages.append(task['distance'])
        # answers.extend(loop.run_until_complete(asyncio.gather(*batch_array)))
        it += batch_size
    return [ answers[i*n:i*n+n] for i in range(n)], [ mileages[i*n:i*n+n] for i in range(n)]





# In[3]:

def read_json(data):
    machines = data['info']['cars']
    machines.sort(key = lambda i: i['length']*i['width']*i['height'],reverse = True)

    for machine in machines:
        prom_time = machine['min_time'].split(':')
        prom_start_time = float(prom_time[0]) + float(prom_time[1]) / 60
        machine['min_time'] = prom_start_time
        prom_time = machine['max_time'].split(':')
        prom_end_time = float(prom_time[0]) + float(prom_time[1]) / 60
        machine['max_time'] = prom_end_time

    prom_addresses = {}

    for address in data['info']['addresses']:
        if len(address['latitude']) < 1 or len(address['longitude']) < 1:
            coords = geocoder(address['address_str'], data['typeAPI'])
            prom_addresses[address['address_id']] = {
                "address_id": address['address_id'],
                "longitude": coords[1],
                "latitude": coords[0],
                "min_time": 0,
                "max_time": 1000,
                "start_time_load": 0,
                "end_time_load": 1000
            }
        else:
            prom_addresses[address['address_id']] = {
                "address_id": address['address_id'],
                "longitude": address['longitude'],
                "latitude": address['latitude'],
                "min_time": 0,
                "max_time": 1000,
                "start_time_load": 0,
                "end_time_load": 1000
            }

    use_addresses = set()
    storages = set()
    addresses = {}
    storage_item_quantity, item_components, address_orders, priority_loads = {}, {}, {}, {}
    load_addresses = {}
    error = {}
    items_time_itog = 0

    for order in data['info']['orders']:
        prom_time = order['start_time'].split(':')
        prom_start_time = float(prom_time[0]) + float(prom_time[1]) / 60   
        prom_time = order['end_time'].split(':')
        prom_end_time = float(prom_time[0]) + float(prom_time[1]) / 60
        prom_items = [] 
        for item in order['items']:
            for load in item['loads']:
                load_addresses.setdefault(load['load_id'], set()).add(order['delivery_id'])
                if load['is_priority'] == True:
                    priority_loads.setdefault(order['order_id'], {}).setdefault(item['item_id'], load['load_id'])
                if item['item_id'] not in storage_item_quantity or load['load_id'] not in storage_item_quantity[item['item_id']]:
                    storage_item_quantity.setdefault(item['item_id'], {}).setdefault(load['load_id'], load['lquantity'])
                if load['load_id'] not in use_addresses:
                    storages.add(load['load_id'])
                    use_addresses.add(load['load_id'])
                prom_time_load = load['start_time_load'].split(':')
                prom_start_time_load = float(prom_time_load[0]) + float(prom_time_load[1]) / 60
                prom_time_load = load['end_time_load'].split(':')
                prom_end_time_load = float(prom_time_load[0]) + float(prom_time_load[1]) / 60

                prom_addresses[load['load_id']]['start_time_load'] = max(prom_addresses[load['load_id']]['start_time_load'], prom_start_time_load)
                prom_addresses[load['load_id']]['end_time_load'] = min(prom_addresses[load['load_id']]['end_time_load'], prom_end_time_load)
                
                if prom_addresses[load['load_id']]['start_time_load'] > prom_addresses[load['load_id']]['end_time_load']:
                    error = {
                        "type": 3,
                        "id": load['load_id'],
                        "message": "Max time load > min time load"
                    }
                    return [], {}, {}, {}, {}, error   
            
            if item['item_id'] not in item_components:
                item_components[item['item_id']] = item['components']
            
            prom_items.append({
                'item_id': item['item_id'],
                'quantity': item['quantity'],
                'time_load': item['item_time_load'],
                'time_unload': item['item_time_unload'],
                'time_lift': item['item_time_lift'],
                'time_assembly': item['item_time_assembly']
            })
            items_time_itog += (item['item_time_load'] + item['item_time_unload'] + item['item_time_lift'] + item['item_time_assembly']) * item['quantity']

        
        if order['delivery_id'] not in use_addresses:
            use_addresses.add(order['delivery_id'])
        
        address_orders.setdefault(order['delivery_id'], []).append({
            'order_id': order['order_id'],
            'items': prom_items 
        })

        prom_addresses[order['delivery_id']]['min_time'] = max(prom_addresses[order['delivery_id']]['min_time'], prom_start_time)
        prom_addresses[order['delivery_id']]['max_time'] = min(prom_addresses[order['delivery_id']]['max_time'], prom_end_time)
        
        if prom_addresses[order['delivery_id']]['min_time'] > prom_addresses[order['delivery_id']]['max_time']:
            error = {
                "type": 1,
                "id": order['delivery_id'],
                "message": "Max time > min time"
            }
            return [], {}, {}, {}, {}, error
    # апельсин сделать проверку нужного товара и на складах                                                        
    
    if 'start' in data:
        start_address = prom_addresses[data['start']]
        use_addresses.add(data['start'])
    else:
        start_address = None
    
    if 'finish' in data:
        finish_address = prom_addresses[data['finish']]
        use_addresses.add(data['finish'])
    else:
        finish_address = start_address
    
    for address in use_addresses:
        addresses[address] = prom_addresses[address]
    return machines, addresses, storage_item_quantity, item_components, address_orders, storages, start_address, finish_address, load_addresses, priority_loads, items_time_itog, error

# In[4]:


# def claster_addresses()
# In[5]:

def calculate_path(machine, array_addresses, distance_matrix, storage_item_quantity, item_components, address_orders, storages, start, finish, load_addresses, priority_loads, minimization_of_customer_time):
    solver = acopyClean.Solver(rho=.011, q=1, iter_without_record=1500)
    colony = acopyClean.Colony(alpha=1, beta=1.1)
    num_storage = set()
    num_destination = set()
    roles = {}
    if start:
        roles[start['address_id']] = copy.deepcopy(start)
        roles[start['address_id']]['is_start'] = True
        if finish['address_id'] not in roles:
            roles[finish['address_id']] = copy.deepcopy(finish)
        roles[finish['address_id']]['is_finish'] = True
    for i in storages:
        if i['address_id'] not in roles:
            roles[i['address_id']] = copy.deepcopy(i)
        roles[i['address_id']]['is_store'] = True
        roles[i['address_id']]['is_destination'] = False
    for i in array_addresses:
        if i['address_id'] not in roles:
            roles[i['address_id']] = copy.deepcopy(i)
        roles[i['address_id']]['is_destination'] = True
        if 'is_store' not in roles[i['address_id']]:
            roles[i['address_id']]['is_store'] = False
    data = list(roles.values())

    new_distance_matrix =[[distance_matrix[data[i]['num']][data[j]['num']] for j in range(len(data))] for i in range(len(data))]
    id_to_num = {}
    newStart = None
    newFinish = None
    for newnum, i in enumerate(data):
        i['num'] = newnum
        id_to_num[i['address_id']] = newnum
        if 'is_start' in i and i['is_start']:
            newStart = i
        if 'is_finish' in i and i['is_finish']:
            newFinish = i
        if 'is_store' in i and i['is_store']:
            num_storage.add(newnum)
        if 'is_destination' in i and i['is_destination']:
            num_destination.add(newnum)
    
    time_start = machine['min_time']
    time_finish = machine['max_time']

    count_storage = len(num_storage)
    count_destination = len(num_destination)
    G = acopyClean.LiteGrath(len(data), id_to_num = id_to_num, priority_loads = priority_loads, load_addresses = load_addresses, cashe_path = {}, num_storage = num_storage, num_destination = num_destination, destination = count_destination, machine = machine, start = newStart, finish = newFinish, item_components = item_components, storage = count_storage, address_orders = address_orders, storage_component = storage_item_quantity, time_s = float(time_start), time_f = float(time_finish), minimization_of_customer_time = minimization_of_customer_time)
    for item in data:
        G.add_node(data = item)
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j:
                G.add_edge(i,j, weight=new_distance_matrix[i][j])
    tour = solver.solve(G, colony, gen_size = 7, limit=5000)
    # with open('Cashe/'+ctime().replace(':', ' ')+'_cashe.pickle', 'wb') as f:
    #     pickle.dump(G.args['cashe_path'], f)
    return tour

# апельсин: заглушка
def validate_input_data(data):
    new_json = copy.deepcopy(data)
    if 'minimization_of_customer_time' not in new_json:
        new_json['minimization_of_customer_time'] = 0
    for i_order in new_json['info']['orders']:
        for i_items in i_order['items']:
            if 'item_time_assembly' not in i_items:
                i_items['item_time_assembly'] = 0
    return new_json

def remake_finished_route(json_cars, address_index, mileage_matrix):
    new_json = copy.deepcopy(json_cars)
    for car in new_json:
        itog_mileage = 0
        for index_address in range(len(car['addresses']) - 1):
            itog_mileage += mileage_matrix[address_index[car['addresses'][index_address]['address_id']]][address_index[car['addresses'][index_address + 1]['address_id']]]
        car['mileage'] = itog_mileage / 1000
        newAddresses = [address for address in car['addresses'] if len(address['load']) + len(address['unload']) > 0]
        car['addresses'] = newAddresses
    return new_json

# In[6]:
# @csrf_exempt
def main_function(request):
    if request.method == 'POST':
        # profiler = Profiler()
        # profiler.start()
        print('Detected POST "/api/logistic"')
        json_data = validate_input_data(json.loads(request.body))
        with open('Jsons/'+ctime().replace(':', ' ')+'.json', 'w') as outfile:
            json.dump(json_data, outfile)
        info_id = json_data['id']
        info_date = json_data['date']
        uniformLoading = json_data['uniformLoading']
        minimization_of_customer_time = json_data['minimization_of_customer_time']
        typeAPI = json_data['typeAPI']
        answerAPI = json_data['answerAPI']

        machines, addresses, storage_item_quantity, item_components, address_orders, storages, start_address, finish_address, load_addresses, priority_loads, items_time_itog, error = read_json(json_data)
        
        if error:
            itog = {
                'info': {},
                'id': info_id,
                'date': info_date,
                'status': 400,
                'error': error 
            }
            print(error)
            with open('Answers/'+ctime().replace(':', ' ')+'.json', 'w') as outfile:
                json.dump(itog, outfile)
            # requests.post('http://31.44.248.254:8082/demologist/hs/Logistics/dataready', json=itog)
            # requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
            return False, itog
        
        print('Data true')
        array_addresses = list(addresses.values())
        address_index = {}
        for num, i in enumerate(array_addresses):
            address_index[i['address_id']] = num
        storage_index = set()
        for i in storages:
            storage_index.add(address_index[i])
        array_coords = [(i['latitude'], i['longitude']) for i in array_addresses]
        start_time = time()
        # with open('Cashe/distance_matrix_200.pickle', 'rb') as f:
        #     distance_matrix = pickle.load(f)
        
        distance_matrix, mileage_matrix = get_distance_matrix(array_coords, typeAPI)
        
        with open('Cashe/distance_matrix_200.pickle', 'wb') as f:
            pickle.dump(distance_matrix, f)
        print('API done')
        print("--- %s seconds ---" % (time() - start_time))

        # Составление матрицы: какие машины могут поехать в каждый адрес
        start_time = time()
        
        address_machines = []
        address_boxes = {}
        address_boxes_array = []
        address_params = []
        
        for address in array_addresses:
            boxes = []
            count_orders = 0
            time_orders = 0
            volume_orders = 0
            if address['address_id'] in address_orders:
                for order in address_orders[address['address_id']]:
                    count_orders += 1
                    for item in order['items']:
                        time_orders += (item['time_load'] + item['time_unload'] + item['time_lift'] + item['time_assembly']) * item['quantity']
                        # boxes.extend(item_components[item['item_id']]) апельсин : в идеале должно быть так
                        for component in item_components[item['item_id']]:
                            for _ in range(item['quantity'] * component['c_quantity']):
                                volume_orders += int(math.ceil(float(component['height'])/100)) * int(math.ceil(float(component['width'])/100)) * int(math.ceil(float(component['length'])/100))
                                boxes.append(tuple([int(math.ceil(float(component['height'])/100)),int(math.ceil(float(component['width'])/100)),int(math.ceil(float(component['length'])/100)),int(math.ceil(float(component['weight']))),int(component['top_allow']),int(component['brinks'])]))
            boxes.sort(key = lambda i: i[0]*i[1]*i[2],reverse = True)
            prom_machine = []
            for machine in machines:
                container = [[[0 for _ in range(int(float(machine['height'])*10))] for __ in range(int(float(machine['width'])*10))] for ___ in range(int(float(machine['length'])*10))]
                packing = Packing3D(container, int(machine['carry_capacity']))
                ans_time = True
                ans_packing = packing.make_packaging(boxes)
                if address['max_time'] < machine['min_time'] or machine['max_time'] < address['min_time']:
                    ans_time = False
                if len(boxes) == 0:
                    ans_time = True
                prom_machine.append(ans_time and ans_packing)
            address_boxes[address['address_id']] = boxes
            address_boxes_array.append(boxes)
            address_params.append({
                "count_orders": count_orders,
                "time": time_orders,
                "volume": volume_orders
            })
            if sum(prom_machine) == 0:
                error = {
                    "type": 2,
                    "id": address['address_id'],
                    "message": "The address is not suitable in time and load"
                }
                itog = {
                    'info': {},
                    'id': info_id,
                    'date': info_date,
                    'status': 400,
                    'error': error
                }
                print(error)
                with open('Answers/'+ctime().replace(':', ' ')+'.json', 'w') as outfile:
                    json.dump(itog, outfile)
                # requests.post('http://31.44.248.254:8082/demologist/hs/Logistics/dataready', json=itog)
                # requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
                return False, itog
            else:
                address_machines.append(prom_machine)

        print('Test packing and time all address finish')
        print("--- %s seconds ---" % (time() - start_time))

        # Проверка можно ли теоритически развести столько заказов всеми машинами
        start_time = time()

        min_need_time = items_time_itog / 60
        solver = acopyClean.LiteSolver(rho=.01, q=1, iter_without_record=100000)
        colony = acopyClean.LiteColony(alpha=1, beta=1.1)
        array_indexes_with_boxes = []
        for i in range(len(array_addresses)):
            if len(address_boxes_array[i]) > 0:
                array_indexes_with_boxes.append(i)
        G = acopyClean.LiteGrath(len(array_indexes_with_boxes))
        for item in array_indexes_with_boxes:
            G.add_node(data = item)
        for numi, i in enumerate(array_indexes_with_boxes):
            for numj, j in enumerate(array_indexes_with_boxes):
                if i != j:
                    G.add_edge(numi,numj, weight=distance_matrix[i][j])
        tour = solver.solve(G, colony, gen_size = 3, limit=1000)
        min_need_time += tour.cost / 3600
        print('Calculate min_need_time finish')
        print("--- %s seconds ---" % (time() - start_time))

        # Основной алгоритм
        number_cars = len(machines)
        for num_machine in range(1, number_cars + 1):
            print('Num machines')
            print(num_machine)
            if uniformLoading == 1 and num_machine != number_cars:
                continue
            result_early_machines = []
            for current_machines in combinations(range(number_cars), num_machine):
                cars_time = 0
                cars_volume = 0
                for i in current_machines:
                    cars_time += machines[i]['max_time'] - machines[i]['min_time']
                    cars_volume += machines[i]['length'] * machines[i]['width'] * machines[i]['height']
                
                is_Continue = False
                for i in result_early_machines:
                    if cars_time <= i['time'] and cars_volume <= i['volume']:
                        is_Continue = True
                        break

                result_early_machines.append({
                    'time': cars_time,
                    'volume': cars_volume
                })

                if is_Continue == True:
                    continue

                if cars_time < min_need_time:
                    continue
                
                # Проверка подойдут ли определенные машины.  апельсин : сумма всех сочетаний 2 в степени n, поэтому более менее будет работать 25 машин нормально. Значит надо переделать алгоритм перебова всех машин и проверки их.
                start_time = time()

                isCheckMachines = True
                for address in address_machines:
                    isCheckAddress = False
                    for machine in current_machines:
                        if address[machine] == True:
                            isCheckAddress = True
                            break
                    if isCheckAddress == False:
                        isCheckMachines = False
                        break

                # print('Check machine finish')
                # print("--- %s seconds ---" % (time() - start_time))

                if isCheckMachines == False:
                    continue
                
                start_time = time()

                array_current_machines = [machines[machine] for machine in current_machines]
                address_machines_genalgo = []
                for num, address in enumerate(address_machines):
                    prom_address_machines_genalgo = []
                    for machine in current_machines:
                        prom_address_machines_genalgo.append(address[machine])
                    address_machines_genalgo.append(prom_address_machines_genalgo)

                prototype = Chromosome(1, 1, 40, 80, None, None, distance_matrix, address_params, array_current_machines, address_machines_genalgo)
                ans = GenAlgo(32,24,8, prototype)
                ans.start()

                # testar = []
                # colors = ['r', 'g', 'b', 'c', 'm', 'y']
                # for test in range(len(array_addresses)):
                #     testar.append(([array_addresses[test]['longitude']], [array_addresses[test]['latitude']], colors[ans.getBestChromosome().permutation[test]]))
                
                # with open('Cashe/'+ctime().replace(':', ' ')+'_test.pickle', 'wb') as f:
                #     pickle.dump(testar, f)

                print(ans.getBestChromosome().cluster_time)
                print(ans.getBestChromosome().cluster_volume)
                sum_volume_machines = sum(machines[i]['length']*machines[i]['width']*machines[i]['height'] for i in current_machines)
                prom_percent_volume_machines = [machines[i]['length']*machines[i]['width']*machines[i]['height'] / sum_volume_machines for i in current_machines]
                print('Volume')
                print(prom_percent_volume_machines)
                print('Itog')
                print(ans.getBestChromosome().itog)
                print(ans.getBestChromosome().fitness)

                print('Cluster finish')
                print("--- %s seconds ---" % (time() - start_time))

                if ans.getBestChromosome().itog == False:
                    continue

                print('Current machines')
                print(current_machines)

                cluster_membership = ans.getBestChromosome().permutation
                

                start_time = time()
                cars = []
                success = True
                storage_item_quantity_copy = copy.deepcopy(storage_item_quantity)
                for machine in range(num_machine):
                    print("Machine %s" % (str(machine)))
                    print("CurrentMachine %s" % (str(current_machines[machine])))
                    addreses_for_algo = []
                    for num, cluster in enumerate(cluster_membership):
                        if cluster == machine and len(address_boxes_array[num]) > 0:
                            addreses_for_algo.append(array_addresses[num])
                            addreses_for_algo[-1]['num'] = num
                    machine_for_algo = machines[current_machines[machine]]
                    print(machine_for_algo['max_time'])
                    print('Count addresses')
                    print(len(addreses_for_algo))
                    storages_for_algo = []

                    for storage in storage_index:
                        storages_for_algo.append(array_addresses[storage])
                        storages_for_algo[-1]['num'] = storage

                    if start_address:
                        start_address['num'] = address_index[start_address['address_id']]
                        finish_address['num'] = address_index[finish_address['address_id']]

                    answer_machine = calculate_path(machine_for_algo, addreses_for_algo, distance_matrix, storage_item_quantity_copy, item_components, address_orders, storages_for_algo, start_address, finish_address, load_addresses, priority_loads, minimization_of_customer_time)
                    storage_item_quantity_copy = copy.deepcopy(answer_machine.storage)
                    if answer_machine.itog:
                        cars.append({
                            'car_id': machine_for_algo['car_id'],
                            'addresses': answer_machine.json_ans
                        })
                    else:
                        success = False
                        break
                print('Main algo finish')
                print("--- %s seconds ---" % (time() - start_time))
                if success:
                    itog = {
                        'info': {
                            'cars': remake_finished_route(cars, address_index, mileage_matrix)
                        },
                        'id': info_id,
                        'date': info_date,
                        'status': 200,
                        'error': {} 
                    }
                    with open('Answers/'+ctime().replace(':', ' ')+'.json', 'w') as outfile:
                        json.dump(itog, outfile)
                    # profiler.stop()
                    # profiler.open_in_browser()

                    # requests.post('http://31.44.248.254:8082/demologist/hs/Logistics/dataready', json=itog)
                    # ans = requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
                    # print(ans)
                    # with open('Answers/main.json', 'w') as outfile:
                    #     json.dump(ans.text, outfile)
                    # print(ans.text)
                    print('Programm finish')
                    return True, itog
                else:
                    continue
        error = {
            "type": 4,
            "message": "Load not finished"
        }
        itog = {
            'info': {},
            'id': info_id,
            'date': info_date,
            'status': 400,
            'error': error
        }
        print(error)
        with open('Answers/'+ctime().replace(':', ' ')+'.json', 'w') as outfile:
            json.dump(itog, outfile)
        # requests.post('http://31.44.248.254:8082/demologist/hs/Logistics/dataready', json=itog)
        # ans = requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
        # print(ans)
        # with open('Answers/main.json', 'w') as outfile:
        #     json.dump(ans.text, outfile)
        # print(ans.text)
        return False, itog


@csrf_exempt
def main_controller(request):
    try:
        json_data = json.loads(request.body)
        answerAPI = json_data['answerAPI']
        ans, itog = main_function(request)
        if answerAPI['auth'] == '123':
            ans_req = requests.post(answerAPI['url'], json=itog)
        else:
            ans_req = requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
        print(ans_req)
        with open('Answers/main.json', 'w') as outfile:
            json.dump(ans_req.text, outfile)
        print(ans_req.text)
        if ans == True:
            return JsonResponse({ 'status': 200 })
        else:
            return JsonResponse({ 'status': 400 })
    except Exception as e:
        print('Error')
        print(str(e))
        json_data = json.loads(request.body)
        info_id = json_data['id']
        info_date = json_data['date']
        answerAPI = json_data['answerAPI']
        error = {
            "type": 5,
            "message": "Server error"
        }
        itog = {
            'info': {},
            'id': info_id,
            'date': info_date,
            'status': 400,
            'error': error
        }
        ans = requests.post(answerAPI['url'], headers={"Authorization":answerAPI['auth']}, json=itog)
        print(ans)
        with open('Answers/main.json', 'w') as outfile:
            json.dump(ans.text, outfile)
        print(ans.text)
        raise
        return JsonResponse({ 'status': 400 })

@csrf_exempt
def main_controller_for_diplom(request):
    try:
        json_data = json.loads(request.body)
        ans, itog = main_function(request)
        with open('AnswersDiplom/main.json', 'w') as outfile:
            json.dump(itog, outfile)
        return JsonResponse(itog)
    except Exception as e:
        print('Error')
        print(str(e))
        json_data = json.loads(request.body)
        info_id = json_data['id']
        info_date = json_data['date']
        error = {
            "type": 5,
            "message": "Server error"
        }
        itog = {
            'info': {},
            'id': info_id,
            'date': info_date,
            'status': 400,
            'error': error
        }
        with open('AnswersDiplom/main.json', 'w') as outfile:
            json.dump(itog, outfile)
        raise
        return JsonResponse(itog)