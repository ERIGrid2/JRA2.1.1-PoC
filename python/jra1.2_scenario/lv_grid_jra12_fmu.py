
import pandapower as pp
from pythonfmu import Fmi2Causality, Fmi2Slave, Real, Integer

class Pandapower_LV_jra12(Fmi2Slave):
    """ Class to create the fmu for the pandapower LV network
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # creates the pandapower LV network
        self.net = pp.from_pickle("erigrid_jra12_nw.p")
        # set load in MW
        self.P_load3 = 3e-3
        self.Q_load3 = 0.96e-3 
        self.P_load4 = 3e-3
        self.Q_load4 = 0.96e-3 
        self.P_loadVar = 0
        self.Vmpu_bus3 = 1.0
        self.Vmpu_bus4 = 1.0
        # fmi inputs: active power of loads and tap
        self.register_variable(Real("P_load3", causality=Fmi2Causality.input))
        self.register_variable(Real("P_load4", causality=Fmi2Causality.input))
        self.register_variable(Real("P_loadVar", causality=Fmi2Causality.input))
        # fmi outputs: bus 3 and 4 voltages
        self.register_variable(Real("Vmpu_bus3", causality=Fmi2Causality.output))
        # self.register_variable(Real("Vmpu_bus4", causality=Fmi2Causality.output))

    def do_step(self, current_time, step_size):
        # set values of load 3 and 4 in pandapower nw
        self.net.load.at[0, "p_mw"] = self.P_load3
        self.net.load.at[1, "p_mw"] = self.P_load4
        self.net.load.at[0, "q_mvar"] = self.Q_load3
        self.net.load.at[1, "q_mvar"] = self.Q_load4
        self.net.load.at[1, "p_mw"] = self.P_loadVar
        # run power flow
        pp.runpp(self.net, numba=False)
        # obtain bus voltages of buses 3 and 4
        self.Vmpu_bus3 = self.net.res_bus.at[2, 'vm_pu']
        # self.Vmpu_bus4 = self.net.res_bus.at[3, 'vm_pu']
    
        return True
