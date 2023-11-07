from src import autoscout24
import pandas as pd


maker = autoscout24.Maker(id='9', name='audi')
model = autoscout24.Model(id=16416, name='A2')

listings = autoscout24.get_listings(maker, model, page=2)
print(*listings, sep='\n')
