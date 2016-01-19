#!/usr/bin/python3
import logging
import re
import yattag
import i18n
import sys
_ = i18n.language.gettext

# TODOS:
# - unittest
# - numerical answers in a list
# - new lines \n in headings etc...

# Sub regular expressions
OPTIONALFEEDBACK='(#(?P<feedback>[^=~#]*))?'
OPTIONALFEEDBACK2='(#(?P<feedback2>[^=~#]*))?'
GENERALFEEDBACK='(####(?P<generalfeedback>.*))?'
ANYCHAR='([^\\\\#=~]|\\\\.)'
NUMERIC='[\d]+(\.[\d]+)?'

# Regular Expressions 
reSepQuestions=re.compile('^\s*$')
reComment=re.compile('^//.*$')
reCategory=re.compile('^\$CATEGORY: (?P<cat>[/\w$]*)')

# Heading
# Title is supposed to be at the begining of a line
reTitle=re.compile('^::(?P<title>.*?)::(?P<text>.*)$',re.M+re.S)
reMarkup=re.compile('^.*\[(?P<markup>.*?)\](?P<text>.*)',re.M+re.S)
reAnswer=re.compile('^(?P<head>.*[^\\\\]){(?P<answer>.*?[^\\\\]?)'+GENERALFEEDBACK+'}(?P<tail>.*)',re.M+re.S)

# numeric answers
reAnswerNumeric=re.compile('^#')
reAnswerNumericValue = re.compile('\s*(?P<value>'+NUMERIC+')(:(?P<tolerance>'+NUMERIC+'))?'+OPTIONALFEEDBACK)
reAnswerNumericInterval=re.compile('\s*(?P<min>'+NUMERIC+')(\.\.(?P<max>'+NUMERIC+'))?'+OPTIONALFEEDBACK)

# Multiple choices only ~ symbols
reAnswerMultipleChoices = re.compile('\s*(?P<sign>=|~)(%(?P<fraction>-?[\d.]+)%)?(?P<answer>([^\\\\#=~]|\\\\.)*)'+OPTIONALFEEDBACK)

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
        self.valid = True
        
    def myprint(self):
        print (self.__class__)

class Essay(AnswerSet):
    """ Empty answer """
    def __init__(self,question):
        AnswerSet.__init__(self,question)

    def toHTML(self, doc, full):
        with doc.tag('textarea',name=self.question.getId(),placeholder=_('Your answer here')):
            doc.text('')
        
class Description(AnswerSet):
    """ Emptyset, nothing!"""
    def __init__(self,question):
        AnswerSet.__init__(self,question)

    def toHTML(self,doc, full):
        return
    
class TrueFalseSet(AnswerSet):
    """ True or False"""
    # Q: should I introduce Answer variables?
    def __init__(self,question,match):
        AnswerSet.__init__(self,question)
        self.answer = match.group('answer').startswith('T')
        self.feedbackWrong = stripMatch(match,"feedback")
        self.feedbackCorrect = stripMatch(match,"feedback2")
        
    def myprint(self):
        print (">TrueFalse:",self.answer,"--",self.feedbackWrong,"--",self.feedbackCorrect)

    def toHTML(self,doc, full):
        with doc.tag('ul'):
            with doc.tag('li'):
                doc.input(name = self.question.getId(), type = 'radio', value = True)
                doc.text(_('True'))
            with doc.tag('li'):
                doc.input(name = self.question.getId(), type = 'radio', value = False)
                doc.text(_('False'))
        if full:
            if self.feedbackCorrect :
                with doc.tag('div', klass='answerFeedback'):
                    with doc.tag('div', klass='answerCorrectFeedback'):
                        doc.text(markupRendering(self.feedbackCorrect,self.question.markup))
            if self.feedbackWrong :
                with doc.tag('div', klass='answerWrongFeedback'):
                    doc.text(markupRendering(self.feedbackWrong,self.question.markup))

        
class SingleNumericAnswer(AnswerSet):
    """ """
    def __init__(self,question,answer):
        AnswerSet.__init__(self,question)
        self.answers = []
        match =reAnswerNumericValue.match(answer)
        if match:
            a = NumericAnswer(match)
            self.answers.append(a)
            self.feedback = stripMatch(match,"feedback")
        else:
            match = reAnswerNumericInterval.match(answer)
            if match:
                a = NumericAnswerMinMax(match)
                self.feedback = stripMatch(match,"feedback")
                self.answers.append(a)
            else :
                self.valid = False

    def toHTML(self,doc, full):
        doc.input(name = self.question.getId(), type = 'number')
        if full:
            with doc.tag('div', klass='answerFeedback'):
                with doc.tag('div', klass='answerFeedback'):
                    doc.text(markupRendering(self.feedback,self.question.markup))

class MatchingSet(AnswerSet):
    """  a mapping (list of pairs) """
    def __init__(self,question,answers):
        AnswerSet.__init__(self,question)
        self.answers = answers
        self.possibleAnswers = [a.answer for a in self.answers]

    def checkValidity(self):
        valid = True
        for a in self.answers:
            valid = valid and a.isMatching
        return valid
    
    def myprint(self):
        print ("Answers :")
        for a in self.answers:
            a.myprint()
            print ('~~~~~')

    def toHTML(self,doc, full):
        with doc.tag('table'):
            for a in self.answers:
                with doc.tag('tr'):
                    with doc.tag('td'):
                        doc.text(a.question)
                    with doc.tag('td'):
                        # should be distinct to _charset_ and isindex,...
                        n = self.question.getId() + a.question
                        with doc.tag('select', name= n):
                            for a in self.possibleAnswers:
                                with doc.tag('option'):
                                    doc.text(a)
        if full:
            #TODO!!
            pass
        
    
