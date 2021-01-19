from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import tarfile
import os

from base import mods
from base.models import Auth, Key


class Question(models.Model):
    desc = models.TextField()
    is_yes_no_question = models.BooleanField(default=False)

    def save(self):

        super().save()

        try:
            # try to get the options YES and NO where the question is self
            option_yes = QuestionOption.objects.get(option = 'YES', question = self)
            option_no = QuestionOption.objects.get(option = 'NO', question = self)

            # if they exist but it is not a yes/no question, we delete these options
            if not self.is_yes_no_question:
                QuestionOption.objects.get(pk=option_yes.id).delete()
                QuestionOption.objects.get(pk=option_no.id).delete()

        # if it doesn't have any yes or no options
        except:

            # if it's a yes or no question
            if self.is_yes_no_question:

                # delete all the options that are not yes/no options
                try:
                    options = QuestionOption.objects.all().filter(question = self)
                    for element in options:
                        QuestionOption.objects.get(pk=element.id).delete()

                    orders = QuestionOrder.objects.all().filter(question = self)
                    for element in orders:
                        QuestionOrder.objects.get(pk=element.id).delete()
                # if it has no options at all
                except:
                    pass

                # save the YES option
                question_yes = QuestionOption(option = 'YES', number = 0, question = self)
                question_yes.save()

                # save the NO option
                question_no = QuestionOption(option = 'NO', number = 1, question = self)
                question_no.save()

    def __str__(self):
        return self.desc


# Auxiliar method save option without repiting
def repitedOption(self):

    # if that option exists, don't save it
    try:
        QuestionOption.objects.get(option = self.option, question = self.question)
        raise ValidationError('Duplicated option, please checkout question options')

    # duplicated option
    except ValidationError:
        return

    # if doesn't exists, save it
    except:
        return QuestionOption.super_save(self)

# Auxiliar method save order without repiting
def repitedOrder(self):

    # if it exists, don't save it
    try:
        QuestionOrder.objects.get(option = self.option, question = self.question)
        raise ValidationError('Duplicated order, please checkout question order')

    # duplicated option
    except ValidationError:
        return

    # if doesn't exists, save it
    except:
        return QuestionOrder.super_save(self)

# Auxiliar method to reassing existing number in QuestionOption
def checkNumberQuestionOption(self, iteration):
    try:
        QuestionOption.objects.get(number = self.number, question = self.question)
        raise ValidationError('Duplicated number, please checkout number value')

    # if repited number
    except ValidationError:
        self.number = self.question.options.count() + iteration
        checkNumberQuestionOption(self,iteration+1)
        return

    # if doesn't exists, save it
    except:
        return


# Auxiliar method to reassing existing number in QuestionOrder
def checkNumberQuestionOrder(self, iteration):

    try:
        QuestionOrder.objects.get(number = self.number, question = self.question)
        raise ValidationError('Duplicated order number, please checkout question order')

    # if repited number
    except ValidationError:
        self.number = self.question.order_options.count() + 2+ iteration
        checkNumberQuestionOrder(self,iteration+1)
        return

    # if doesn't exists, save it
    except:
        return


# Auxiliar method to reassing existing number order number
def checkOrderNumber(self, iteration):

    try:
        QuestionOrder.objects.get(order_number = self.order_number, question = self.question)
        raise ValidationError('Duplicated order number, please checkout question order')

    # if repited number
    except ValidationError:
        self.order_number = self.question.order_options.count() + iteration
        checkOrderNumber(self,iteration+1)
        return

    # if doesn't exists, save it
    except:
        return

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    number = models.PositiveIntegerField(blank=True, null=True)
    option = models.TextField()

    def super_save(self):
        return super().save()

    def save(self):

        checkNumberQuestionOption(self,0)
        # if it isn't a yes/no question, we manage the option
        if not self.question.is_yes_no_question:
            if not self.number:
                self.number = self.question.options.count() + 2

            repitedOption(self)

        # if it is a yes/no question
        else:
            # if the option isn't 'YES' or 'NO', don't save it
            if (self.option == 'YES') or (self.option == 'NO'):
                repitedOption(self)
            else:
                return

    def delete(self):

        # if the question is a yes/no question, we can not delete the 'YES' or 'NO' options
        if ((self.option == 'YES') or (self.option == 'NO')) and (self.question.is_yes_no_question):
            return
        else:
            return super().delete()

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)


class QuestionOrder(models.Model):
    question = models.ForeignKey(Question, related_name='order_options', on_delete=models.CASCADE)
    order_number = models.PositiveIntegerField(blank=True, null=True)
    number = models.PositiveIntegerField(blank=True, null=True)
    option = models.TextField()

    def super_save(self):
        return super().save()

    def save(self):
        if not self.question.is_yes_no_question:
            if not self.number:
                self.number = self.question.order_options.count() + 1
            if not self.order_number:
                self.order_number = self.question.order_options.count() + 1

            checkOrderNumber(self,0)
            checkNumberQuestionOrder(self,0)
            repitedOrder(self)

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)

