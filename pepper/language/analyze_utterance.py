from __future__ import unicode_literals

from nltk.corpus import wordnet
from nltk.stem.porter import *
from nltk import word_tokenize
from nltk.tag import StanfordNERTagger
import spacy

import wolframalpha

import json
import os


# certain, uncertain, possible, probable
ROOT = os.path.join(os.path.dirname(__file__))
ner = StanfordNERTagger(os.path.join(ROOT, 'stanford-ner', 'english.muc.7class.distsim.crf.ser'),
                        os.path.join(ROOT, 'stanford-ner', 'stanford-ner.jar'), encoding='utf-8')

json_dict = json.load(open(os.path.join(ROOT, 'dict.json')))

client = wolframalpha.Client('LA3GP6-VJ8KK8Y36A')
stemmer = PorterStemmer()

print("HELLO UTTERANCE")

grammar = json_dict["grammar"]
names = ['selene', 'bram', 'leolani', 'piek','selene']
people = [{'name': 'selene', 'lastname':'baez','gender': 'f', 'from': 'mexico', 'likes': 'monster inc.', 'knows': ['bram', 'piek']},
          {'name': 'selene', 'lastname':'koleman','from':'netherlands'},
              {'name': 'bram', 'gender': 'm', 'from': 'netherlands', 'likes': 'terminator', 'knows': ['selene']},
              {'name': 'leolani', 'gender': 'f', 'from': 'france', 'movies': -1, 'knows': names, 'visited': 'netherlands',
               'likes':'computers'}]

def get_synonims(word):
    syns = wordnet.synsets(word)
    for s in syns:
        print(word+' - ' + s.lemmas()[0].name() + ': ' + s.definition())
        print(s.lemmas()[0].antonyms())

def analyze_question(speaker, words, pos_list):
    ambig = 0
    morphology = {}
    to_be = ''
    main_verb = ''
    say = ''
    response = {}

    rdf_subject = ''
    rdf_predicate = ''
    rdf_object = ''

    question_word = words[0].lower().strip()

    # SETTING THE RESPONSE TYPE
    if question_word in grammar["question words"]:
        response['type'] = grammar["question words"][question_word]["response"]
    elif pos_list[0][1].startswith('VB'):
        to_be = question_word
        response['type'] = 'bool'
    if pos_list[0][0].lower() == 'have' or words[2].lower().strip() == 'ever':
        response['type'] += '-frequency'
   # print('because the question word is '+question_word+', response type is '+response['type'])

    # EXTRACTING THE MAIN VERB AND TO BE
    for pos in pos_list[1:]:
        if pos[0] not in names:
            if pos[0].lower() in grammar['to be'] and to_be=='':
                to_be=pos[0]
                morphology["tense"] = grammar['to be'][to_be]['tense']
                if 'person' in grammar['to be'][to_be]:
                    morphology['person'] = grammar['to be'][to_be]['person']
            if pos[1].startswith('VB'):
                main_verb = pos[0]
   # print('be: ' + to_be + ', verb:' + main_verb)
    if main_verb.endswith('ing'):
        morphology['duration'] = 'continuous'
    if main_verb.endswith('d'):
        morphology['duration'] = 'done'


    # FINDING THE SUBJECT OF THE SENTENCE
    # TODO DEALING WITH LASTNAMES
    subject = list()
    if question_word == 'have':
        subject.append(words[1])
    else:
        subject.append(words[words.index(to_be) + 1])


    if subject[0] in grammar['pronouns']:
        morphology['pronoun_info'] = grammar['pronouns'][subject[0]]
        if subject[0] == 'i':
            subject.append(speaker)
        elif subject[0] == 'you':
            subject.append('leolani')
        else: #PRONOUN COREFERENCE RESOLUTION
            say+='I am not sure which '+subject[0]+' you think '
            ambig = 1

     #  print('subject: ' + str(subject))

    #FINDING THE OBJECT OF THE SENTENCE
    obj = words[words.index(main_verb) + 1:]
    if obj:
      #  print('obj: ' + str(obj))
        if obj[0] == 'your':
            obj = words[3].lower().strip()
            subject = 'my ' + obj
            if obj in people[len(people)-1].keys():
                # WHAT IS YOUR X
                say += subject+' '+to_be+ ' '+ people[len(people)-1][obj]

    if obj[0] in grammar['pronouns']:
        pr = obj[0]
        morphology['obj pronoun'] = grammar['pronouns'][pr]
        if pr in ['me','I']:
            obj[0] = speaker
        elif pr=='you':
            obj[0] = 'leolani'
        else:
            say = ' which '+obj[0]+' you mean?'
            ambig = 1

    # WHERE IS X FROM / WHERE ARE YOU FROM / WHO IS FROM X
    if 'from' in words:
        rdf_predicate = 'is_from'
        if question_word=='where':
            rdf_object = 'LOCATION'
        if question_word=='who':
            rdf_subject = 'PERSON'
            if words[words.index('from')+1]:
                rdf_object = words[words.index('from')+1]
        for person in people:
            if person['name'] in subject:
                subject = person['name']
                #if names.count(person['name'])>1 and 'lastname' in person.keys():
                #    subject+=' '+person['lastname']+' '
                rdf_subject = subject
                if person['name'] == 'leolani':
                    subject = ' I '
                    to_be = 'am'
                if 'from' in person.keys():
                    say += ' '+subject+' '+to_be + " " + 'from' + ' ' + person['from']
                else:
                    say += "I don't know"+question_word+' '+person['name']+' '+to_be+ ' from'
        print('RDF ',rdf_subject, rdf_predicate, rdf_object)

    # DOES X KNOW Y / HAS X MET Y / DO YOU KNOW Y
    if (stemmer.stem(main_verb) =='know' or main_verb=='met') and ambig == 0:
        rdf_predicate = 'knows'
        rdf_object = obj[0]
        rdf_subject = 'PERSON'
        for s in subject:
            if s in names:
                rdf_subject = s
                if s =='leolani':
                    if obj[0] in people[len(people)-1]['knows']:
                        to_be = ''
                    else:
                        if to_be == 'have':
                            to_be += ' not'
                        else:
                            main_verb += ' not '
                    if obj[0]==speaker:
                        obj[0] = 'you, '+speaker
                    say += 'I '+to_be+' '+main_verb+' '+obj[0]
                else:
                    for person in people:
                        if person['name']==s:
                            if speaker == 'person':
                                speaker = ''
                            else:
                                speaker+=' '
                            if 'knows' in person.keys() and obj[0] in person['knows']:
                                say += 'yes, '+speaker+s+' knows '+obj[0]
                            else:
                                say += ' no, '+speaker+s+ ' '+to_be +' not '+main_verb+' '+obj[0]
        print('RDF triple:',rdf_subject,rdf_predicate,rdf_object)

    if names.count(subject[0])>1 or names.count(obj[0])>1:
        print('I know two people with that name')
        ambig = 1
        for word in say.split(' '):
            if names.count(word)>1:
                for person in people:
                    if person['name']==word and 'lastname' in person.keys():
                        print(word+' '+person['lastname'])
                break

   # print('response info: ' + str(response))
   # print('extracted morphological info: ' + str(morphology))
    if say:
        print('response:'+say)
        return(say)
    else:
        print(str(subject) + " " + to_be + " " + main_verb + "..." + response["type"] + ' ' + str(obj))
        return('i got confused')


