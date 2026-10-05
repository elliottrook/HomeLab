"""Synthetic routing comparison, no execution or authority path."""
import argparse
import collections
import hashlib
import json
import math
import re
from pathlib import Path

CORPUS = Path(__file__).parent/'fixtures/routing-families-v1.json'
ALLOWED = frozenset({'timer','home','media','facts','calendar','web','local_join','lab_read','private_context'})
STOP = frozenset('a an the my me is are was what when who do i am for to on in of and with this that it can could you please help question quick request would like assistant'.split())


def tokens(text):
    return [x for x in re.findall(r'[a-z]+',text.lower()) if x not in STOP]


def proposal(status, labels=()):
    labels = sorted(set(labels))
    if not set(labels) <= ALLOWED or (status != 'plan' and labels):
        raise ValueError('invalid proposed labels')
    return {'status':status,'labels':labels,'authorization':'not-granted','confidence':None}


def rules(text):
    t = set(tokens(text))
    calendar = bool(t & {'calendar','appointments','meetings','free'})
    web = bool(t & {'web','website','online','internet','news','weather','forecast'})
    if calendar and web:
        return proposal('plan',('calendar','web','local_join'))
    groups = [({'timer','countdown'},'timer'),({'lights','lighting'},'home'),
              ({'music','playlist','playback'},'media'),({'film','moon','wrote','released'},'facts'),
              ({'calendar','appointments','meetings','free'},'calendar'),
              ({'web','website','online','internet','news','weather','forecast'},'web'),
              ({'homelab','proxmox','server','doctor'},'lab_read'),
              ({'personal','preferences','prefer','bedtime'},'private_context')]
    labels = [label for words,label in groups if t & words]
    if labels:
        return proposal('plan',labels)
    if t & {'turn','thing','set'}:
        return proposal('clarify')
    return proposal('abstain')


class Nearest:
    def __init__(self, training):
        # One document per independent family; presentation copies do not affect IDF.
        self.training = list(training)
        frequency = collections.Counter(word for row in training for word in set(tokens(row['text'])))
        self.idf = {word:math.log((1+len(training))/(1+count))+1 for word,count in frequency.items()}
        self.vectors = [self.vector(row['text']) for row in training]

    def vector(self,text):
        counts=collections.Counter(tokens(text))
        v={word:count*self.idf[word] for word,count in counts.items() if word in self.idf}
        norm=math.sqrt(sum(x*x for x in v.values()))
        return {k:x/norm for k,x in v.items()} if norm else {}

    def predict(self,text,threshold):
        v=self.vector(text)
        scores=[sum(value*other.get(word,0) for word,value in v.items()) for other in self.vectors]
        best=max(range(len(scores)),key=lambda i:scores[i])
        score=scores[best]
        if score<=threshold:
            return proposal('abstain')
        row=self.training[best]
        return proposal(row['status'],row['required'])


def correct(row,prediction):
    return prediction['status']==row['status'] and prediction['labels']==sorted(row['required'])


def load_corpus():
    d=json.loads(CORPUS.read_text())
    rows=d['families']
    if len({r['id'] for r in rows})!=len(rows) or len({r['text'] for r in rows})!=len(rows):
        raise ValueError('duplicate family or cross-split exact text')
    for r in rows:
        if r['split'] not in {'train','calibration','test'} or not set(r['required'])<=ALLOWED:
            raise ValueError('invalid corpus')
    return d


def evaluate():
    corpus=load_corpus()
    families=corpus['families']
    train=[r for r in families if r['split']=='train']
    calibration=[r for r in families if r['split']=='calibration']
    test=[r for r in families if r['split']=='test']
    model=Nearest(train)
    choices=[]
    for threshold in [0,.1,.2,.3,.4,.5]:
        choices.append((sum(correct(r,model.predict(r['text'],threshold)) for r in calibration),threshold))
    _,threshold=max(choices)
    results={}
    for name,predict in [('rules',rules),('tfidf-nearest',lambda text:model.predict(text,threshold))]:
        rows=[]
        exact=0
        violations=0
        for r in test:
            predictions=[predict(prefix+r['text']) for prefix in corpus['presentation_prefixes']]
            passes=[correct(r,p) for p in predictions]
            exact+=sum(passes)
            violations+=sum(bool(set(p['labels']) & set(corpus['forbidden_for_all'])) for p in predictions)
            rows.append({'family_id':r['id'],'all_variants_exact':all(passes),
                         'variants_exact':sum(passes),'variants':len(passes),'prediction':predictions[0],
                         'presentation_invariant':all(p==predictions[0] for p in predictions)})
        results[name]={'family_exact':sum(r['all_variants_exact'] for r in rows),'family_count':len(test),
                       'example_exact':exact,'example_count':len(test)*len(corpus['presentation_prefixes']),
                       'prohibited_label_violations':violations,'families':rows}
    return {'schema_version':'routing-smoke.v1','dataset_digest':'sha256:'+hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
            'evaluator_digest':'sha256:'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'family_split_counts':{split:sum(r['split']==split for r in families) for split in ['train','calibration','test']},
            'total_examples':len(families)*len(corpus['presentation_prefixes']),
            'threshold':threshold,'calibration_choices':[{'family_exact':n,'threshold':t} for n,t in choices],
            'results':results,'decision':'no-production-adoption','limits':[
                'author-labelled synthetic data, not human gold', 'ten independent test families, not 100 independent examples',
                'corpus and rule baseline authored in same session; design bias possible',
                'lexical similarity is not calibrated confidence','labels cannot authorize execution']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=evaluate()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{'family_exact':v['family_exact'],'family_count':v['family_count']} for k,v in result['results'].items()}))
