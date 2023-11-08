# pip install stable-baselines3[extra]
# Python version 3.9.18
import gym 
import copy
from gymnasium import Env
from gymnasium.spaces import Discrete, Box, Dict, Tuple, MultiBinary, MultiDiscrete 
import numpy as np
import random
import os
import time
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from dataclasses import dataclass
import matplotlib.pyplot as plt

# Bank, 1 clerk.py
import salabim as sim
#-------------------------------------------------------------------------------------------
action_Cust = 5

#Struct that holds the information regarding a truck
@dataclass
class Truck:
    Battery:        np.int16
    Arrival_Time:   np.int16
    total_time:     np.int16

#-------------------------------------------------------------------------------------------
#Class that prepares a car arrival set
class Prepare():
    def __init__(self):
        #Create an empty list where we can store the truck scedual
        self.trucks = []
        random.seed(time.time())

    def prepare_data(self):
        self.trucks = []
        time = 0
        #Loop until a day is finished
        while time <1400:                      
            #Create a new data object
            Truck_Data = Truck(Battery= sim.Uniform(20, 80).sample(),Arrival_Time=time,total_time=0)  
            #Append the data to the list
            self.trucks.append(Truck_Data)   
            #Determine the new arrival time
            time += sim.Uniform(10, 40).sample()
#-------------------------------------------------------------------------------------------
class CustomerGenerator(sim.Component):
    def __init__(self,waiting_room,env,clerks,wait_times,shedual):
        super().__init__()
        self.waiting_room = waiting_room
        self.env = env
        self.clerks = clerks
        self.debug = False
        self.wait_times = wait_times
        self.shedual = shedual

    def process(self):
        previous_arrival = 0
        while True:            
            #Check if there ia an truck left in the list
            if len(self.shedual) > 0:
                #Get the next truck out of the list
                truck = self.shedual.pop(0)
            else:
                print("Break")
                #Break when there are no more trucks to create
                break
            #Create a truck object
            cust =Customer(waiting_room= self.waiting_room,env=self.env,stations=self.clerks,wait_times = self.wait_times,battery_charge=truck.Battery)
            cust.creation_time = self.env.now()
            #Hold the simmulation until the next truck is sheduald
            self.hold(truck.Arrival_Time - previous_arrival)
            #Set the previous time
            previous_arrival = truck.Arrival_Time


class Charging_Station(sim.Component):
    def __init__(self,waiting_room,env):
        super().__init__()
        random.seed(time.time())
        self.waiting_room = waiting_room
        self.vehicle = 0
        self.env =  env

    def process(self):
        while True:
            #Continu looping until a vehicle shows up in the waiting line
            while len(self.waiting_room) == 0:
                self.passivate()
            self.vehicle = self.waiting_room.pop()
            self.charge_car()
            

    #This method charges car and stops when the car has been charged
    def charge_car(self):
        loop = 0
        while self.vehicle.battery_charge < 100:
            self.hold(1)
            self.vehicle.battery_charge +=1
            loop +=1
        #Calculate the time that the complete charging procedure took
        self.vehicle.wait_times.append(self.env.now() - self.vehicle.creation_time)
        return loop


class Customer(sim.Component):
    def __init__(self,waiting_room,env,stations,wait_times,battery_charge):
        super().__init__()
        self.waiting_room = waiting_room
        self.env = env
        self.stations = stations
        self.battery_charge = battery_charge
        self.creation_time = 0
        self.wait_times = wait_times

    def process(self):        
        #Put the vehicle in the waiting room
        self.enter(self.waiting_room)
        #Check if there is a station that is passive
        for station in self.stations:
            if station.ispassive():
                station.activate()
                break  # activate at most one clerk
        self.passivate()

#-------------------------------------------------------------------------------------------
class sim_manager():
    def __init__(self,Charging_Stations):
        self.shedual = Prepare()
        self.Charging_stations = Charging_Stations
        #Prepare the truck data
        self.shedual.prepare_data()

    #This function runs the simmulation
    def run_sim(self):
        #Create varaibles for monitoring
        wait_Times = []
        #Prepare the truck data

        #Create the objects that make up the simmulation
        env_Sim = sim.Environment(trace=False)
        waiting_room = sim.Queue("waitingline88")
        clerks = [Charging_Station(waiting_room=waiting_room,env=env_Sim) for _ in range(self.Charging_stations)]
        generator = CustomerGenerator(waiting_room= waiting_room,env=env_Sim,clerks=clerks,wait_times = wait_Times,shedual= self.shedual.trucks )
        #Start the simmulation
        env_Sim.run(till=1440)
        #Delete the objects from the memory
        del(env_Sim)
        del(waiting_room)
        for clerk in clerks:
            del(clerk)
        del(generator)

        #Get the output of the simmulation
        avg = sum(wait_Times)/len(wait_Times)
        min_o = min(wait_Times)
        max_o = max(wait_Times)

        return int(avg),int(min_o),int(max_o)

    def reset_shedual(self):
        self.shedual.prepare_data()

sim_m = sim_manager(3)
print(sim_m.run_sim())
sim_m.reset_shedual()
print(sim_m.run_sim())

#-------------------------------------------------------------------------------------------
#Create a truck enviroment that the model is going to perform in
class TruckEnv(Env):
    def __init__(self):
        self.action_space = Discrete(100)
        #self.action_space = Box(low = -0, high = 10, shape = (1,), dtype = int)
        self.observation_space = Box(low = -3, high = 250, shape = (1,), dtype = np.float64)
        self.state = 0
        self.done = False
        self.running = False
        self.sim_env = sim_manager(3)
        #self.env_sim = env = sim.Environment(trace=False)    

    def step(self,action):           
        print(action)
        wait_time = self.sim_env.run_sim(action)
        
        done = True         
        info = {}
        if wait_time >70 and wait_time <80:
            reward = 1

        else:
            reward = -1

        return np.float32(self.state),reward, done,False, info
    
    def render(self):
        pass

    def reset(self,seed =None):
        super().reset(seed=seed) 
        #Reset the simmulation enviroment
        self.sim_env.reset_shedual()
        #Get a local copy of the schedule
        schedule = self.sim_env.shedual.trucks

        battery = []
        arriaval_time =[]
        #Extract the data from the schedule
        for i in schedule:
            battery.append(i.Battery)
            arriaval_time.append(i.Arrival_Time)
        print(arriaval_time)



        #Create a 
        self.state = 100
        info = {}
        return np.float32(self.state), info   

  
env = TruckEnv()
env.reset()
log_path = os.path.join('.','logs')
#model = PPO('MlpPolicy', env, verbose = 1, tensorboard_log = log_path)

#model.learn(total_timesteps= 10000,progress_bar= True)