def analyze_statement(speaker, words, pos_list):

    rdf = {'subject': 'SUBJECT', 'predicate': 'PREDICATE', 'object': 'OBJECT'}

    morphology={}
    to_be=''
    main_verb=''
    subject=[]
    say = ''

    for pos in pos_list[1:]:
        if pos[0] not in names:
            if pos[0].lower() in grammar['to be'] and to_be=='':
                to_be=pos[0]
                morphology["tense"] = grammar['to be'][to_be]['tense']
                if 'person' in grammar['to be'][to_be]:
                    morphology['person'] = grammar['to be'][to_be]['person']
            if (pos[1].startswith('VB') or pos[0] in grammar['verbs']) and main_verb=='':
                main_verb = pos[0]
    print('be: ' + to_be + ', verb:' + main_verb)
    if main_verb.endswith('ing'):
        morphology['duration'] = 'continuous'
    if main_verb.endswith('d'):
        morphology['duration'] = 'done'
    print(morphology)

    if pos_list[0][1].startswith('PRP') or pos_list[0][0] in names:
        #if main_verb in ['know','think']:
        if to_be!='':
            subject.append(words[words.index(to_be)-1])
        else:
            subject.append(pos_list[0][0])
        if pos_list[0][0] in grammar['pronouns']:
            morphology['pronoun_info']=grammar['pronouns'][pos_list[0][0]]
            if morphology['pronoun_info']['person'] == 'first':# and main_verb not in ['think','assume','believe']:
                subject.append(speaker)
            if morphology['pronoun_info']['person'] == 'second':
                subject.append('leolani')
        if subject[0].lower() == 'my':
            subject.append(speaker)
            if subject[0] in names:
                subject.append(subject[0]+'\'s '+ pos_list[1][0])
            else:
                subject.append('your '+pos_list[1][0])
            #subject.pop(0)
        #else:
        #    subject.append(pos_list[0][0]+' '+pos_list[1][0])

    obj = ''
    for word in words[words.index(main_verb) + 1:]: #FIX
        obj+=' '+word
    if obj:
        rdf['predicate'] = main_verb
        #  print('obj: ' + str(obj))
        if obj[0] == 'your':
            obj = words[3].lower().strip()

    if len(pos_list)>2 and pos_list[2][0]=='from':
        rdf['predicate'] = 'is_from'
        if subject[len(subject)-1] in names:
            for person in people:
                if person['name'] == subject[len(subject)-1]:
                    if 'from' in person.keys():
                        print("i thought "+person['name'] +' is from '+person['from'])

    # knows person, studies at, works at, lives_in, visited, likes, dislikes
    # working with plural

    for sub in subject:
        if sub in names or sub == 'person':
            rdf['subject'] = sub
    if obj:
        rdf['object']=''
        for o in obj:
            if o !='from':
                rdf['object'] = rdf['object'] + ' ' + o

    print('RDF TRIPLE:', str(rdf))

    if stemmer.stem(main_verb) =='like':
        if subject[len(subject) - 1] in names:
            for person in people:
                if person['name'] == subject[len(subject) - 1]:
                    if 'likes' in person.keys():
                        print('looking up '+person['name'])
                        if subject[0]=='i':
                            say+='i have heard you like '+person['likes']+' '

                        else:
                            say+="i have heard " + person['name'] + ' likes ' + person['likes']+' '

    print('subject: '+str(subject))

    if main_verb in ['know', 'like', 'live'] and morphology['pronoun_info']['person'] == 'third':
        main_verb = main_verb + 's'

    if len(subject)>0:
        say+=subject[len(subject)-1]+' '+main_verb + ' '+str(obj)
    else:
        say+='i got confused' #unknown sentence


    return say

