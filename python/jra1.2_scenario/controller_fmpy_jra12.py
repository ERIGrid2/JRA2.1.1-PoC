"""
    A controller implementing a simple voltage control algorithm
"""

import mosaik_api
from itertools import count
import xml.etree.ElementTree as ETree
import math
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import numpy as np
import shutil
import collections

META = {
    "api_version": "3.0",
    "type": "event-based",
    'models': {
        'voltage_controller': {
            'public': True,
            'params': ['v_low', 'v_up'],
            'trigger': ['u3'],
            # 'attrs': ['v3', 'v4', 'deltaP'],
            'attrs': ['u3','deltaP'],
        },
    },
}

class voltage_controller(mosaik_api.Simulator):

    def __init__(self):
        super().__init__(META)
        self.data = collections.defaultdict(dict)
        self._entities = {}
        self.eid_counters = {}
        self.is_responsive = {}             # controller state regarding dead time
        self.wakeup_time = {}               # time stamp until end of dead time
        self.dead_time = 0                  # dead time of controller
        self.unzipdir = None                # directory of FMU
        self.model_description = None       # model description of FMU
        self.model_name = None              # model name of FMU
        self.instance_name = None           # instance name of FMU
        self.vrs = {}                       # dict for FMU value references
        self.vr_inputs = None               # input variables
        self.vr_outputs = None              # output variables      
        self.default_step_time = None       # real time length for one default simulation step
        self.step_size = 1                  # int simulation step size (must be 1 for each simulator)
        self.start_time = 0                 # FMPy parameter
        self.stop_time = 0                  # FMPy parameter
        self.stop_time_defined = False      # FMPy parameter
        self.sec_per_mt = 1                 # Number of seconds of internal time per mosaik time
        self.fmutimes = {}                  # Keeping track of each FMU's internal time
        self.deltaP = 0                     # demand response delta P
        self.v_low = None
        self.v_up = None
        self.eid = None

    def init(self, sid, time_resolution, dead_time, fmu_filename, instance_name, step_size, start_time = 0,
            stop_time = 0, seconds_per_mosaik_timestep = 1):
        self.dead_time = dead_time / seconds_per_mosaik_timestep
        self.start_time = start_time
        self.stop_time = stop_time
        self.step_size = step_size
        self.model_name = fmu_filename
        self.instance_name = instance_name
        # Number of seconds of internaltime per mosaiktime (Default: 1, mosaiktime measured in seconds)
        self.sec_per_mt = seconds_per_mosaik_timestep
        # read the model description 
        self.model_description = read_model_description(self.model_name)
        assert self.model_description is not None
        # collect the value references
        for variable in self.model_description.modelVariables:
            self.vrs[variable.name] = variable.valueReference
        assert self.vrs is not None
        # get the value references for the variables we want to get and set
        # self.vr_inputs = [self.vrs['u3'], self.vrs['u4'],self.vrs['v_low'], self.vrs['v_up']]
        self.vr_inputs = [self.vrs['u3'],self.vrs['v_low'], self.vrs['v_up']]     
     
        self.vr_outputs = [self.vrs['deltaP']]
        print(self.vrs)
        print("Init of controller via mosaik successful")

        return self.meta

    def create(self, num, model, v_low = 0.98, v_up = 1.01):
        counter = self.eid_counters.get(model, count())
        entities = []
        self.v_low=v_low
        self.v_up=v_up
        for i in range(num):
            eid = '%s_%s' % (model, next(counter))  # entity ID
            self.eid=eid
            print (eid)
            # extract the FMU
            self.unzipdir = extract(self.model_name)

            fmu = FMU2Slave(guid = self.model_description.guid,
                    unzipDirectory = self.unzipdir,
                    modelIdentifier = self.model_description.coSimulation.modelIdentifier,
                    instanceName = self.instance_name)
            print("fmu extracted")
            self._entities[eid] = fmu
            fmu.instantiate()
            self._entities[eid].setupExperiment(startTime = self.start_time)
            # Initialize FMU
            self._entities[eid].enterInitializationMode()
            self._entities[eid].exitInitializationMode()

            self.data[eid] = {'deltaP': self._entities[eid].getInteger([self.vr_outputs[0]])}
            self._entities[eid].setReal(self.vr_inputs, [v_low, v_up])
            self.is_responsive[eid] = True
            self.wakeup_time[eid] = None

            # Handling tracking internal fmu times
            self.fmutimes[eid] = self.start_time*self.sec_per_mt

            entities.append( { 'eid': eid, 'type': model, 'rel': [] } )

        return entities

    def step(self, time, inputs, max_advance):
        # print( 'CONTROLLER called at t = {}, inputs = {}'.format( time, inputs ) )
        # This is the internal time.
        print("step controller at "+str(time)+", inputs="+str(inputs))
        target_time = (time + self.start_time )*self.sec_per_mt
        # print("control target_time", target_time)
        for eid, input_data in inputs.items():
            print("eid="+eid+", input_data="+str(input_data))
            [ ( _, u3 ) ] = input_data['u3'].items() if 'u3' in input_data else [ ( None, None ) ]
            #[ ( _, v_low ) ] = input_data['v_low'].items() if 'v_low' in input_data else [ ( None, None ) ]
            #[ ( _, v_up ) ] = input_data['v_up'].items() if 'v_up' in input_data else [ ( None, None ) ]
            communication_point = self.fmutimes[eid]
            communication_step_size = target_time - self.fmutimes[eid]
            # print("ctrl commns point", communication_point, communication_step_size)
            status = self._entities[eid].doStep( currentCommunicationPoint = communication_point, 
                communicationStepSize = communication_step_size )
            # print(status)  
            # assert status is not None
            self.fmutimes[eid] += communication_step_size
            
            # Controller is responsive
            if True is self.is_responsive[eid]:
                if u3 is not None: 
                # or v4 is not None:
                    new_deltaP = self.deltaP_change(eid, u3, communication_step_size )
                    print ("new deltaP from func", new_deltaP)
                    self.deltaP=new_deltaP
                    #input_data['tap'] = new_tap
                    # Enter dead time
                    self.is_responsive[eid] = False
                    self.wakeup_time[eid] = time + self.dead_time
                #else:
                    #input_data['tap'] = None # No inputs --> no output.
            else: # Controller is not responsive (dead time).
                if time >= self.wakeup_time[eid]:
                    self.wakeup_time[eid] = None
                    self.is_responsive[eid] = True

        return None

    def deltaP_change( self, eid, u3, step_size ):
        # self._entities[eid].setReal([self.vr_inputs], [u3, self.v_up, self.v_low])
        self._entities[eid].setReal([self.vr_inputs[0]], [u3][0])
        self._entities[eid].setReal([self.vr_inputs[1]], [self.v_up])
        self._entities[eid].setReal([self.vr_inputs[2]], [self.v_low])
        status = self._entities[eid].doStep( currentCommunicationPoint = self.fmutimes[eid], 
                communicationStepSize = step_size)
        # assert status is not None
        deltaP_new = self._entities[eid].getInteger(self.vr_outputs)
        print("deltaP_new="+str(deltaP_new))

        return(deltaP_new)

    def get_data(self, outputs):
        data = {}
        for eid, attrs in self.data.items():
            if eid == self.eid:
                data[eid]={}
                for attr in attrs:
                    if attr != 'deltaP':
                        raise ValueError('Unknown output attribute "%s"' % attr)
                    data[eid][attr]=self.deltaP

        return data








        
