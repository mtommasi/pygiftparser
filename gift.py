#!/usr/bin/python3
import logging
import re

reSepQuestions=re.compile('^\s*$')
reComment=re.compile('^//.*$')
reCategory=re.compile('^\$CATEGORY: (?P<cat>[/\w$]*)')
# Title supposed to be at the begining of a line
reTitle=re.compile('^::(?P<title>.*?)::(?P<text>.*)$',re.M+re.S)
reFormat=re.compile('^.*\[(?P<format>.*?)\](?P<text>.*)',re.M+re.S)
reAnswer=re.compile('^(?P<head>.*[^\\\\]){(?P<answer>.*[^\\\\]?)}(?P<tail>.*)',re.M+re.S)

# Sub regular expressions
OPTIONALFEEDBACK='(#(?P<feedback>[^=~#]*))?'
OPTIONALFEEDBACK2='(#(?P<feedback2>[^=~#]*))?'

# numeric answers
reAnswerNumeric=re.compile('^#')
reAnswerNumericValue = re.compile('\s*(?P<value>[\d.,]+)(:?P<tolerance>[\d.,]+)?'+OPTIONALFEEDBACK)
reAnswerNumericInterval=re.compile('\s*(?P<min>[\d.]+)..(?P<max>[\d.,]+)'+OPTIONALFEEDBACK)

# Multiple choices only ~ symbols
reAnswerMultipleChoices = re.compile('\s*(?P<sign>=|~)(%(?P<fraction>-?[\d.]+)%)?(?P<answer>[^#=~]*)'+OPTIONALFEEDBACK)

# True False
reAnswerTrueFalse = re.compile('^\s*(?P<answer>(T(RUE)?)|(F(ALSE)?))'+OPTIONALFEEDBACK+OPTIONALFEEDBACK2)

# Match (applies on 'answer' part of the reAnswerMultipleChoices pattern
reMatch = re.compile('(?P<question>.*)->(?P<answer>.*)')

def stripMatch(match,s):
    if match.group(s):
        return match.group(s).strip()
    else:
        return ""

############# Sets of answers ###############
# Can be a singleton, empty or not or just the emptyset!

class AnswerSet:
    def __init__(self,question):
        self.question = question
        self.alid = True
        
    def myprint(self):
        print (self.__class__)

class Essay(AnswerSet):
    """ Empty answer """
    def __init__(self,question):
        AnswerSet.__init__(self,question)

class Description(AnswerSet):
    """ Emptyset, nothing!"""
    def __init__(self,question):
        AnswerSet.__init__(self,question)

class TrueFalseSet(AnswerSet):
    """ True or False"""
    # Q: should I introduce Answer variables?
    def __init__(self,match):
        AnswerSet.__init__(self,question)
        self.answer = match.group('answer').startswith('T')
        self.feedbackWrong = stripMatch(match,"feedback")
        self.feedbackCorrect = stripMatch(match,"feedback2")
        
    def myprint(self):
        print (">TrueFalse:",self.answer,"--",self.feedbackWrong,"--",self.feedbackCorrect)
        
class SingleNumericAnswer(AnswerSet):
    """ """
    def __init__(self,question,answer):
        AnswerSet.__init__(self,question)
        match = reAnswerNumericValue.match(answer)
        if match:
            self.value = float(match.group('value'))
            if match.group('tolerance'):
                self.tolerance = float( match.group('tolerance') )
        else:
            match = reAnswerNumericInterval.match(answer)
            if match:
                self.mini = match.group('min')
                self.maxi = match.group('max')
            else:
                self.valid = False
                 
class ChoicesSet(AnswerSet):
    """ One or many choices in a list"""
    def __init__(self,question,answers):
        AnswerSet.__init__(self,question)
        self.answers = answers

    def myprint(self):
        print ("Answers :")
        for a in self.answers:
            a.myprint()
            print ('~~~~~')

class ShortSet(ChoicesSet):
    def __init__(self,question,answers):
        ChoicesSet.__init__(self,question,answers)

class SelectSet(ChoicesSet):
    """ One  choice in a list"""
    def __init__(self,question,answers):
        ChoicesSet.__init__(self,question,answers)

class MultipleChoicesSet(ChoicesSet):
    """ One or more choices in a list"""
    def __init__(self,question,answers):
        ChoicesSet.__init__(self,question,answers)

    def checkValidity(self):
        """ Check validity the sum f fractions should be 100 """
        return sum([ a.fraction for a in self.answers if a.fraction>0]) == 100

