# fmi_singlepipe_python_dummy.py
"""
Pretends to be a wrapper for the single pipe FMU, but isn't.
"""
import mosaik_api
from collections import deque


META = {
    "api_version": "3.0",
    'type': 'hybrid',
    'models': {
        'Singlepipe': {
            'public': True,
            'params': [],
            'attrs': ['msg_in', 'msg_out'],
            'trigger': ['msg_in'],
            'non-persistent': ['msg_out']
        },
    },
}


class Singlepipe(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.agents = []
        # self.sid = None
        self.time_resolution = None
        self.sid = None
        self.eid = None
        self.tqueue = None
        self.mqueue = None

    def init(self, sid, time_resolution):
        self.sid = sid
        self.time_resolution = time_resolution
        #print('.........? Would be calling FMI3Instantiate here')
        return self.meta

    def create(self, num, model):
        assert (model == 'Singlepipe'), f"Invalid model {model}"
        assert (num == 1 and self.eid is None), f"Only one entity allowed for simulator {self.sid}."
        self.eid = 'pipe-0'
        entities = [
            {'eid': self.eid,
             'type': model,
             'rel': [],
            }]
        self.mqueue = deque()
        self.tqueue = deque();
        #print('.........? Would be calling FMI3EnterInitializationMode here')
        #print('.........? Would be setting parameters (FMI3SetXXX) here')
        #print('.........? Would be calling FMI3ExitInitializationMode here')
        return entities

    def step(self, t, inputs, max_advance):
        print('.........# called step(time='+str(t)+', inputs='+str(inputs)+', max_advance='+str(max_advance))

        #print('.........? Would be calling FMI3DoStep here')

        self.time = float(t*self.time_resolution)

        for agent_eid, attrs in inputs.items():
            messages = attrs['msg_in']
            assert len(messages) == 1
            msg_in = list(messages.values())[0];
            msg_out=None

            if msg_in is not None:
                #print('.........? Would be calling FMI3EnterEventMode here')
                #print('.........? Would be calling FMI3SetValue here')
                #print('.........? Would be calling FMI3SetClock here')
                # delayed_time = 0.5177645315523848+self.time
                delayed_time = 5+self.time
                self.mqueue.append({'value':msg_in, 'out_time':delayed_time})
                self.tqueue.append({'time':delayed_time})
                print("Incoming message. MQueue is now "+str(self.mqueue))
                #print("TQueue is now "+str(self.tqueue))
                #print('.........? Would be calling FMI3ExitEventMode here')
            #elif msg_out is not None:
                #print('.........? Would be calling FMI3EnterEventMode here')
                #print('.........? Would be calling FMI3GetClock here')
                #print('.........? Would be calling FMI3GetValue here')
                #print('.........? Would be calling FMI3ExitEventMode here')

        #print('.........? Would be calling FMI3UpdateDiscreteStates here')
        #print('.........? Would be calling FMI3EnterStepMode here')

        cache = self.cache = {}

        if len(self.tqueue)>0:
            nextout_mtime=int(self.tqueue.pop()['time']/self.time_resolution)
            #print('.........$ step returns:'+str(nextout_mtime))
            return nextout_mtime

        #print('.........$ step returns: None')
        return None

    def get_data(self, outputs):
        #print('.........# called get_data(outputs='+str(outputs))
        #print('.........Ø mqueue='+str(self.mqueue))
        data = {}
        for eid, attrs in outputs.items():
            if eid == self.eid:
                data[eid]={}
                for attr in attrs:
                    if attr != 'msg_out':
                        raise ValueError('Unknown output attribute "%s"' % attr)
                    if len(self.mqueue)>0:
                        nextout=self.mqueue[0]['out_time']
                        if (self.time>=nextout):
                            data[eid][attr]=self.mqueue.pop()['value']
                            print("Message out:"+str(data[eid][attr]))

        #print('.........$ get_data returns: '+str(data))
        return data


def main():
    return mosaik_api.start_simulation(Singlepipe())


if __name__ == '__main__':
    main()
