"""Official MOST service for known bodies. No orbit is invented from two clicks."""
import hashlib
import math
from datetime import date

import numpy as np
from astroquery.ipac.irsa.most import MostClass


def search_moving(name,start_date,end_date):
    start,end=date.fromisoformat(start_date),date.fromisoformat(end_date)
    if end<start or (end-start).days>31:raise ValueError('Wybierz przedział od 0 do 31 dni.')
    client=MostClass();client.TIMEOUT=90
    try:
        table=client.query_object(catalog='spherex',input_mode='name_input',obj_name=name,
                                  obs_begin=start_date,obs_end=end_date,output_mode='Brief',with_tarballs=False)
    except Exception as exc:
        response=getattr(exc,'response',None)
        if response is not None and response.status_code==400:
            raise ValueError('MOST odrzucił nazwę lub zakres. Przy niejednoznacznej nazwie użyj identyfikatora NAIF, np. 20000001:NID dla Ceres. '+response.text[:1400]) from exc
        raise
    rows=[]
    if table is not None:
        for row in table[:500]:
            values={}
            for key in table.colnames:
                value=row[key]
                if np.ma.is_masked(value):values[key]=None
                elif isinstance(value,(np.floating,float)):
                    values[key]=float(value) if math.isfinite(value) else None
                elif isinstance(value,(np.integer,int)):values[key]=int(value)
                elif isinstance(value,bytes):values[key]=value.decode('utf-8',errors='replace')
                else:values[key]=str(value)
            rows.append(values)
    return dict(kind='most',object=name,start_date=start_date,end_date=end_date,catalog='spherex',rows=rows,
                count=0 if table is None else len(table),truncated=table is not None and len(table)>500,
                source='https://irsa.ipac.caltech.edu/applications/MOST/',
                limitations=['Wyszukiwanie wykorzystuje efemerydy znanego obiektu. Nie potwierdza jego detekcji w zdjęciu.',
                             'Nie wyszukuje nieznanej Planet Nine i nie dopasowuje orbity do ręcznej trasy.',
                             'Limit zapytania: 31 dni; wyświetlamy do 500 rekordów. Wynik zależy od dostępności danych w MOST.'])
