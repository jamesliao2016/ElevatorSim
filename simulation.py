import rand
import period
from system import System
from event import Event
from elevator import Elevator
from elevator_group import ElevatorGroup
from elevator import types, TYPE_F, TYPE_L, TYPE_I, TYPE_E

totalTrialNum = 100
ELEVATOR_PASSENGERS_STAT = 'elevator_%s_%d_num_passengers'
ELEVATOR_IDLE_STAT = 'elevator_%s_%d_idle_time'
ELEVATOR_BUSY_STAT = 'elevator_%s_%d_busy_time'
ELEVATOR_TRAVEL_STAT = 'elevator_%s_%d_travel_time'
GROUP_POOL_STAT = 'elevator_group_%s_pool_size'
GROUP_PASSENGERS_STAT = 'elevator_group_%s_num_passengers'
GROUP_IDLE_STAT = 'elevator_group_%s_idle_time'
GROUP_BUSY_STAT = 'elevator_group_%s_busy_time'
GROUP_TRAVEL_STAT = 'elevator_group_%s_travel_time'
ALL_PASSENGERS_STAT = 'all_num_passengers'
ALL_IDLE_STAT = 'all_idle_time'
ALL_BUSY_STAT = 'all_busy_time'
ALL_TRAVEL_STAT = 'all_travel_time'

class ElevatorArriveEvent(Event):
    def __init__(self, time, group, index):
        Event.__init__(self, time)
        self.elevator_group = group
        self.elevator_index = index

class ElevatorSystem(System):
    def initialize(self):
        # each group holds a certain type of elevator and a certain amount
        # of elevators of that type. We specify the default amount of
        # elevators (from the original data collection) followed by
        # the amount we want to use of that type for the sim
        self.elevator_groups = [ElevatorGroup(TYPE_F, 2, count=2),
                                ElevatorGroup(TYPE_L, 3, count=3),
                                ElevatorGroup(TYPE_I, 1, count=1),
                                ElevatorGroup(TYPE_E, 2, count=2)]
        time = 0
        for elevator_group in self.elevator_groups:
            # schedule arrival of all elevators at time 0
            for i in range(elevator_group.count):
                self.schedule_event(ElevatorArriveEvent(time, elevator_group, i))
        
    def update(self):
        # decide whether or not new passengers need to be generated for each
        # group of elevators based on where we are in the time period
        time_in_minutes = self.clock.time() / 60
        for elevator_group in self.elevator_groups:
            if elevator_group.next_gen <= time_in_minutes:
                while elevator_group.next_gen <= time_in_minutes:
                    elevator_group.next_gen += 5
                    elevator_group.create_passengers(self.clock.time())
                    # mark down this amount
                    self.stats.add(GROUP_POOL_STAT % types[elevator_group.type],
                               elevator_group.pool)

    def handle(self, event):
        if isinstance(event, ElevatorArriveEvent):
            group = event.elevator_group
            index = event.elevator_index
            elevator = group.elevators[index]
             
            if group.pool > 0:
                # if there are waiting passengers to be picked up, 
                # uniformly grab as many as we can
                if group.pool > elevator.capacity:
                    elevator.num_passengers = rand.uniform(1, elevator.capacity)
                else:
                    elevator.num_passengers = rand.uniform(1, group.pool)
                group.pool -= elevator.num_passengers
                # mark down the amount of passengers on board
                self.stats.add(ELEVATOR_PASSENGERS_STAT % 
                                    (types[elevator.type], index),
                               elevator.num_passengers)

                cur_time = self.clock.time()
                
                idle_time = elevator.idle_time(cur_time)
                busy_time = elevator.busy_time(cur_time)
                travel_time = elevator.travel_time(cur_time)
                # mark down the times
                self.stats.add(ELEVATOR_IDLE_STAT % 
                                    (types[elevator.type], index),
                               idle_time)
                self.stats.add(ELEVATOR_BUSY_STAT % 
                                    (types[elevator.type], index),
                               busy_time)
                self.stats.add(ELEVATOR_TRAVEL_STAT % 
                                    (types[elevator.type], index),
                               travel_time)

                # schedule next arrival
                service_time = idle_time + busy_time + travel_time
                time = cur_time + service_time
                self.schedule_event(ElevatorArriveEvent(time, group, index))
            else:
                # schedule the next arrival for the beginning of next 5 minute
                # period
            	event_time = group.next_gen * 60
                cur_time = self.clock.time()
                idle_time = event_time - cur_time
                # mark down the idle time
                self.stats.add(ELEVATOR_IDLE_STAT % 
                                    (types[elevator.type], index),
                               idle_time)
            	self.schedule_event(ElevatorArriveEvent(event_time, group, index))
        
    def finalize(self):
        # at the end of a run, tally up the group totals from the elevator
        # totals and finally everything from the group totals
        for elevator_group in self.elevator_groups:
            for i in range(len(elevator_group.elevators)):
                elevator = elevator_group.elevators[i]
                num_passengers_list = self.stats.get(ELEVATOR_PASSENGERS_STAT %
                                                    (types[elevator.type], i))
                self.stats.add(GROUP_PASSENGERS_STAT % types[elevator.type], 
                               num_passengers_list)
                idle_time_list = self.stats.get(ELEVATOR_IDLE_STAT %
                                                    (types[elevator.type], i))
                self.stats.add(GROUP_IDLE_STAT % types[elevator.type], 
                               idle_time_list)
                busy_time_list = self.stats.get(ELEVATOR_BUSY_STAT %
                                                    (types[elevator.type], i))
                self.stats.add(GROUP_BUSY_STAT % types[elevator.type], 
                               busy_time_list)
                travel_time_list = self.stats.get(ELEVATOR_TRAVEL_STAT %
                                                    (types[elevator.type], i))
                self.stats.add(GROUP_TRAVEL_STAT % types[elevator.type], 
                               travel_time_list)
            self.stats.add(ALL_PASSENGERS_STAT,
                           self.stats.get(GROUP_PASSENGERS_STAT % 
                                          types[elevator_group.type]))
            self.stats.add(ALL_IDLE_STAT,
                           self.stats.get(GROUP_IDLE_STAT % 
                                          types[elevator_group.type]))
            self.stats.add(ALL_BUSY_STAT,
                           self.stats.get(GROUP_BUSY_STAT % 
                                          types[elevator_group.type]))
            self.stats.add(ALL_TRAVEL_STAT,
                           self.stats.get(GROUP_TRAVEL_STAT % 
                                          types[elevator_group.type]))


