from typing import List, Tuple
import salabim as sim
from customer_generator import CustomerGenerator

from power_supply import PowerSupply

from charging_station import ChargingStation
from prepare import Prepare


class SimManager:
    def __init__(self, charging_stations: int, total_time: int):
        self.shedual = Prepare(total_time=total_time)
        self.charging_stations = charging_stations

        # Prepare the truck data
        self.shedual.prepare_data(spread_type=3)
        self.total_time = total_time

        # Create varaibles for monitoring
        self.wait_times = []
        self.time_before_service = []
        self.first = False
        self.old_time = 0
        # Setup the enviroment
        self.env_sim = sim.App(
            trace=False,
            random_seed="*",
            name="Simmulation",
            do_reset=False,
            yieldless=True,
        )
        # Create the power supply
        self.power_supply_o = PowerSupply(env=self.env_sim, max_power_from_grid=20000)

        # Create the waiting room
        self.waiting_room = sim.Queue(name="waitingline88", monitor=False)
        self.waiting_room.length_of_stay.monitor(value=True)
        self.waiting_room.length_of_stay.reset_monitors(stats_only=True)

        # Create the charing stations
        self.stations = [
            ChargingStation(
                waiting_room=self.waiting_room,
                env=self.env_sim,
                power_supply=self.power_supply_o,
                max_power_delivery=20,
            )
            for _ in range(self.charging_stations)
        ]

        # Create the EV generator
        self.generator = CustomerGenerator(
            waiting_room=self.waiting_room,
            env=self.env_sim,
            clerks=self.stations,
            wait_times=self.wait_times,
            time_before_service=self.time_before_service,
            shedual=self.shedual.trucks,
        )

    # This function runs the simmulation
    def run_sim(self) -> Tuple[int, int, int]:
        # Create random numbers for the max power supplys
        self.power_supply_o.distribution_rl = [1, 1, 1]
        self.power_supply_o.strategy = 2
        # Start the simmulation
        self.env_sim.run(till=self.total_time)
        while len(self.waiting_room) != 0:
            #print("empty")
            temp =self.waiting_room.pop()
            temp.in_loop = False

        # Get the output of the simmulation
        avg = sum(self.wait_times) / len(self.wait_times)
        min_o = min(self.wait_times)
        max_o = max(self.wait_times)
        self.old_time += self.total_time
        return avg, int(min_o), int(max_o)
    
    def rl_Run(self,power_input): 
        self.power_supply_o.distribution_rl = [power_input[0], power_input[1]]
        
        self.env_sim.run(till=self.old_time + 1)
        self.old_time += 1

        charge_request = 0
        if len(self.waiting_room) > 0:
            for i in self.waiting_room:
                charge_request += 100 - i.battery_charge

        else:
            charge_request = 0      
        if len(self.wait_times) != 0: 
            avg = sum(self.wait_times) / len(self.wait_times)
        else:
            avg = 0

        if self.old_time >= self.total_time:
            return True,avg, len(self.waiting_room), charge_request
        else:
            return False,avg,len(self.waiting_room), charge_request
        
    
    def rl_reset(self):
        self.old_time = 0
        avg = sum(self.wait_times) / len(self.wait_times)
        min_o = min(self.wait_times)
        max_o = max(self.wait_times)   
        while len(self.waiting_room) != 0:
                #print("empty")
            temp =self.waiting_room.pop()
            temp.in_loop = False
        #print(self.env_sim.get_time_unit())
        self.wait_times.clear()
        self.waiting_room.clear()
        self.env_sim.reset_now()
        self.shedual.prepare_data(spread_type=3)
        self.generator.shedual = self.shedual.trucks
        self.generator.reset()
        return avg, int(min_o), int(max_o)






    def rerun(self):
        while len(self.waiting_room) != 0:
            #print("empty")
            temp =self.waiting_room.pop()
            temp.in_loop = False
        #print(self.env_sim.get_time_unit())
        self.wait_times.clear()
        self.waiting_room.clear()
        self.env_sim.reset_now()
        self.shedual.prepare_data(spread_type=3)
        self.generator.shedual = self.shedual.trucks
        self.generator.reset()
        self.env_sim.run(till=self.total_time)
        #self.generator.activate()
        #print(len(self.wait_times),"length")
        avg = sum(self.wait_times) / len(self.wait_times)
        min_o = min(self.wait_times)
        max_o = max(self.wait_times)
        self.old_time += self.total_time
        return avg, int(min_o), int(max_o)

    def reset_shedual(
        self,
    ):  # This method resets the complete simmulation to its starting position
        self.env_sim.reset()
        self.waiting_room.clear()
        self.env_sim.reset_now(0)
        self.first = True
        self.env_sim = sim.App(
            trace=False,
            random_seed="*",
            name="Simmulation",
            do_reset=True,
            yieldless=True,
        )
        # Make sure all the charging stations are disabled
        self.shedual.prepare_data(spread_type=3)
        self.generator.shedual = self.shedual.trucks
