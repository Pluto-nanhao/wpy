from gsim import Universe as uv
from gsim import DataRegistry as dr
from gsim import AlphaBase
from gsim import Oputil
import numpy as np

"""

"""

class AlphaSize(AlphaBase):
    def __init__(self, cfg): 
        AlphaBase.__init__(self, cfg)
        self.valid = dr.getData(cfg.getAttributeString('universeId'))
        self.H = int(cfg.getAttributeDefault('H', 3900))
        self.L = int(cfg.getAttributeDefault('L', 5484))
        self.npydata = cfg.getAttributeStringDefault('npydata', 'error')
        self.data = np.memmap(self.npydata, mode='r', dtype=np.float64, shape=(self.H, self.L))
        print(f"npydata path: {self.npydata}")
        self.ndays = cfg.getAttributeDefault('ndays', 240)

        return

    def generate(self, di):
        valid_idx = self.valid[di]
        # self.alpha[valid_idx] =  Oputil.mean(self.data[di-self.delay-self.ndays:di-self.delay+1 , valid_idx],axis=0)
        self.alpha[valid_idx] = self.data[di - 1, valid_idx]
        return