class Voting(models.Model):
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    question = models.ForeignKey(Question, related_name='voting', on_delete=models.CASCADE)
    alpha = RegexValidator("^[0-9a-zA-Z]*$", "Only letters and numbers are allowed.")
    slug = models.CharField(max_length=30, default="", unique=True ,validators=[alpha])

    VOTING_TYPE_CHOICES = [
        ('IDENTITY', 'IDENTITY'),
        ('ABSOLUTA', 'ABSOLUTA'),
        ('RELATIVA', 'RELATIVA'),]

    voting_type= models.CharField(max_length=8,choices=VOTING_TYPE_CHOICES,default='IDENTITY')

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    pub_key = models.OneToOneField(Key, related_name='voting', blank=True, null=True, on_delete=models.SET_NULL)
    auths = models.ManyToManyField(Auth, related_name='votings')

    tally = JSONField(blank=True, null=True)
    postproc = JSONField(blank=True, null=True)

    def create_pubkey(self):
        if self.pub_key or not self.auths.count():
            return

        auth = self.auths.first()
        data = {
            "voting": self.id,
            "auths": [ {"name": a.name, "url": a.url} for a in self.auths.all() ],
        }
        key = mods.post('mixnet', baseurl=auth.url, json=data)
        pk = Key(p=key["p"], g=key["g"], y=key["y"])
        pk.save()
        self.pub_key = pk
        self.save()

    def get_votes(self, token=''):
        # getting votes from store
        votes = mods.get('store', params={'voting_id': self.id}, HTTP_AUTHORIZATION='Token ' + token)
        # anon votes
        return [[i['a'], i['b']] for i in votes]

    def tally_votes(self, token=''):
        '''
        The tally is a shuffle and then a decrypt
        '''

        votes = self.get_votes(token)

        auth = self.auths.first()
        shuffle_url = "/shuffle/{}/".format(self.id)
        decrypt_url = "/decrypt/{}/".format(self.id)
        auths = [{"name": a.name, "url": a.url} for a in self.auths.all()]

        # first, we do the shuffle
        data = { "msgs": votes }
        response = mods.post('mixnet', entry_point=shuffle_url, baseurl=auth.url, json=data,
                response=True)
        if response.status_code != 200:
            # TODO: manage error
            pass

        # then, we can decrypt that
        data = {"msgs": response.json()}
        response = mods.post('mixnet', entry_point=decrypt_url, baseurl=auth.url, json=data,
                response=True)

        if response.status_code != 200:
            # TODO: manage error
            pass

        self.tally = response.json()
        self.save()

        self.do_postproc()

    def do_postproc(self):
        # votingType = "IDENTITY"
        votingType = self.voting_type
        tally = self.tally
        options = self.question.options.all()
        order_options = self.question.order_options.all()

        opts = []
        # we open the file where de results are stored and the compressed file were this files are stored
        if not os.path.exists("voting/results/"):
            os.mkdir("voting/results")
        fname = "voting/results/v" + str(self.id) + "_" + self.slug + ".txt"
        t_file = open(fname, "w")

        if options.count()!=0:
            t_file.write("Results from voting with ID " + str(self.id) + ":\n")
            for opt in options:
                if isinstance(tally, list):
                    votes = tally.count(opt.number)
                else:
                   votes = 0
                opts.append({
                    'option': opt.option,
                    'number': opt.number,
                    'votes': votes
                })
                t_file.write("Option " + str(opt.number) + ": " + opt.option + " -> " + str(votes) + " votes\n")

        ords = []
        if order_options.count()!=0:
            votingType = "BORDA"
            t_file.write("Results from ordered voting with ID" + str(self.id) + ":\n")
            for order_option in order_options:
                if isinstance(tally, list):
                    votes = tally.count(order_option.order_number)
                else:
                    votes = 0
                ords.append({
                    'option': order_option.option,
                    'number': order_option.number,
                    'order_number': order_option.order_number,
                    'votes': votes
                })
                t_file.write("Option " + str(order_option.number) + ": " + order_option.option + " -> " + str(votes) + " votes in position " + str(order_option.order_number) + "\n")
                
        t_file.close()
        
        data = { 'type': votingType, 'options': opts, 'order_options':ords }
        postp = mods.post('postproc', json=data)

        self.postproc = postp
        self.save()

        # Compress the file
        comprimido = tarfile.open('voting/results/results.tar', mode='a')
        if not fname in comprimido.getnames():
            comprimido.add(fname)
        comprimido.close()
        os.remove(fname)


    def __str__(self):
        return self.name