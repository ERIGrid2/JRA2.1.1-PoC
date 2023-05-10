"""
A simple data collector that prints all data and saves to a csv file when the simulation finishes.

"""
import collections
import mosaik_api
import pandas as pd
import matplotlib.pyplot as plt
import csv

META = {
    'type': 'event-based',
    'models': {
        'Monitor': {
            'public': True,
            'any_inputs': True,
            'params': [],
            'attrs': [],
        },
    },
}


class Collector(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid = None
        self.data = collections.defaultdict(lambda:
                                            collections.defaultdict(dict))

    def init(self, sid, time_resolution):
        return self.meta

    def create(self, num, model):
        if num > 1 or self.eid is not None:
            raise RuntimeError('Can only create one instance of Monitor.')

        self.eid = 'Monitor'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs, max_advance):
        data = inputs.get(self.eid, {})
        for attr, values in data.items():
            for src, value in values.items():
                self.data[src][attr][time] = value

        return None

    def finalize(self):
        new_dict = {}
        print('\n Collected data:')
        for sim, sim_data in sorted(self.data.items()):
            # print('- %s:' % sim)
            for attr, values in sorted(sim_data.items()):
                print('  - %s: %s' % (attr, values))
                new_dict[(attr)] = values
        with open('ps_in.csv', 'w') as f:
          for key in new_dict['ps_in'].keys():
            f.write("%s,%s\n"%(key,new_dict['ps_in'][key][0]))
        df = pd.DataFrame(new_dict)
        print("-----------------------------------------")
        print(df)
        df.to_json('output.json')


if __name__ == '__main__':
    mosaik_api.start_simulation(Collector())