class ChoicesSet(AnswerSet):
    """ One or many choices in a list (Abstract)"""
    def __init__(self,question,answers):
        AnswerSet.__init__(self,question)
        self.answers = answers

    def myprint(self):
        print ("Answers :")
        for a in self.answers:
            a.myprint()
            print ('~~~~~')

                    

class ShortSet(ChoicesSet):
    """ A single answer is expected but several solutions are possible """ 
    def __init__(self,question,answers):
        ChoicesSet.__init__(self,question,answers)

    def toHTML(self,doc, full):
        doc.input(name=self.question.getId(), type = 'text')
                

class SelectSet(ChoicesSet):
    """ One  choice in a list"""
    def __init__(self,question,answers):
        ChoicesSet.__init__(self,question,answers)

    def toHTML(self,doc, full):
        with doc.tag('select', name=self.question.getId()):
            for a in self.answers:
                with doc.tag('option'):
                    doc.text(a.answer)
        if full:
            #TODO!!
            pass

class MultipleChoicesSet(ChoicesSet):
    """ One or more choices in a list"""
    def __init__(self,question,answers):
        ChoicesSet.__init__(self,question,answers)

    def checkValidity(self):
        """ Check validity the sum f fractions should be 100 """
        return sum([ a.fraction for a in self.answers if a.fraction>0]) == 100

    def toHTML(self,doc, full):
        with doc.tag('ul'):
            for a in self.answers:
                with doc.tag('li'):
                    doc.input(name = self.question.getId(), type = 'checkbox')
                    doc.text(a.answer)
        if full:
            #TODO!!
            pass
                    

################# Single answer ######################
class Answer:
    """ one answer in a list"""
    pass


class NumericAnswer(Answer):
    def __init__(self,match):
        self.value = float(match.group('value'))
        if match.group('tolerance'):
            self.tolerance = float( match.group('tolerance') )
    
class NumericAnswerMinMax(Answer):
    def __init__(self,match):
        self.mini = match.group('min')
        self.maxi = match.group('max')

class AnswerInList(Answer):
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
        self.parse(source)

    def getId(self):
        """ get Identifier for the question""" 
        return 'Q'+str(id(self)) # TODO process title
        
    def parse(self,source):
        """ parse a question source. Comments should be removed first"""
        # split according to the answer
        match = reAnswer.match(source)
        if not match:
            # it is a description
            self.answers = Description(None)
            self.__parseHead(source)
            self.generalFeedback = ""
        else: 
            self.tail=stripMatch(match,'tail') 
            self.__parseHead(match.group('head'))
            self.generalFeedback = stripMatch(match,'generalfeedback')
            self.__parseAnswer(match.group('answer'))
        
    def __parseHead(self,head):
        # find the title and the type of the text
        match = reTitle.match(head)
        if match:
            self.title = match.group('title').strip()
            textMarkup = match.group('text')
        else:
            self.title = head[:20] # take 20 first chars as a title
            textMarkup = head
            
        match = reMarkup.match(textMarkup)
        if match:
            self.markup = match.group('markup').lower()
            self.text = match.group('text').strip()
        else:
            self.markup = 'moodle'
            self.text = textMarkup.strip()

    

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

        #  answers with choices and short answers
        answers=[]
        select = False
        short = True
        matching = True
        for match in reAnswerMultipleChoices.finditer(answer):
            a = AnswerInList(match)
            # one = sign is a select question
            if a.select: select = True
            # short answers are only = signs without fractions
            short = short and a.select and a.fraction == 100
            matching = matching and short and a.isMatching
            answers.append(a)
            
        if len(answers) > 0 :
            # TODO: numeric answers in a list
            if matching:
                self.answers = MatchingSet(self,answers)
                self.valid = self.answers.checkValidity()
            elif short:
                self.answers = ShortSet(self,answers)
            elif select:
                self.answers = SelectSet(self,answers)
            else:
                self.answers = MultipleChoicesSet(self,answers)
                self.valid = self.answers.checkValidity() 
        elif self.numeric :
            # is it a single numerical answer?
            self.answers = SingleNumericAnswer(self,answer[1:])
            self.valid = self.answers.valid
        else:
            # not a valid question  ?
            logging.warning("Incorrect question "+self.full)
            self.valid = False

    def toHTML(self, doc=yattag.Doc(),feedbacks=False):
        """ produces an HTML fragment, feedbacks controls the output of feedbacks"""
        if not self.valid: return ''
        with doc.tag('div', klass='question'):
            with doc.tag('div', klass='questionTitle'):
                doc.text(self.title)
            with doc.tag('form', action = ""):
                with doc.tag('div', klass='questionText'):
                    doc.text(markupRendering(self.text,self.markup))
                with doc.tag('div', klass='questionAnswers'):
                    self.answers.toHTML(doc,feedbacks)
                if feedbacks:
                    if self.generalFeedback != '':
                        with doc.tag('div', klass='questionGeneralFeedback'):
                            doc.text(markupRendering(self.generalFeedback,self.markup))
            
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

def moodleRendering(src):
    return src

def htmlRendering(src):
    return src

def markdownRendering(src):
    return markdown.markdown(src)
    
def markupRendering(src,markup='html'):
    m = sys.modules[__name__]
    rendering=markup+'Rendering'
    if rendering in m.__dict__ :
        return getattr(m,rendering)(src)
    else:
        logging.warning('Rendering error: unknown markup language '+self.markup)
        
    
    
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
