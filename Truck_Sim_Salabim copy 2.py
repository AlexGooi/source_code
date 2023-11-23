# pip install stable-baselines3[extra]
# Python version 3.9.18
from gymnasium import Env
from gymnasium.spaces import Discrete, Box, Dict, Tuple, MultiBinary, MultiDiscrete 
import numpy as np
import random
import os
import time
from scipy.stats import expon
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from dataclasses import dataclass
import matplotlib.pyplot as plt
import salabim as sim
import gc


#-------------------------------------------------------------------------------------------
def limit(lower,value,max):
    if value < lower:
        return lower
    elif value > max:
        return max
    else:
        return value
    
#-------------------------------------------------------------------------------------------
#Struct that holds the information regarding a truck
@dataclass
class Truck:
    Battery:                np.int16
    Arrival_Time:           np.int16
    total_time:             np.int16
    total_wait_Time:        np.int16

#Trcuk that hold charging station information
@dataclass
class Consumption:
    Power_Consumption:      np.real#Current consumption
    Max_Power_Consumption:  np.real#Max consumption from the 
    Max_Power_Reqeust:      np.real#Max power the charging station is able to get

arrival_times = sim.Exponential(60 / 40)
service_times = sim.Exponential(60 / 50)
#-------------------------------------------------------------------------------------------
#Class that prepares a car arrival set
class Prepare():
    def __init__(self,total_time):
        #Create an empty list where we can store the truck scedual
        self.trucks = []
        self.total_time = total_time
        self.arrival_times = sim.Exponential(60 / 40)
        self.service_times = sim.Exponential(60 / 50)
        random.seed(time.time())
        #print(self.service_times.sample())
        self.avg_wait_time = []

    def prepare_data(self,spread_type):
        self.trucks = []
        time = 0
        first = False   
        #Loop until a day is finished

        while time <self.total_time:           
            if spread_type == 1:     
                #Create a new data object
                Truck_Data = Truck(Battery= sim.Uniform(20, 80).sample(),Arrival_Time=time,total_time=0)  
            elif spread_type == 2:                            
                Truck_Data = Truck(Battery= sim.Uniform(40).sample(),Arrival_Time=time,total_time=0,total_wait_Time=0)   
            elif spread_type == 3: 
                arrival, service_time = self.poison()
                self.avg_wait_time.append(service_time)
                service_invert = 100.0 - service_time
                #print(service_invert)
                Truck_Data = Truck(Battery= service_invert,Arrival_Time=time,total_time=0,total_wait_Time=0)   
            #Append the data to the list
            self.trucks.append(Truck_Data)   
            
            #Determine the new arrival time
            if first == False: 
                time += arrival
            else:
                first = True

        #print("Avarage = ",sum(self.avg_wait_time)/len(self.avg_wait_time))
        #print(self.trucks)
    def poison(self):
        # Given parameters

        # Generate inter-arrival times for the students (Poisson process)
        # Generate service times for the students (exponential distribution)

        #return 30,60
        return self.arrival_times.sample(),self.service_times.sample()
    

#-------------------------------------------------------------------------------------------
class CustomerGenerator(sim.Component):
    def __init__(self,shedual,name):
        super().__init__(name=name)
        self.debug = False
        self.shedual = shedual

    
    def setup(self):
        self.mode.monitor(False)
        self.status.monitor(False)

    def process(self):
        previous_arrival = 0
        print(len(self.shedual))
        while True:     
            if len(self.shedual) > 0:
                pass
            else:

                break
            #Create a truck object
            Customer()
            self.hold(arrival_times.sample())

class Charging_Station(sim.Component):
    def __init__(self,max_power_delivery,name):
        super().__init__(name=name)
        random.seed(time.time())

        self.vehicle = 0
        self.max_power_delivery = max_power_delivery
        self.power_consumption = Consumption(0,0,0)
        #Append the power consumption to the consumtion list
        #power_supply.power_used_list.append(self.power_consumption)
        self.power_consumption.Max_Power_Reqeust = self.max_power_delivery

    def setup(self):
        self.mode.monitor(False)
        self.status.monitor(False)

    def process(self):
        while True:
            #Continu looping until a vehicle shows up in the waiting line
            while len(waiting_room) == 0:
                self.passivate()
            self.vehicle = waiting_room.pop()
            self.charge_car()           

    #This method charges car and stops when the car has been charged
    def charge_car(self):
        add_Charge = 0
        wait_Times.append(env.now() )
        charge = 80
        while charge < 100:

            if charge < 100 - self.max_power_delivery:
                add_Charge = self.power_consumption.Max_Power_Consumption
                self.hold(1)
            else:
                add_Charge = limit(0,self.power_consumption.Max_Power_Consumption,100 - charge)
                self.hold(add_Charge)
            #print("add_Charge",add_Charge)
            #Note to the power supply much power is being used from it
            self.power_consumption.Power_Consumption = add_Charge   
            charge +=add_Charge
        #Calculate the time that the complete charging procedure took


    #This method calculates the maximum amount of charge the charging pole is allowed to give
    def max_power_consumption(self):
        #Calculate the total amount of power already used by the charging stations
        power_used = 0
        for i in self.power_supply.power_used:
            power_used += i
       

class Customer(sim.Component):
    def setup(self):
        self.mode.monitor(False)
        self.status.monitor(False)
    def process(self):        
        #Put the vehicle in the waiting room        
        self.enter(waiting_room)
        #print(len(self.waiting_room))
        #Check if there is a station that is passive
        for station in stations:
            if station.ispassive():                
                station.activate()
                break  # activate at most one clerk
        self.passivate()

