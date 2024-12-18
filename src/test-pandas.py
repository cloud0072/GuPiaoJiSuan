import pandas as pd
import numpy as np


def test1():
    df = pd.DataFrame(np.random.rand(10, 4), columns=['a', 'b', 'c', 'd', ])
    # df.plot.bar()


test1()
