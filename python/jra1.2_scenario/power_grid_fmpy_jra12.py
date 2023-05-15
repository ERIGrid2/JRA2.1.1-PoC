"""
    Simulate the low voltage power grid using a pandaPower FMU
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
    "type": "time-based",
    'models': {
        'pandapower_LV': {
            'public': True,
            'params': [],
            'attrs': ['deltaP', 'L_3', 'L_4', 'V3'],
            # 'attrs': ['tap', 'L_3', 'L_4', 'V3', 'v4'],
        },
    },
}

class pandapower_LV_jra12(mosaik_api.Simulator):

    def __init__(self):
        super().__init__(META)
        self.data = collections.defaultdict(dict)
        self.vrs = {}
        self._entities = {}
        self.eid_counters = {}
        self.unzipdir = None                # directory of FMU
        self.model_description = None
        self.model_name = None              # model name of FMU
        self.instance_name = None           # instance name of FMU
        self. val_in = [0]
        self.val_out = [0]
        self.val_in_clock = None
        self.val_out_clock = None
        self.default_step_time = None       # real time length for one default simulation step
        self.tolerance = 1e-8
        self.time_resolution
        self.start_time = 0                 # FMPY parameter
        self.stop_time = 0                  # FMPY parameter
        self.step_size = 1                  # in real time seconds
        # self.uri_to_extracted_fmu = None
        self.fmutimes = {}                  # Keeping track of each FMU's internal time
        self.current_deltaP = 0             # current delta P of the flexible load

    def init(self, sid, time_resolution, fmu_filename, instance_name, start_time = 0, stop_time = 0):
        print("entered init of grid")
        self.time_resolution=time_resolution
        self.start_time = start_time
        self.stop_time = stop_time
        self.model_name = fmu_filename
        self.instance_name = instance_name
        # read the model description 
        self.model_description = read_model_description(self.model_name)
        assert self.model_description is not None
        # collect the value references
        for variable in self.model_description.modelVariables:
            self.vrs[variable.name] = variable.valueReference
        assert self.vrs is not None
        # get the value references for the variables we want to get and set
        self.vr_inputs = [self.vrs['P_load3'], self.vrs['P_load4'], self.vrs['P_loadVar']]
        # self.vr_outputs = [self.vrs['Vmpu_bus3'], self.vrs['Vmpu_bus4']] 
        # for single output
        self.vr_outputs = [self.vrs['Vmpu_bus3']]
        print(self.vrs)
        print("Init of power system via mosaik successful")
        return self.meta

    def create(self, num, model):
        counter = self.eid_counters.get(model, count())
        entities = []
        for i in range(num):
            eid = '%s_%s' % (model, next(counter))  # entity ID
            print (eid)
            # extract the FMU
            self.unzipdir = extract(self.model_name)

            fmu = FMU2Slave(guid = self.model_description.guid,
                    unzipDirectory = self.unzipdir,
                    modelIdentifier = self.model_description.coSimulation.modelIdentifier,
                    instanceName = self.instance_name)
            print("fmu extracted")
            self._entities[eid] = fmu
            # print(self._entities[eid], fmu)
            fmu.instantiate()
            # self._entities[eid].instantiate()
            # print("grid FMU create done")

            # assert status is not None
            # fmu.instantiate()
            # fmu.setupExperiment(startTime = self.start_time)
            # fmu.enterInitializationMode()
            # fmu.exitInitializationMode()
            # print("FMU init done")
            # volt = fmu.getReal([self.vr_outputs[0]])
            # print(volt)

            self._entities[eid].setupExperiment(startTime = self.start_time)
            self._entities[eid].enterInitializationMode()
            self._entities[eid].exitInitializationMode()
            # self.data[eid] = {
            #     'V3': self._entities.getReal([self.vr_outputs[0]]),
            #     'V4': self._entities.getReal([self.vr_outputs[1]]),
            # }
            self.data[eid] = {
                'V3': self._entities[eid].getReal([self.vr_outputs[0]]),
            }
            # print(self.data[eid])
            
            # Handling tracking internal fmu times
            self.fmutimes[eid] = self.start_time*self.time_resolution
            entities.append( { 'eid': eid, 'type': model, 'rel': [] } )
        print("create function of grid successful")
        return entities

    def load_ramp(self, load_high, load_low, ramp_time, t):
        if t > ramp_time:
            load = load_high
        else:
            delta = 1 - ( ramp_time - t ) / ramp_time
            load = load_low + (load_high - load_low ) * delta
        return load 

    def step(self, time, inputs, max_advance):
        # This is the internal time.
        target_time = time*self.time_resolution
        #target_time = ( time + self.start_time )*self.sec_per_mt

        for eid, input_data in inputs.items():
        
            [ ( _, l3 ) ] = input_data['L_3'].items() if 'L_3' in input_data else [ ( None, None ) ]
            [ ( _, l4 ) ] = input_data['L_4'].items() if 'L_4' in input_data else [ ( None, None ) ]
            [ ( _, deltaP ) ] = input_data['deltaP'].items() if 'deltaP' in input_data else [ ( None, None ) ]

                        
            if 0 == math.fmod( time, self.step_size ) or deltaP is not None:
                             
                if l3 is not None: self.vrs['P_load3'] = l3
                if l4 is not None: self.vrs['P_load4'] = l4
                if deltaP is not None:
                    dxp=deltaP[0]*1e-3
                    self.vrs['P_loadVar'] = (15e-3)+dxp
                    print("+++++++++++++++++++++ ",deltaP[0])
                    print("///////////////////// ",dxp)
                    print("--------------------- ",self.vrs['P_loadVar'])
        
                load_3 = self.load_ramp(load_high = 5e-3, load_low = 2e-3, ramp_time = self.stop_time/2,  t = time )
                # print(type (load_3))
                load_4 = self.load_ramp(load_high = 7e-3, load_low = 4e-3, ramp_time = self.stop_time/2,  t = time )
                # tap_pos = 0        
                # self._entities[eid].setReal([self.vr_inputs], [load_3, load_4])
                self._entities[eid].setReal([self.vr_inputs[0]], [load_3])
                self._entities[eid].setReal([self.vr_inputs[1]], [load_4])
                if deltaP is not None:
                    dxr=(15e-3)+(deltaP[0]*1e-3)

                    self._entities[eid].setReal([self.vr_inputs[2]], [dxr])
                # print("Error is here")

                communication_point = self.fmutimes[eid]
                communication_step_size = target_time - self.fmutimes[eid]
                status = self._entities[eid].doStep( currentCommunicationPoint = communication_point, 
                communicationStepSize = communication_step_size )               
                self.fmutimes[eid] += communication_step_size
                
                # self.data[eid] = {
            #     'V3': self._entities.getReal([self.vr_outputs[0]]),
            #     'V4': self._entities.getReal([self.vr_outputs[1]]),
            # }
                self.data[eid] = {
                'V3': self._entities[eid].getReal([self.vr_outputs[0]]),
            }

        return int(time + (1 / self.time_resolution)) # self.step_size
    
    def get_data(self, outputs):
        data = {}
        for eid, edata in self.data.items():
            requests = outputs[eid]
            mydata = {}
            for attr in requests:
                try:
                    mydata[attr] = edata[attr]
                except KeyError:
                    raise RuntimeError("pandapower FMU has no attribute {0}".format(attr))
            data[eid] = mydata
        return data


    
if __name__ == '__main__':
    mosaik_api.start_simulation(pandapower_LV())