#["you live in the closet","person"],["i am from serbia","lenka"], ["a rabbit bit me", "selene"],
#              ["What did you do", "person"], ["How are you", "person"], ["Where is she going", "person"]
# ["How are you feeling", "person"],['What are you doing', 'person'],

statements = [['Does selene know piek', 'bram'],['who is from italy?','jill'],
            ['Where is Selene from', 'person'], ['Have you ever been to Canada', 'person'],
             ['where are you from', 'person'], ['Do you like people','person'],
             ['What is your name', 'person'], ['Have you ever met Michael Jordan?', 'piek'], ['Has Selene ever met piek', 'person'],
             ['Does bram know Beyonce', 'person'], ['Do you know me','bram'],['Do you know him','bram'],
              ['My name is lenka', 'person'], ['piek is from the Netherlands', 'bram'],
              ['i like action movies', 'bram'],
              ['bram likes romantic movies', 'selene'], ['bram is from Italy', 'selene'],
              ['i think sel is from mexico', 'jo']]  # [question, speaker]

# for st in statements:
def analyze_utterance(utterance, speaker):
    print('--------------------------------------------------------')
    print('utterance: '+utterance+', speaker: '+speaker)
    words = utterance.lower().split(" ")
    nlp = spacy.load('en')
    doc = nlp(utterance)
    pos_list = []

    recognized_entities = {'stanford':[],'spacy':[]}

    tok = word_tokenize(utterance)

    ner_text = ner.tag(tok)
    for n in ner_text:
        if n[1]!='O':
            #print('stanford NER: '+str(n))
            recognized_entities['stanford'].append(n)

    for ent in doc.ents:
        #print('spacy NER: ',ent.text, ent.start_char, ent.end_char, ent.label_)
        recognized_entities['spacy'].append([ent,ent.label_])

    i = 0
    for el in recognized_entities['stanford']:
        if len(recognized_entities['stanford']) > i+1 and el[1]==recognized_entities['stanford'][i+1][1]:
            recognized_entities['stanford'].append([el[0] + ' '+recognized_entities['stanford'][i+1][0],el[1]])
            recognized_entities['stanford'].remove(recognized_entities['stanford'][i+1])
            recognized_entities['stanford'].remove(el)
        i+=1

    for el in recognized_entities['stanford']:
        if el[1]=='LOCATION':
            q = 'Where is '+el[0]
            print(q)

        elif el[1] == 'PERSON':
            q = 'Who is '+el[0]
            print(q)

        #res = client.query(q)
        #print(res)
        #for r in res.results:
        #    print(r.text())

    print(recognized_entities)

    for token in doc:
        pos_list.append([token.text, token.tag_])
    print(pos_list)

    if pos_list[0][1] in ['WP', 'WRB','VBZ','VBP']:
        return analyze_question(speaker, words, pos_list)
    else:
        return analyze_statement(speaker, words, pos_list)


for stat in statements:
    print('LEOLANI SAYS: '+analyze_utterance(stat[0],stat[1]))