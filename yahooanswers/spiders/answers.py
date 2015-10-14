# -*- coding: utf-8 -*-
import scrapy
import urlparse
import urllib
import os


class AnswersSpider(scrapy.Spider):
    name = "answers"
    allowed_domains = ["answers.yahoo.com"]
    start_urls = (
        'http://www.answers.yahoo.com/',
    )

    def __init__(self, qfile=''):
        '''get file with questions'''
        self.qfile = qfile
        with open(self.qfile, 'r') as questions_file:
            self.questions = questions_file.readlines()

    def parse(self, response):
        '''constructig url for question'''
        for question in self.questions:

            url = urlparse.urljoin(
                # www.answers.yahoo.com
                self.start_urls[0],
                'search/search_result?fr=uh3_answers_vert_gs&type=2button&{}'
                .format(urllib.urlencode({'p': question.rstrip('\n')})))

            request = scrapy.Request(url, self.answers_page)
            request.meta['folder_name'] = question.rstrip('\n')
            yield request

    def answers_page(self, response):
        '''collects all answers urls and url for next page'''
        folder_name = response.meta['folder_name']

        answer_urls = response.xpath(
            '//h3[@class="question-title"]/a/@href').extract()
        try:
            current_page = response.xpath(
                '//div[@id="ya-sr-pg"]/strong/text()').extract()[0]
            next_page = response.xpath(
                '//div[@id="ya-sr-pg"]/a[@class="ya-sr-next"]/@href')\
                .extract()[0]

            print('parse page: {}'.format(current_page))

            req = scrapy.Request(
                response.urljoin(next_page),
                self.answers_page)
            req.meta['folder_name'] = folder_name

            yield req

        except IndexError:
            print('work done')
            pass

        for url in answer_urls:
            answer_txt_name = url.split('?')[1]
            url = response.urljoin(url)
            request = scrapy.Request(url, self.question_page)
            request.meta['answer_txt_name'] = answer_txt_name
            request.meta['folder_name'] = folder_name

            yield request

    def question_page(self, response):
        '''parse single answer page write data into file with name
            same as answer url'''

        name = response.xpath('//h1[@itemprop="name"]/text()').extract()[0]

        body = response.xpath('//span[@itemprop="text"]/text()').extract()[0]
        best_answer = response.xpath(
            '//div[@itemprop="acceptedAnswer"]\
            //span[@class="ya-q-full-text"]//text()').extract()
        best_answer = ''.join(best_answer)

        # print('=' * 50)
        # print(response.url)
        # print(u'QUESTION: {}\nQUESTION BODY: {}'.format(name, body))
        # print(u'BEST ANSWER: {}'.format(best_answer))

        another_answers = response.xpath('//ul[@id="ya-qn-answers"]//li')

        all_another_answers = []

        for another_answer in another_answers:
            another_answer_body = another_answer.xpath(
                '//div[@class="answer-detail Fw-n"]//text()').extract()
            another_answer_body = ''.join(another_answer_body)
            # print('=' * 50)
            # print(another_answer_body)
            # print('=' * 50)
            all_another_answers.append(another_answer_body)

        self.write_info(
            response.meta['folder_name'],
            response.meta['answer_txt_name'],
            link=response.url,
            name=name,
            question_body=body,
            best_answer=best_answer,
            all_another_answers=all_another_answers
        )

    def write_info(self, folder, file_name, **kwargs):
        '''Helper function for check the answers folder exists here
        and write all data from kwargs.'''
        if os.path.exists('answers'):
            # it's ok
            pass
        else:
            os.mkdir('answers')

        if os.path.exists('answers' + os.sep + '{}'.format(folder)):
            # it's ok
            pass
        else:
            os.mkdir('answers' + os.sep + '{}'.format(folder))

        with open('answers/{}/{}.txt'.format(
                folder, file_name), 'wa') as datafile:
            datafile.write('LINK: {}\n'.format(kwargs['link']))
            datafile.write(
                'QUESTION: {}\n'.format(kwargs['name']
                                        .encode('utf-8').strip()))
            datafile.write(
                'QUESTION BODY: {}\n'.format(kwargs['question_body']
                                             .encode('utf-8').strip()))
            datafile.write(
                'BEST ANSWER: {}\n'.format(kwargs['best_answer']
                                           .encode('utf-8').strip()))
            datafile.write('ANOTHER ANSWERS\n')
            try:
                for another_answer in kwargs['all_another_answers'][0]:
                        datafile.write(another_answer.encode('utf-8'))
            except IndexError:
                # no another answers
                pass
            # another_answers = '\n'.join(kwargs['all_another_answers'])
            # datafile.write(another_answers.encode('utf-8'))
            # for another_answer in kwargs['all_another_answers']:
            #     datafile.write('=' * 50)
            #     datafile.write('\n')
            #     datafile.write(another_answer.encode('utf-8').strip())
            #     datafile.write('\n')
            #     datafile.write('=' * 50)
            #     datafile.write('\n')