################# Single answer ######################
class Answer:
    """ one answer in a list"""
    def __init__(self,match):
        if not match : return
        self.answer = match.group('answer').strip()
        self.feedback = stripMatch(match,"feedback")
        # At least one = sign => selects (radio buttons)
        self.select = match.group('sign') == "="

        # fractions
        if match.group('fraction') :
            self.fraction=float(match.group('fraction'))
        else: 
            if match.group('sign') == "=":
                self.fraction = 100
            else:
                self.fraction = 0
    
        # matching
        match = reMatch.match(self.answer)
        self.isMatching = match != None
        if self.isMatching:
            self.answer = match.group('answer')
            self.question = match.group('question')

    def myprint(self):
        for key, val in self.__dict__.items():
            print ('>',key,':',val)
        

############ Questions ################
                
class Question:
    """ Question class.

    About rendering: It is up to you! But it mostly depends on the type of the answer set. Additionnally if it has a tail and the answerset is a ChoicesSet, it can be rendered as a "Missing word". 
    """
    def __init__(self,source,full,cat):
        """ source of the question without comments and with comments"""
        self.full = full
        self.category = cat
        self.valid = True
        self.__parse(source)
        
    def __parse(self,source):
        # split according to the answer
        match = reAnswer.match(source)
        if not match:
            # it is a description
            self.answers = Description(None)
            self.__parseHead(source)
        else: 
            self.tail=stripMatch(match,'tail') 
            self.__parseHead(match.group('head'))
            self.__parseAnswer(match.group('answer'))
        
    def __parseHead(self,head):
        # find the title and the type of the text
        match = reTitle.match(head)
        if match:
            self.title = match.group('title').strip()
            textFormat = match.group('text')
        else:
            self.title = head[:20] # take 20 first chars as a title
            textFormat = head
            
        match = reFormat.match(textFormat)
        if match:
            self.format = match.group('format').lower()
            self.text = match.group('text')
        else:
            self.format = 'moodle'
            self.text = textFormat

    

    def __parseAnswer(self,answer):
        # Essay
        if answer=='':
            self.answers = Essay(self)
            return

        # True False
        match = reAnswerTrueFalse.match(answer)
        if match:
            self.answers = TrueFalseSet(self,match)
            return

        # Numeric answer
        numeric = False
        self.numeric = reAnswerNumeric.match(answer) != None

        #  answers with choices and short answers (TODO short easy)
        answers=[]
        select = False
        short = True
        matching = True
        for match in reAnswerMultipleChoices.finditer(answer):
            a = Answer(match)
            # one = sign is a select question
            if a.select: select = True
            # short answers are only = signs without fractions
            short = short and a.select and a.fraction == 100
            matching = matching and short and a.isMatching
            answers.append(a)
        if len(answers) > 0 :
            if short:
                self.answers = ShortSet(self,answers)
            if select:
                self.answers = SelectSet(self,answers)
            else:
                self.answers = MultipleChoicesSet(self,answers)
                self.valid = self.answers.checkValidity() #TODO
        elif self.numeric :
            # is it a single numerical answer?
            self.answers = SingleNumericAnswer(self,answer)
        else:
            # not a valid question  ?
            self.valid = False

    def myprint(self):
        print ("=========Question=========")
        if not self.valid:
            return
        print (self.answers.__class__)
        for key, val in self.__dict__.items():
            if key in ['full','source',"answer","valid"]:
                continue
            if key == 'answers':
                self.answers.myprint()
            else:
                print (key,':',val)
        
def parseFile(f):
    cleanedSource = fullSource = ""
    category='$course$'
    newCategory = None
    questions=[]
    
    for  line in f:
        if reSepQuestions.match(line):
            if newCategory:
                # the previous line was a category declaration
                category = newCategory
                newCategory = None
            else:
                if cleanedSource != "":
                    # this is the end of a question
                    questions.append(Question(cleanedSource,fullSource,category))
                cleanedSource = fullSource = ""
        else:
            # it is not a blank line : is it a category definition?
            match = reCategory.match(line)
            if match:
                newCategory = match.group('cat')
                continue
            
            # is it a comment ?
            if not reComment.match(line):
                cleanedSource += line
            fullSource+=line

    if cleanedSource != "":
        questions.append(Question(cleanedSource,fullSource,category))

    return questions


if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(description="Parses gift files.")
    parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level", default='WARNING')
    parser.add_argument('f', help="gift file",type=argparse.FileType('r'))
    args = parser.parse_args()
    logging.basicConfig(filename='gift.log',filemode='w',level=getattr(logging, args.logLevel))

    questions = parseFile (args.f)
    args.f.close()

    for q in questions:
        q.myprint()
