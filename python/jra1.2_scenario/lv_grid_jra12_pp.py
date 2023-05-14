import pandapower as pp
import os

net = pp.create_empty_network()
    
def create_network():
    """model based on TC-3 powerfactory model from ERIGrid 1.
    Network consists of one HV bus, three LV buses, two loads and one controllable load
    """
    bus1 = pp.create_bus(net, name = "HV_Bus", vn_kv = 20, type = "b")
    bus2 = pp.create_bus(net, name = "LV_Bus2", vn_kv = 0.4, type = "b")
    bus3 = pp.create_bus(net, name = "LV_Bus3", vn_kv = 0.4, type = "b")
    bus4 = pp.create_bus(net, name = "LV_Bus4", vn_kv = 0.4, type = "b")
    # external grid connection
    pp.create_ext_grid(net, bus1, vm_pu=1.00, va_degree=0.0) 
    # connect transformer between bus 1 and bus 2
    trafo1 = pp.create_transformer(net, bus1, bus2, name="OLTC", std_type="0.25 MVA 20/0.4 kV")
    # connect bus 2-3 and bus 2-4 via lines
    line1 = pp.create_line(net, bus2, bus3, length_km=2, std_type="NAYY 4x50 SE", name="Line-2-3")
    line2 = pp.create_line(net, bus2, bus4, length_km=3, std_type="NAYY 4x50 SE", name="Line-2-4")
    # create loads
    pp.create_load(net, bus3, p_mw=3e-3, q_mvar=0.96e-3, name="load3")
    pp.create_load(net, bus4, p_mw=3e-3, q_mvar=0.96e-3, name="load4")
    pp.create_load(net, bus4, p_mw=10e-3, q_mvar=0.0, name="loadVar")
    return net

def run_pf():
    pp.runpp(net)
    print(net.res_bus)
    
def save_nw():
    # path to store pandapower network as'pickle' file
    pandapower_net_file = os.path.join(os.getcwd(), 'erigrid_jra12_nw.p')
    # load pickle file as FMU and use as pandapower network
    pp.to_pickle(net, pandapower_net_file)
    
if __name__ == '__main__':
    net = create_network()
    run_pf()
    save_nw()

