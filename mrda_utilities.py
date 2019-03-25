import os
import pickle
import re
import string

import spacy
from spacy.tokenizer import Tokenizer
nlp = spacy.load('en')
tokenizer = Tokenizer(nlp.vocab)


class Dialogue:
    def __init__(self, transcript_id, num_utterances, utterances):
        self.conversation_id = transcript_id
        self.num_utterances = num_utterances
        self.utterances = utterances

    def to_string(self):
        return str("Conversation: " + self.conversation_id + "\n"
                   + "Number of Utterances: " + str(self.num_utterances))


class Utterance:
    def __init__(self, speaker, text, da_label):
        self.speaker = speaker
        self.text = text
        self.da_label = da_label

    def to_string(self):
        return str(self.speaker + " " + self.text + " " + self.da_label)


def process_transcript(transcript, database, excluded_chars=None, excluded_tags=None):

    # Process each utterance in the transcript and create list of Utterance objects
    utterances = []
    for utt_index in range(len(transcript)):

        # Process the utterance text
        # Split on comma to get text from Original CSV Transcription
        text = transcript[utt_index].split(',')[1]

        # If text is allcaps i.e. 'DIGIT_TASK' then ignore
        if text.isupper():
            continue

        # Tokenise
        utterance_tokens = tokenizer(text)

        # Remove the word annotations and filter_disfluency
        utterance_text = []
        for word in utterance_tokens:
            word = word.text
            # If no excluded characters are present just add it
            if all(char not in excluded_chars for char in word):
                utterance_text.append(word)
            # Else, to keep hyphenated words, check 1st, last and 2nd-to-last char for interruptions (i.e. 'spi-,')
            elif len(word) > 1:
                if word[0] not in excluded_chars and word[-1] not in excluded_chars and word[-2] not in excluded_chars:
                    utterance_text.append(word)

        # Check utterance is not only punctuation (because the rest was invalid/removed)
        if len(utterance_text) == 1 and any(char in ['.', '?', '!'] for char in utterance_text[0]):
            # If so, ignore
            continue
        # Else if the last token is punctuation, concatenate with last word
        elif len(utterance_text) > 1 and any(char in ['.', '?', '!'] for char in utterance_text[-1]):
            if len(utterance_text[-2]) > 0:
                utterance_text[-2] = ''.join((utterance_text[-2], utterance_text[-1]))
                utterance_text.pop()


        # Join words for complete sentence
        utterance_text = " ".join(utterance_text)
        # Strip leading and trailing whitespace
        utterance_text.strip()

        # TODO Concatenate multi-utterance's with '+' label

        # Process the utterance dialogue act, adjacency pair and speaker
        # Get the dialogue act from the database file
        da_tag = database[utt_index].split(',')[5]  # TODO Split DA on '.'?

        # # Get the adjacency pair (if it exists) TODO Add AP?
        # adjacency_pair = database[utt_index].split(',')[9]
        # # Convert AP to a more friendly format
        # if len(adjacency_pair) > 0:
        #     # Split AP labels into number and characters
        #     ap_split = re.findall(r'[A-Za-z]|-?\d+\.\d+|\d+', adjacency_pair)

        # Get the speaker label
        speaker = database[utt_index].split(',')[7]

        # Print original and processed utterances
        # print(str(utt_index) + " " + utterance_tokens)
        # print(str(utt_index) + " " + speaker + " " + utterance_text + " " + da_tag)

        # Check we are not adding an empty utterance (i.e. because it was just 'DIGIT_TASK'),
        # or adding an utterance with an excluded tag.
        if len(utterance_text) > 0 and da_tag not in excluded_tags:

            # Create Utterance and add to list
            current_utt = Utterance(speaker, utterance_text, da_tag)
            utterances.append(current_utt)

    # Create Dialogue
    transcript_id = transcript[0].split('-')[0]
    dialogue = Dialogue(transcript_id, len(utterances), utterances)

    return dialogue


def load_data(path, verbose=True):
    with open(path, "r") as file:
        # Read a line and strip newline char
        lines = [line.rstrip('\r\n') for line in file.readlines()]
    if verbose:
        print("Loaded data from file %s." % path)
    return lines


def save_data_pickle(path, data, verbose=True):
    file = open(path, "wb")
    pickle.dump(data, file, protocol=2)
    file.close()
    if verbose:
        print("Saved data to file %s." % path)


def dialogue_to_file(path, dialogue, utterance_only, write_type):
    if utterance_only:
        path = path + "_utt"
    with open(path + ".txt", write_type) as file:
        for utterance in dialogue.utterances:
            if utterance_only:
                file.write(utterance.text.strip() + "\n")
            else:
                file.write(utterance.speaker + "|" + utterance.text.strip() + "|" + utterance.da_label + "\n")


def remove_file(data_dir, file, utterance_only):
    # Remove either text or full versions
    if utterance_only:
        if os.path.exists(data_dir + file + "_utt" + ".txt"):
            os.remove(data_dir + file + "_utt" + ".txt")
    else:
        if os.path.exists(data_dir + file + ".txt"):
            os.remove(data_dir + file + ".txt")