# If we call run with the same seed parameter each time, not
# only will our results be predictable (reproducable) each time
# we run the program, but the individual calls will have the
# same random values.
#
# This can be used for Correlated Sampling
system = ElevatorSystem()
stats = system.run(totalTrialNum, period.ONE_DAY, seed=0xDEADBEEF)

# now that we have the stats after x trials, we want to specify the order
# in which they're printed out for easy reading
group_order = [
    GROUP_POOL_STAT % 'F',
    GROUP_POOL_STAT % 'L',
    GROUP_POOL_STAT % 'I',
    GROUP_POOL_STAT % 'E',

    GROUP_PASSENGERS_STAT % 'F',
    GROUP_PASSENGERS_STAT % 'L',
    GROUP_PASSENGERS_STAT % 'I',
    GROUP_PASSENGERS_STAT % 'E',

    GROUP_IDLE_STAT % 'F',
    GROUP_IDLE_STAT % 'L',
    GROUP_IDLE_STAT % 'I',
    GROUP_IDLE_STAT % 'E',

    GROUP_BUSY_STAT % 'F',
    GROUP_BUSY_STAT % 'L',
    GROUP_BUSY_STAT % 'I',
    GROUP_BUSY_STAT % 'E',

    GROUP_TRAVEL_STAT % 'F',
    GROUP_TRAVEL_STAT % 'L',
    GROUP_TRAVEL_STAT % 'I',
    GROUP_TRAVEL_STAT % 'E'
]

individual_order = []
for elevator_group in system.elevator_groups:
    for i in range(len(elevator_group.elevators)):
        individual_order.append(ELEVATOR_PASSENGERS_STAT %
                               (types[elevator_group.type], i))
        individual_order.append(ELEVATOR_IDLE_STAT %
                               (types[elevator_group.type], i))
        individual_order.append(ELEVATOR_BUSY_STAT %
                               (types[elevator_group.type], i))
        individual_order.append(ELEVATOR_TRAVEL_STAT %
                               (types[elevator_group.type], i))
output_order = []
output_order.extend([ALL_PASSENGERS_STAT,
                     ALL_IDLE_STAT,
                     ALL_BUSY_STAT,
                     ALL_TRAVEL_STAT])
output_order.extend(group_order)
output_order.extend(individual_order)

stats_output = stats.__str__(ordered_stats=output_order)
print stats_output
