"""This scenario tests dummy comms"""

# Import packages needed for the scenario.
import mosaik
from mosaik.util import connect_many_to_one
import os
import argparse
from pathlib import Path
import datetime

# N ticks of mosaik time = 1 second
MT_PER_SEC = 1000

# Specify simulator configurations
sim_config = {
    'Grid': {
        'python':'power_grid_fmpy_mosaik:pandapower_LV'
    },
    'Ctrl': {
        'python': 'controller_fmpy_mosaik:tap_controller'
#         'python': 'controller_dummy:Controller'
    },
    'Collector': {
        'python': 'simulators.collector:Collector'
    },
    'PeriodicSender':{
            'python': 'periodic_sender_fmpy:PeriodicSender',
    },
    'CommSim':{
        'python': 'fmi_singlepipe:Singlepipe',
    },
    'Collector': {
        'cmd': '%(python)s collector.py %(addr)s',
    },
}


# Set scenario parameters:
STOP = 10 * 60* MT_PER_SEC  # 10 minutes
START = 0
# Set up the "world" of the scenario
world = mosaik.World(sim_config, time_resolution=1/MT_PER_SEC, debug=True)

# Initialize the simulators
periodic_sender_sim = world.start( 'PeriodicSender', verbose=False )
sender_U3 = periodic_sender_sim.PeriodicSender( period = 60.0*MT_PER_SEC )

# Simulator for power system
loadflow_sim = world.start('Grid', fmu_filename = '../../fmus/Pandapower_LV.fmu', instance_name ='powerflow1', start_time = 0.0, stop_time = STOP)
loadflow = loadflow_sim.pandapower_LV.create(1)[0]

# Simulator for controller.
controller_sim = world.start( 'Ctrl', dead_time= 0,
    fmu_filename = '../../fmus/controller_tap.fmu', instance_name='Controller1',step_size = 1e-1*MT_PER_SEC,
    start_time=0, stop_time=STOP,seconds_per_mosaik_timestep=1./MT_PER_SEC)
controller =  controller_sim.tap_controller.create(1)[0]

# data collector

collector = world.start('Collector')

# dummy simulator for the controller

#controller_sim = world.start( 'Ctrl')
#controller = controller_sim.Controller()

# dummy simulator for the comms

comm_network_sim = world.start( 'CommSim', fmu_filename = '../../fmus/Pipeline_deterministic.fmu',
                                           instance_name = 'test_sim_ict', start_time = 0.0, stop_time = STOP)
comm_network = comm_network_sim.Singlepipe()

# data collector

monitor = collector.Monitor()

# Connect voltage U3 to controller.
world.connect( loadflow, sender_U3, ('V3', 'ps_in'))
world.connect( sender_U3, comm_network, ( 'ps_out', 'msg_in' ))
world.connect( comm_network, controller, ( 'msg_out', 'u3' ))
#world.connect( comm_network, controller, ( 'msg_out', 'voltage_in' ) )

# #  # Connect output from controller to OLTC.
world.connect( controller, loadflow, 'tap' , time_shifted=True, initial_data={'tap':0})
# world.connect( controller, comm_network, ( 'tap', 'ctrl_send' ) )
# # world.connect( comm_network, tap_actuator, ( 'ctrl_receive', 'tap_setpoint' ) )
# # world.connect( tap_actuator, loadflow, ( 'tap_position', 'tap' ),
# #     time_shifted=True, initial_data={ 'tap_position': 0 } )

world.connect( loadflow, monitor, ('V3', 'ps_in'))
world.connect( sender_U3, monitor, ('ps_out', 'msg_in'))
world.connect( comm_network, monitor, ('msg_out', 'u3'))
world.connect( controller, monitor, 'tap' )

world.run(until=STOP, print_progress=True)
