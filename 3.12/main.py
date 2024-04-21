import parsingAgain
import timeCalculator
import json
import sys
import simpy
import numpy as np
from collections import deque
from datetime import datetime, timedelta
from datetime import time as dt_time


#to remove, credo
import random
import time

#sys.setrecursionlimit(100000)



diagbpPath="../json/diagbp.json"
bpmnPath="../json/bpmn.json"

parsingAgain.parse_again()

try:
    with open(bpmnPath, "r") as file:
        bpmn = json.load(file)
except FileNotFoundError:
    print(f"-----ERROR-----: bpmn file not found")
    sys.exit()
except json.JSONDecodeError:
    print(f"-----ERROR-----: bpmn file bad syntax")
    sys.exit()
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit()

try:
    with open(diagbpPath, "r") as file:
        diagbp = json.load(file) #Simulations parameters
except FileNotFoundError:
    print(f"-----ERROR-----: simulation parameters not found")
    sys.exit()
except json.JSONDecodeError:
    print(f"-----ERROR-----: simulation parameters bad syntax")
    sys.exit()
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit()




num_instances = sum(int(instance['count']) for instance in diagbp['processInstances'])
print("NUM_INSTANCES: "+ str(num_instances))
instance_types = diagbp['processInstances']
xor_probabilities = {flow['elementId']: float(flow['executionProbability']) for flow in diagbp['sequenceFlows']}
resources = diagbp['resources']
timetables = diagbp['timetables']

# Generate the delays
delay_between_instances = diagbp['arrivalRateDistribution'] #array contains: type, mean, arg1, arg2
delays = [0]
total_delay = 0
for _ in range(num_instances-1):
    delay = timeCalculator.convert_to_seconds(delay_between_instances)
    total_delay += delay #each delay is therefore equal to itself + the previous delay
    delays.append(total_delay)

task_durations = {element['elementId']: element['durationDistribution'] for element in diagbp['elements']} #dict contains: type, mean, arg1, arg2
task_resources = {element['elementId']: element['resourceIds'] for element in diagbp['elements']} #array contains dicts with each: resourceName, amountNeeded, groupId

