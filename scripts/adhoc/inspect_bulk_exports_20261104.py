#!/usr/bin/env python3
"""Inspect served export contents for the unchanged full-corpus download criterion.
Inputs: seven public export URLs. Output: compact field inventories under reviews.
2026-11-04 fleet refresh PR; read-only, no site/repository mutations.
"""
import json
from pathlib import Path
import urllib.request

URLS={
 'CultureMech':'https://culturebotai.github.io/CultureMech/app/recipes.json',
 'CommunityMech':'https://culturebotai.github.io/CommunityMech/communities.json',
 'MediaIngredientMech':'https://culturebotai.github.io/MediaIngredientMech/data/ingredients.json',
 'ProteinTraitsMech':'https://culturebotai.github.io/proteintraitsmech/data/facets.json',
 'DUFMech':'https://culturebotai.github.io/DUFMech/index.json',
 'CMMMech':'https://culturebotai.github.io/CMMMech/pages/index.json',
 'AIMech':'https://culturebotai.github.io/AIMech/pages/index.json'}

def fields(value,depth=0):
    if isinstance(value,dict):return {k:fields(v,depth+1) if depth<1 else type(v).__name__ for k,v in value.items()}
    if isinstance(value,list):return {'length':len(value),'first_item_fields':list(value[0]) if value and isinstance(value[0],dict) else type(value[0]).__name__ if value else None}
    return type(value).__name__

def main():
    out={}
    for mech,url in URLS.items():
        with urllib.request.urlopen(url,timeout=90) as r:data=json.load(r)
        item={'url':url,'structure':fields(data)}
        if mech=='DUFMech':
            item['structure']['metadata']={'records':len(data['metadata']),'PF04149':fields(data['metadata']['PF04149'])}
            item['structure']['summary']={'keys':list(data.get('summary',{}))}
        elif mech=='ProteinTraitsMech':
            item['structure']['counts']={'axes':data['counts']['axis'],'categories':len(data['counts']['cat']),'sources':len(data['counts']['src'])}
            shard=data['shards'][0]
            item['first_shard_descriptor']=shard
            path=shard.get('path',shard.get('url',''))
            if path:
                from urllib.parse import urljoin
                shard_url=urljoin(url,path)
                try:
                    with urllib.request.urlopen(shard_url,timeout=90) as r:content=json.load(r)
                    item['first_shard_structure']=fields(content)
                except Exception as e:item['shard_error']=str(e)
        out[mech]=item
    dest=Path('_fleet/reviews/refresh-20261104/group-b-bulk-inventory.json')
    dest.write_text(json.dumps(out,indent=2)+'\n')
    print(dest)

if __name__=='__main__':main()
