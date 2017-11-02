__author__ = 'root'

from practnlptools.tools import Annotator
from nltk.corpus import wordnet as wn





class PropbankAnnotator:
    """ A propbank annotator that gives arguments A0-A5
    """
    annotator=Annotator()


    def get_person_list_from_ner(self, annotation_list_for_ner):

        if type(annotation_list_for_ner) is not list:
            return []

        print annotation_list_for_ner
        persons_list = []
        tmp_person = ''
        for e in annotation_list_for_ner:
            (tuple_1, tuple_2) = e

            if 'S-PER' in tuple_2:
                persons_list.append(tuple_1)

            elif 'B-PER' in tuple_2 or 'I-PER' in tuple_2:

                tmp_person = tmp_person + ' ' + tuple_1

            elif 'E-PER' in tuple_2:
                tmp_person = tmp_person + ' ' + tuple_1

                persons_list.append(tmp_person.strip())
                tmp_person = ''


        return persons_list

    def retrieve_actors(self, annotation={}):
        actor_list = []

        for event in annotation['events']:
            # print 'original'
            # print event

            persons_list = self.get_person_list_from_ner(annotation['ner'])

            if 'A0' in event and 'A1' in event:
                # verb = event['V']
                # verb_synset = wn.synsets(verb, wn.VERB)
                # print wn.morphy(verb, wn.VERB), verb_synset

                if event['A0'] == '':
                    continue

                if event['A1'] == '' and 'A2' not in event:
                    continue

                for event_key in event:
                    if event_key in ['A0', 'A1', 'A2']:

                        if event_key != 'V':

                            for ner_person in persons_list:
                                if (ner_person in event[event_key]) and (ner_person not in actor_list):
                                    actor_list.append(ner_person)

        return actor_list

    def get_annotate_retrieve_actors(self, sentence):
        annotation = self.annotator.getAnnotations(sentence, dep_parse=True)


        actor_list = []

        for event in annotation['srl']:
            print 'original'
            print event

            persons_list = self.get_person_list_from_ner(annotation['ner'])

            if 'A0' in event and 'A1' in event:
                #verb = event['V']
                #verb_synset = wn.synsets(verb, wn.VERB)
                #print wn.morphy(verb, wn.VERB), verb_synset

                if event['A0'] == '':
                    continue

                if event['A1'] == '' and 'A2' not in event:
                    continue


                for event_key in event:
                    if event_key in ['A0', 'A1', 'A2']:

                        if event_key != 'V':

                            for ner_person in persons_list:
                                if (ner_person in event[event_key]) and (ner_person not in actor_list):
                                    actor_list.append(ner_person)

        return  actor_list


if __name__ == "__main__":
    p = PropbankAnnotator()
    print p.get_annotate_retrieve_actors('PROGRESSOHIO said on Tuesday that he would soon visit China and hoped to also travel to Russia, as he again criticised long-time ally the United States for "arrogance".')