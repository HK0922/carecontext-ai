"""Experimental retriever: BM25 with optional *local* dense embeddings and RRF.

No embedding model is downloaded or called automatically. Pass an explicitly
configured local encoder implementing ``encode(list[str]) -> vectors``.
This module is deliberately not enabled in clinical answer generation until an
independent retrieval evaluation demonstrates an improvement over BM25.
"""
from __future__ import annotations
from collections import Counter
import math
from typing import Protocol
from .retrieval import tokens


class LocalEncoder(Protocol):
    def encode(self, sentences: list[str]) -> list[list[float]]: ...


def _cos(a,b):
    if len(a)!=len(b) or not a:return 0.0
    dot=sum(float(x)*float(y) for x,y in zip(a,b))
    na=math.sqrt(sum(float(v)*float(v) for v in a))
    nb=math.sqrt(sum(float(v)*float(v) for v in b))
    return dot/(na*nb) if na and nb else 0.0


def _lexical(q, sources):
    terms=set(tokens(q));docs=[tokens(source['text']) for source in sources]
    if not docs or not terms:return []
    n=len(docs);avgdl=sum(map(len,docs))/n or 1
    df=Counter(t for d in docs for t in set(d));out=[]
    for source,doc in zip(sources,docs):
        count=Counter(doc);matches=terms&count.keys()
        if not matches:continue
        score=sum(math.log(1+(n-df[t]+.5)/(df[t]+.5))*count[t]*2.2/(count[t]+1.2*(.25+.75*len(doc)/avgdl)) for t in matches)
        out.append((source['source_id'],score))
    return sorted(out,key=lambda p:(-p[1],p[0]))


def retrieve(question:str, sources:list[dict], *, encoder: LocalEncoder | None=None, limit=8, rrf_k=60) -> list[dict]:
    if limit<1 or limit>50:raise ValueError('Invalid retrieval limit')
    if len(sources)!=len(set(s['source_id'] for s in sources)):raise ValueError('Source IDs must be unique')
    lexical=_lexical(question,sources)
    if encoder is None:
        selected=lexical[:limit]
        return [{'source_id':id,'score':round(score,6),'method':'bm25','source':next(s for s in sources if s['source_id']==id)} for id,score in selected]
    # Encoder must operate in-process. A cloud adapter is prohibited for records.
    embeddings=encoder.encode([question]+[s['text'] for s in sources]);assert len(embeddings)==len(sources)+1
    dense=sorted([(s['source_id'],_cos(embeddings[0],v)) for s,v in zip(sources,embeddings[1:])],key=lambda p:(-p[1],p[0]))
    fused={}; origins={}
    for label, ranking in [('bm25',lexical),('dense',dense)]:
        for index,(id,_) in enumerate(ranking):
            fused[id]=fused.get(id,0)+1/(rrf_k+index+1)
            origins.setdefault(id,[]).append(label)
    by_id={s['source_id']:s for s in sources}
    return [{'source_id':id,'score':round(score,9),'method':'rrf','retrieval_paths':origins[id],
             'source':by_id[id]} for id,score in sorted(fused.items(),key=lambda p:(-p[1],p[0]))[:limit]]
