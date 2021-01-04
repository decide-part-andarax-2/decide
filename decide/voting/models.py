from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator

from base import mods
from base.models import Auth, Key
import tarfile
import os

class Question(models.Model):
    desc = models.TextField()

    def __str__(self):
        return self.desc


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    number = models.PositiveIntegerField(blank=True, null=True)
    option = models.TextField()

    def save(self):
        if not self.number:
            self.number = self.question.options.count() + 2
        return super().save()

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)

class QuestionOrder(models.Model):
    question = models.ForeignKey(Question, related_name='order_options', on_delete=models.CASCADE)
    order_number = models.PositiveIntegerField(blank=True, null=True)
    number = models.PositiveIntegerField(blank=True, null=True)
    option = models.TextField()

    def save(self):
        if not self.number:
            self.number = self.question.order_options.count() + 2
        if not self.order_number:
            self.order_number = self.question.order_options.count() + 2
        return super().save()

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)

class Voting(models.Model):
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    question = models.ForeignKey(Question, related_name='voting', on_delete=models.CASCADE)
    alpha = RegexValidator("^[0-9a-zA-Z]*$", "Sólo se permiten letras y números.")
    link = models.CharField(max_length=30, default="", unique=True ,validators=[alpha])

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
        # gettings votes from store
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
        tally = self.tally
        options = self.question.options.all()
        order_options = self.question.order_options.all()

        opts = []
        #Abrimos el fichero donde se guardaran los resultados y el comprimido donde se guardaran estos ficheros
        t_file = open("voting/v" + str(self.id) + ".txt", "w")

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
        data = { 'type': 'IDENTITY', 'options': opts, 'order_options':ords }
        postp = mods.post('postproc', json=data)

        self.postproc = postp
        self.save()

        #Comprimimos el fichero
        #comprimido.add("voting/results", "tar", "voting/files")
        comprimido = tarfile.open('voting/results.tar', mode='a')
        comprimido.add("voting/v" + str(self.id) + ".txt")
        comprimido.close()
        os.remove("voting/v" + str(self.id) + ".txt")


    def __str__(self):
        return self.name