class Process:
    executed_nodes = {}  # make executed_nodes a dictionary of sets
    startDateTime = diagbp['startDateTime']
    def __init__(self, env, name, process_details, num, globalResources, start_delay=0, instance_type="default"):
        self.env = env
        self.name = name
        self.process_details = process_details
        self.stack=[]
        self.start_delay = start_delay
        self.instance_type = instance_type
        self.num = num
        self.action = env.process(self.run())
        #resources is a dict with name as key and a tuple made of simpy resource, cost and timetable.
        self.resources = globalResources
        Process.executed_nodes[self.num] = set() 
        for resource_name, resource_info in self.resources.items():
            resource, cost_per_hour, timetable_name = resource_info
            print(f"Resource Name: {resource_name}, Capacity: {resource.capacity}")
    
    def is_in_timetable(self, timetable_name):
        start_time = Process.startDateTime
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        current_time = start_time + timedelta(seconds=self.env.now)
        # Get the timetable from the global timetables variable
        timetable = next(t for t in timetables if t['name'] == timetable_name)

        # Extract the current time's hour and minute
        current_hour_minute_second = dt_time(current_time.hour, current_time.minute, current_time.second)
        
        #print("start:"+str(Process.startDateTime))
        #print("converted:"+str(start_time))
        #print("now:"+str(current_time))
        # Check if the current time falls within any of the rules in the timetable
        for rule in timetable['rules']:
            timeFlag=False
            from_hour, from_minute, from_second = map(int, rule['fromTime'].split(':'))
            to_hour, to_minute, to_second = map(int, rule['toTime'].split(':'))

            from_time = dt_time(from_hour, from_minute, from_second)
            to_time = dt_time(to_hour, to_minute, to_second)
            from_day = rule['fromWeekDay'].upper()
            to_day = rule['toWeekDay'].upper()
            print(str(from_time)+"|"+str(current_hour_minute_second)+"|"+str(to_time)+"|days:|"+str(from_day)+"|"+str(current_time.strftime('%A').upper())+"|"+str(to_day))

            # Checks for both ways, from time bigger or lower than to time
            if from_time > to_time: #ie: 22:00:00 to 04:00:00
                if not (to_time >= current_hour_minute_second or current_hour_minute_second >= from_time):
                    continue  # Skip this rule, as current time is outside the range
                # This variable is true only if current hour minute is less than midnight
                # This is to avoid a case where shift is 22 to 04 and friday to sunday (morning) and sunday 23:00 would be considered ok (which is not), while sunday 01:00 is ok
                timeFlag=True  
            elif not from_time <= current_hour_minute_second <= to_time:
                continue  # Skip this rule, as current time is outside the range

            # Check if current day is within the rule's day range

            days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']

            # Checks for both ways as before for time
            if (days.index(to_day) < days.index(from_day)) and timeFlag:
                if not (days.index(to_day) > days.index(current_time.strftime('%A').upper()) or days.index(current_time.strftime('%A').upper()) >= days.index(from_day)):
                    continue # Skip this rule, as current day is outside the range
            elif days.index(to_day) < days.index(from_day) and not timeFlag:
                if not (days.index(to_day) >= days.index(current_time.strftime('%A').upper()) or days.index(current_time.strftime('%A').upper()) >= days.index(from_day)):
                    continue  # Skip this rule, as current day is outside the range
            elif (not (days.index(from_day) <= days.index(current_time.strftime('%A').upper()) < days.index(to_day))) and timeFlag:
                continue  # Skip this rule, as current day is outside the range
            elif (not (days.index(from_day) <= days.index(current_time.strftime('%A').upper()) <= days.index(to_day))) and not timeFlag:
                continue  # Skip this rule, as current day is outside the range


            return True

        return False

    def printState(self, node, node_id, inSubProcess):
        if node['type'] == 'subProcess':
            print(f"#{self.num}|{self.name}: {node_id} (subprocess {node['name']} just started), instance_type:{self.instance_type}. time: {self.env.now}.")
        elif inSubProcess == True:
            print(f"#{self.num}|{self.name} (inside subprocess): {node_id} ({node['name']}), type: {node['type']}, instance_type:{self.instance_type}. time: {self.env.now}.")
        else:
            print(f"#{self.num}|{self.name}: {node_id} ({node['name']}), type: {node['type']}, instance_type:{self.instance_type}. time: {self.env.now}.")

    def run(self):
        yield self.env.timeout(self.start_delay) #delay start because of arrival rate.
        start_node_id = next((node_id for node_id, node in self.process_details['node_details'].items() if node['type'] == 'startEvent'), None)
        if start_node_id is None:
            return
        yield from self.run_node(start_node_id)


    def run_node(self, node_id, subprocess_node=None):
        if subprocess_node is None:
            node = self.process_details['node_details'][node_id]
            printFlag=False
        else:
            node = self.process_details['node_details'][subprocess_node]['subprocess_details'][node_id]
            printFlag=True

        if node['type'] == 'startEvent':
            next_node_id = node['next'][0]
            if len(node['previous'])>0:
                while not all(prev_node in Process.executed_nodes[self.num] for prev_node in node['previous']):
                    yield self.env.timeout(1)
            self.printState(node,node_id,printFlag)
            yield from self.run_node(next_node_id, subprocess_node)


        elif node['type'] == 'task':
            if len(node['previous'])>0:
                while not all(prev_node in Process.executed_nodes[self.num] for prev_node in node['previous']):
                    yield self.env.timeout(1)
            taskTime=timeCalculator.convert_to_seconds(task_durations[node_id]) # task duration is used here, it is passed before to a converter that transforms the type/mean/arg1/arg2 to a value in seconds, this value the task duration is always different in each instance
            
            #resources zone
            taskNeededResources=task_resources[node_id]
            if taskNeededResources: #if the task needs resources
                grouped_resources = {}
                for res in taskNeededResources:
                    if res['groupId'] not in grouped_resources:
                        grouped_resources[res['groupId']] = []
                    grouped_resources[res['groupId']].append((res['resourceName'], int(res['amountNeeded'])))
                
                # Check each group of resources
                while True:
                    resources_allocated = False
                    i=0
                    for group_id, resources in grouped_resources.items():              
                        i+=1      
                        # Check if there are enough resources to fulfill the request of a group
                        requests = []
                        for resource, amount in resources:
                            #capacity indica capacità della risorsa, count quante ne ho allocate. Inoltre controlla se la risorsa è in timetable
                            if not self.is_in_timetable(self.resources[resource][2]) or self.resources[resource][0].capacity-self.resources[resource][0].count < amount:
                                if not self.is_in_timetable(self.resources[resource][2]):
                                    print(node_id + "|group n."+str(i)+"| TIMETABLE-BREAK | "+resource+": "+str(self.resources[resource][0].count)+"/"+str(self.resources[resource][0].capacity)+" amount: "+str(amount))
                                else:
                                    print(node_id + "|group n."+str(i)+"| BREAK | "+resource+": "+str(self.resources[resource][0].count)+"/"+str(self.resources[resource][0].capacity)+" amount: "+str(amount))
                                for req in requests:
                                    req.resource.release(req)
                                    req.cancel() # cancel the requests that were accumulated till now since this group is ko
                                break  # If not enough resources, break and check the next group
                            else:
                                for _ in range(amount):
                                    req = self.resources[resource][0].request()  # If enough resources, request resources
                                    print(node_id + "|group n."+str(i)+"|"+resource+": "+str(self.resources[resource][0].count)+"/"+str(self.resources[resource][0].capacity)+" total amount needed: "+str(amount))
                                    requests.append(req)
                        total_resources_needed = sum(amount for _, amount in resources)
                        if len(requests) == total_resources_needed:  # If all resources in the group can be allocated
                            resources_allocated = True
                            for req in requests:
                                yield req
                                print (node_id + "|Resource locked: " + str(req.resource) + ", Time: " + str(self.env.now) )  # Print + str(req.amount)
                            break  # Break the loop as resources are allocated
                    if not resources_allocated:
                        yield self.env.timeout(1)  # If no group can be allocated, wait for a timeout(1)
                    else:
                        break  # Break the while true as resources are allocated

            yield self.env.timeout(taskTime) 
            Process.executed_nodes[self.num].add(node_id)
            self.printState(node,node_id,printFlag)
            next_node_id = node['next'][0]
            
            # Release resources
            for req in requests:
                req.resource.release(req)
                print(node_id + "|Resource released: " + str(req.resource)  + ", Time: " + str(self.env.now))

            yield from self.run_node(next_node_id, subprocess_node)


        elif node['type'] == 'exclusiveGateway':
            # Get the flows from bpmn.json that start from the current XOR
            flows_from_xor = [(flow_id, flow) for flow_id, flow in bpmn['sequence_flows'].items() if flow['sourceRef'] == node_id]
            # Create a dictionary mapping target nodes to their probabilities
            node_probabilities = {}
            forced_flow_target = None
            for flow_id, flow in flows_from_xor:
                # Find the corresponding flow in diagbp.json
                diagbp_flow = next((item for item in diagbp['sequenceFlows'] if item['elementId'] == flow_id), None)
                if diagbp_flow is not None:
                    node_probabilities[flow['targetRef']] = float(diagbp_flow['executionProbability'])
                    # Check if 'types' field exists and if it matches with self.instance_type (to force the current instance into his xor based on the instance type)
                    if 'types' in diagbp_flow:
                        for type_dict in diagbp_flow['types']:
                            if type_dict['type'] == self.instance_type:
                                forced_flow_target = flow['targetRef']
                                break
                if forced_flow_target is not None:
                    break
            # Check if node_probabilities is empty, if yes then the xor has only one next elem.
            if not node_probabilities:
                next_node_id = node['next'][0]
            elif forced_flow_target is not None:
                next_node_id = forced_flow_target
            else:
                next_node_id = np.random.choice(list(node_probabilities.keys()), p=list(node_probabilities.values()))
            self.printState(node,node_id,printFlag)
            yield from self.run_node(next_node_id, subprocess_node)


        elif node['type'] == 'parallelGateway':
            # AND logic: run all paths concurrently and wait for all to finish, process is created for each path to ensure parallelism
            events = []
            for next_node_id in node['next']:
                process = self.env.process(self.run_node(next_node_id, subprocess_node))
                events.append(process)
            self.printState(node,node_id,printFlag)
            yield self.env.all_of(events)
            # When all_of is done, proceed with the node after the close
            next_node_after_parallel = self.stack.pop()
            # print for parallel close
            if not printFlag:
                print(f"#{self.num}|{self.name}: Parallel gateway closed. instance_type:{self.instance_type}. time: {self.env.now}.")
            else:
                print(f"#{self.num}|{self.name}| (inside subprocess): Parallel gateway closed. instance_type:{self.instance_type}. time: {self.env.now}.")
            yield from self.run_node(next_node_after_parallel, subprocess_node)

        elif node['type'] == 'parallelGateway_close':
            self.stack.append(node['next'][0])
            return
            
        elif node['type'] == 'subProcess':
            if len(node['previous'])>0:
                while not all(prev_node in Process.executed_nodes[self.num] for prev_node in node['previous']):
                    yield self.env.timeout(1)
            start_node_id = next(sub_node_id for sub_node_id, sub_node in node['subprocess_details'].items() if sub_node['type'] == 'startEvent')
            self.printState(node,node_id,printFlag)
            yield from self.run_node(start_node_id, node_id)
            Process.executed_nodes[self.num].add(node_id)
            next_node_id = node['next'][0]
            # After the subprocess is executed, continue with the node next to the subprocess
            yield from self.run_node(next_node_id, None)
        elif node['type'] == 'intermediateThrowEvent':
            next_node_id = node['next'][0]
            Process.executed_nodes[self.num].add(node_id)
            self.printState(node,node_id,printFlag)
            yield from self.run_node(next_node_id, subprocess_node)
            return
        elif node['type'] == 'intermediateCatchEvent':
            if node['subtype'] == 'messageEventDefinition':
                next_node_id = node['next'][0]
                if len(node['previous'])>0: #wait for msg
                    while not all(prev_node in Process.executed_nodes[self.num] for prev_node in node['previous']):
                        yield self.env.timeout(1)
                Process.executed_nodes[self.num].add(node_id)
                self.printState(node,node_id,printFlag)
                yield from self.run_node(next_node_id, subprocess_node)
                return
            else:
                next_node_id = node['next'][0]
                Process.executed_nodes[self.num].add(node_id)
                self.printState(node,node_id,printFlag)
                yield self.env.timeout(1) #TODO: CAMBIARE 1 IN DURATA DA PRENDERE DA PARAM DEL TIMER
                yield from self.run_node(next_node_id, subprocess_node)
                return

        elif node['type'] == 'endEvent':
            self.printState(node,node_id,printFlag)
            return


def simulate_bpmn(bpmn_dict):
    instance_index = 0
    instance_count = 0

    env = simpy.Environment()
    global_resources = {res['name']: (simpy.Resource(env, capacity=int(res['totalAmount'])), res['costPerHour'], res['timetableName']) for res in resources} if resources else {}
    for i in range(num_instances):
        instance_type = instance_types[instance_index]['type']

        for participant_id, participant in bpmn_dict['collaboration']['participants'].items():
            process_details = bpmn_dict['process_elements'][participant['processRef']]
            # for each instance a class Process is created:
            Process(env, participant['name'], process_details,i+1, global_resources, delays[i], instance_type)

        instance_count += 1
        if instance_count >= int(instance_types[instance_index]['count']):
            instance_index += 1
            instance_count = 0
    env.run()


simulate_bpmn(bpmn)