#This class resables the general power supply that the chraging stations are coupled to
class Power_supply(sim.Component):
    def __init__(self,max_power_from_Grid,name):
        super().__init__(name=name)
        self.max_power_from_grid = max_power_from_Grid
        self.power_used_list = []
        self.distribution_rl = []
        self.power_used = 0
        self.strategy = 0
        self.max_reached = False

    def setup(self):
        self.mode.monitor(False)
        self.status.monitor(False)

    def process(self):
        #Calculate the amount of energy that is currently being used
        while True:
            total = 0
            #Select the charging strategy
            if self.strategy == 0:
                self.__distribute_power_simple()
            elif self.strategy == 1:
                self.__disrtibute_power_share_equal()
            elif self.strategy == 2:
                self.__distribute_power_rl(rl_distribution=self.distribution_rl)
            #Check if the list has members
            print(len(self.power_used_list))
            if len(self.power_used_list) != 0:
                #Loop through all the charging stations
                for i in self.power_used_list:
                    total += i.Power_Consumption
                self.hold(1)
            else:
                pass
        print("Process_Stop")

    def __distribute_power_simple(self):#This method resembles the simplest distribution (give max until it is out)
        #Loop through all the power cinsumers
        total_distributed = 0
        for i in self.power_used_list:
            #Calculate the max distribution left
            max_allowd = limit(0,self.max_power_from_grid - total_distributed,self.max_power_from_grid)
            #print("Max_Allowed",max_allowd)
            i.Max_Power_Consumption = limit(0,i.Max_Power_Reqeust,max_allowd)
            #if i.Max_Power_Consumption == 0:
                #print("No power_To_Pole")
            total_distributed += i. Max_Power_Consumption
                                                
    def __disrtibute_power_share_equal(self):#This method resables a equal share to all the charging stations
        #Loop through all the power consumers
        total_distributed = 0
        if len(self.power_used_list) != 0:
            available_per_station = self.max_power_from_grid / len(self.power_used_list)
            for i in self.power_used_list:#Calculate the total amount
                #Give the allowed power to the stations
                i.Max_Power_Consumption = limit(0,i.Max_Power_Reqeust,available_per_station)

    def __distribute_power_rl(self,rl_distribution):#This method is used to distribute the power with the help of reinforcemnt learning
        total_distributed = 0
        counter = 0
        if len(self.power_used_list) != 0:
            for i in self.power_used_list:
                max_allowd = limit(0,self.max_power_from_grid - total_distributed,self.max_power_from_grid)
                max_allowd = limit(0,max_allowd,i.Max_Power_Reqeust)
                max_allowd = limit(0,max_allowd,limit(0,self.max_power_from_grid - total_distributed,self.max_power_from_grid - total_distributed))
                #Note to the system when the maximum energy consumption is reached
                if max_allowd == 0:
                    self.max_reached = True
                else:
                    self.max_reached = False
                #Insert the max power consumption from the reinforcement learning model into 
                i.Max_Power_Consumption = limit(0,rl_distribution[counter],max_allowd)       
                total_distributed += i. Max_Power_Consumption
                counter += 1

#-------------------------------------------------------------------------------------------
env = sim.App(trace=False,random_seed="*",name= "Simmulation",time_unit= "minutes",do_reset= False, yieldless= True)
waiting_room = sim.Queue(monitor= False,name = "*")
power_supply = Power_supply(max_power_from_Grid= 20000,name = "*")
stations = [Charging_Station(max_power_delivery=1,name = "*") for _ in range(3)]

shedual = Prepare(total_time=500000)
shedual.prepare_data(3)
generator = CustomerGenerator(shedual= shedual.trucks,name = "*" )
wait_Times = []
time_before_service = []

class sim_manager():
    def __init__(self,Charging_Stations,total_time):
  
        self.Charging_stations = Charging_Stations
        #Prepare the truck data
        #self.hesdual.prepare_data(spread_type=3)
        self.total_time = total_time


    #This function runs the simmulation
    def run_sim(self):
        #Create random numbers for the max power supplys
        #max_power = np.random.randint(20,size=1)
        power_supply.distribution_rl = [1,1,1]
        #self.Power_supply_o.distribution_rl = [max_power[0],max_power[1],max_power[2]]
        power_supply.strategy = 2
        #Start the simmulation)

        #Get the output of the simmulation
        #if len(self.wait_Times) > 0: 
        #print(len(self.wait_Times))
        print("len =",len(wait_Times))
        avg = sum(wait_Times)/len(wait_Times)
        min_o = min(wait_Times)
        max_o = max(wait_Times)
        #else:
         #   print("Niet goed")
          #  avg = 0
          #  min_o = 0
           # max_o = 0

        return avg,int(min_o),int(max_o)

    def reset_shedual(self):#This method resets the complete simmulation to its starting position
        env.reset_now(0)
  
        #print("length of stations", len(self.stations))
        
        # #dsds
        #self.Power_supply_o.
        #self.generator.__init__(waiting_room= self.waiting_room,env=self.env_Sim,clerks=self.stations,wait_times = self.wait_Times,time_before_service=self.time_before_service,shedual= self.shedual.trucks)        
        #print("Reset")
        #Make sure all the charging stations are disabled

        self.shedual.prepare_data(spread_type= 3)
        self.generator.shedual = self.shedual.trucks
        #print("Length =",len(self.generator.shedual))
        #print()

count = 0 
sim_m = sim_manager(1,500000)

env.run(till=500000)
#print(sim_m.run_sim())
    #sim_m.reset_shedual()
