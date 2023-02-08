import pandas as pd
import numpy as np 
import json 
import pickle as pkl

json_file_path ='../data/mondo.json'
icd_omim={}
icd_do={}

with open(json_file_path, 'r') as j:
     contents = json.loads(j.read())

     data = contents['graphs'][0]['nodes']

     for i in data:
        
        if 'meta' in i:
            if 'xrefs' in i['meta']:
                icds = i['meta']['xrefs']
                for j in icds:  
                
                    if 'ICD9:' in str(j['val']):
                        icd = j['val']
                    if 'DOID:' in str(j['val']):  
                        do = j['val']
                    if 'OMIM:' in str(j['val']):  
                        omim = j['val']

                if icd !='':
                    if omim != '':
                        icd_omim[icd]=omim
                    if do != '':
                        icd_do[icd]=do
            else:
                continue  


with open('../data/icd_omim.pkl', 'wb') as handle:
    pkl.dump(icd_omim, handle, protocol=pkl.HIGHEST_PROTOCOL)

with open('../data/icd_do.pkl', 'wb') as handle:
    pkl.dump(icd_do, handle, protocol=pkl.HIGHEST_PROTOCOL)
