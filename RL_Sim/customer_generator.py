from typing import List
import salabim as sim
from charging_station import ChargingStation

from customer import Customer
from data import Truck

available_trucks = []
class CustomerGenerator(sim.Component):
    def __init__(
        self,
        waiting_room: sim.Queue,
        env: sim.App,
        clerks: List[ChargingStation],
        wait_times: List,
        time_before_service: List,
        shedual: List[Truck]
    ):
        super().__init__(name="Generator")
        self.waiting_room = waiting_room
        self.env = env
        self.clerks = clerks
        self.debug = False
        self.wait_times = wait_times
        self.time_before_service = time_before_service
        self.shedual = shedual
        self.mode.monitor(False)
        self.status.monitor(False)
        self.previous_Arrival = 0
        #print(len(available_trucks),"available")

    def process(self):
        previous_arrival = 0
        number2 = 0
        available_trucks.clear()
        #print(available_trucks,"AVA")
        while True:
            #print("generate")
            # Check if there ia an truck left in the list
            if len(self.shedual) > 0:

                # Get the next truck out of the list
                truck = self.shedual.pop(0)

                if len(available_trucks) == 0:
                    #print("Created?????")
                    # Create a truck object
                    customer = Customer(creation_time=self.env.now(),
                        waiting_room=self.waiting_room,
                        env=self.env,stations=self.clerks,wait_times=self.wait_times,time_before_service=self.time_before_service, battery_charge=truck.battery,number= number2
                    )
                    available_trucks.append(customer)
                else:
                    truck_found = False
                    #print(len(self.available_trucks),"length")
                    for cust in available_trucks:
                        #print(cust.status.get())
                        if cust.in_loop == False :
                            cust.creation_time = self.env.now()
                            cust.in_loop = True
                            cust.battery_charge = truck.battery
                            #print("activate_old")
                            cust.activate()
                            cust.process()
                            #print("Old_Truck")
                            truck_found = True
                            break
                    if truck_found == False: 
                        #print("new_Created")
                        customer = Customer(creation_time=self.env.now(),
                        waiting_room=self.waiting_room,
                        env=self.env,stations=self.clerks,wait_times=self.wait_times,time_before_service=self.time_before_service, battery_charge=truck.battery,number= number2
                        )
                        available_trucks.append(customer)  
                        #print(len(available_trucks))
                        number2 += 1
                # Hold the simmulation until the next truck is sheduald
                #print(truck.arrival_time,"djfdjfkdjfk")
                #print("kdjfkdjfkjdk", truck.arrival_time - self.previous_Arrival)
                self.hold(truck.arrival_time - self.previous_Arrival)

                # Set the previous time
                self.previous_Arrival = truck.arrival_time

            else:
             #   # Break when there are no more trucks to create

                self.standby()
        
    def reset(self):
        self.previous_Arrival = 0