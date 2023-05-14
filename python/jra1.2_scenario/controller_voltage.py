import sys
from pythonfmu import Fmi2Causality, Fmi2Slave, Real, Integer

class controller_voltage(Fmi2Slave):
    """ 
        Class to model a basic voltage controller to alter 
        demand response.
    
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # initalize inputs and output
        self.deltaP = 0
        self.u3 = 1.0
        self.u4 = 1.0
        self.v_up = 1.0
        self.v_low = 1.0
        # register as inputs/output as per FMI standard
        self.register_variable(Real("u3", causality=Fmi2Causality.input))
        # self.register_variable(Real("u4", causality=Fmi2Causality.input))
        self.register_variable(Real("v_up", causality=Fmi2Causality.input))
        self.register_variable(Real("v_low", causality=Fmi2Causality.input))
        self.register_variable(Integer("deltaP", causality=Fmi2Causality.output))
        print("Controller co-simulation: INIT DONE")
    
    def do_step(self, current_time, step_size):
        """ Function to update state of controller and change demand respose setpoints if required.
        Parameters
        ----------
        comm_point: float
        current time step in co-simulation
        comm_step_size: float
        step size of co-simulation
        """
        # u3 = self.u3
        # u4 = self.u4
        # v_low = self.v_low
        # v_high = self.v_up
        # u_min = min(u3, u4)
        # u_max = max(u3, u4)
        # if (u_max > v_high):
        #     self.tap += 1
        # if (u_min < v_low):
        #     self.tap -= 1
        # if(self.tap > 2):
        #     self.tap = 2
        # elif(self.tap < -2):
        #     self.tap = -2
        u3 = self.u3
        v_low = self.v_low
        v_high = self.v_up
        
        if (u3 > v_high):
            self.deltaP += 1
        if (u3 < v_low):
            self.deltaP -= 1
        if(self.deltaP > 2):
            self.deltaP = 2
        elif(self.deltaP < -2):
            self.deltaP = -2
        return True
