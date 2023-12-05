from sim_manager import SimManager
from customer import Customer
import gc
import salabim as sim

array = [0.22,1.0,0.2]
if __name__ == "__main__":
    man = SimManager(1, 1400)
    for i in range(2000):        
        done = False
        while done == False:
           done,temp = man.rl_Run(array)
        print(man.rl_reset())