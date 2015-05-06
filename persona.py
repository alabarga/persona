'''
Created on May 4, 2015
@author: uday
'''
import requests,json
from bs4 import BeautifulSoup
from urllib.request import urlopen
from fullcontact import FullContact
from TwitterSearch import *
from alchemyapi import AlchemyAPI
import csv
import fpdf

import numpy as np
import matplotlib.pyplot as plt

def barplot(pname, traits):
    fig = plt.figure()
    ax = fig.add_subplot(111)
        
    ## necessary variables
    ind = np.arange(1,len(traits)+1)      # the x locations for the groups
    width = 0.2                       # the width of the bars
    
    values = [int(float(value)*100) for name, value in traits.items()]
    print(values)
    
    ## the bars
    rects1 = ax.bar(ind, values, width,color=['blue','red','green','black','orange','yellow','purple'])
    
    # axes and labels
    ax.set_xlim(0,len(ind)+2)
    ax.set_ylim(0,100)
    ax.set_ylabel('Scores')
    ax.set_title('Traits')
    legends = [name for name,value in traits.items()]
    ax.legend( rects1, legends )
    
    plt.savefig(pname+".png", bbox_inches='tight')

def getTweets(username):
    tFeeds=[]
    try:
        tuo = TwitterUserOrder(username) # create a TwitterUserOrder

        # it's about time to create TwitterSearch object again
        ts = TwitterSearch(
            consumer_key = '&&&',
            consumer_secret = '***',
            access_token = '???',
            access_token_secret = '$$$'
        )

        # start asking Twitter about the timeline
        for tweet in ts.search_tweets_iterable(tuo):
            tweetx=str(tweet['text'].encode('ascii', 'ignore'))
            tFeeds.append(tweetx)
            
    except TwitterSearchException as e: # catch all those ugly errors
        print(e)
        
    return tFeeds

def callFullContact(email):
    #fc = FullContact('fec9240910d56738')
    apiKey = 'fec9240910d56738'
    url="https://api.fullcontact.com/v2/person.json?email="+email+"&style=dictionary&apiKey="+apiKey
    print(url)
    resp=requests.get(url)
    print(json.loads(resp.text))

def performSA(pname, text):
    alchemyapi = AlchemyAPI()
    response = alchemyapi.sentiment('text', text)
    sentiment = response['docSentiment']
    print(response)
    print(sentiment)
    if (sentiment['type']=='neutral'):
        sentiment['score']='0'
    return sentiment

def performPI(pname, text):
    traits = {}
    username = "b879ac45-108f-40eb-ba91-9a9f1ea03725"
    password = "D15conBKSVSI"
    url      = "https://gateway.watsonplatform.net/personality-insights/api/v2/profile"
    resp = requests.post(url, auth=(username, password),  headers = {"content-type": "text/plain"}, data=text)
    response = json.loads(resp.text)
    tree = response['tree']
    traits['openness']=tree['children'][0]['children'][0]['percentage']
    
    big5Traits = tree['children'][0]['children'][0]['children'][0]['children']
    for trait in big5Traits:
        traits[trait['id']]=trait['percentage']

    print(traits)
    barplot(pname, traits)
    return traits

def performEE(url):
    alchemyapi = AlchemyAPI()
    response = alchemyapi.entities('url', url, {'disambiguate': 0})
    relatedEntities = {}
    if response['status'] == 'OK':
        entities = response['entities']
        print(entities)
        for entity in entities:
            print(entity["relevance"]+" "+entity["text"])
            if (float(entity['relevance'])>0.1):
                relatedEntities[entity["type"]]=entity["text"]
    return relatedEntities

def performSAURL(pname, url, tData):
    response = urlopen(url)
    html = response.read()    
    soup = BeautifulSoup(html)
    text = str(soup.get_text().encode('latin-1', 'ignore'))
    text = text + "." + ''.join(tData)
    return performSA(pname, text)

def performPIURL(pname, url,tData):    
    response = urlopen(url)
    html = response.read()    
    soup = BeautifulSoup(html)
    text = str(soup.get_text().encode('latin-1', 'ignore'))
    text = text + "." + ''.join(tData)
    traits = performPI(pname, text)
    return traits

def writeToFile(name, piData, eeData, twitterFeedData):
    outFilename = name + ".out"
    outFile = open(outFilename,'w')
    outFile.write("persona report for " + name)
    outFile.write("\n")
    outFile.write("------------------------------------"+"\n")
    outFile.write("personality insights ")
    outFile.write("\n")
    for name,value in piData.items():
        outFile.write(name+" "+str(value)+"\n")
    outFile.write("------------------------------------"+"\n")
    outFile.write("related entities"+"\n")
    for name,value in eeData.items():
        outFile.write(name+" "+value+"\n")
    outFile.write("------------------------------------"+"\n")
    outFile.write("tweets"+"\n")
    outFile.write(twitterFeedData)
    outFile.close()

def createPDF(pname, piData, eeData, twitterFeedData, sentiment, spsScore):
    pdf = fpdf.FPDF(format='letter')
    pdf.add_page()
    pdf.set_font("Arial", style='BU', size=14)
    pdf.cell(200, 10, txt="Persona Report For "+pname, border=0,ln=1, align="C")
    spsScore="SPS:"+str(spsScore)
    pdf.cell(200, 10, txt=spsScore, border=0,ln=1, align="C")
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200, 10, txt="Personality Traits",border=0,ln=1,align='C')
    pdf.image(pname+".png",w=100,h=50)
    #pdf.set_font("Arial", style='', size=9)
    #for name,value in piData.items():
    #    valueS = name+":"+"{0:.2f}".format(float(value))
    #    pdf.cell(200, 8, txt=valueS, border=1, ln=1, align='C')
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200,10,txt="Top Related Entities",border=0,ln=1,align='C')
    pdf.set_font("Arial", style='', size=9)
    for name,value in eeData.items():
        valueS=name+":"+value
        pdf.cell(200, 8, txt=valueS, border=1, ln=1, align='C')
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200,10,txt="Recent Tweets..",border=0,ln=1,align='C')
    pdf.set_font("Arial", style='', size=9)
    for i in range(len(twitterFeedData)):
        if (i<10):
            pdf.cell(200, 10, txt=twitterFeedData[i], border=0, ln=1, align='C')
        else:
            break
    pdf.set_font("Arial", style='U', size=12)
    pdf.cell(200,10,txt="Tweet Sentiment",border=0,ln=1,align='C')
    pdf.set_font("Arial", style='', size=9)
    sentimentOut = "type="+sentiment['type']+" score="+sentiment['score']
    pdf.cell(200,10,txt=sentimentOut,border=1,ln=1, align='C')
    pdf.output(pname+".pdf")
    
def processPersona(person):
    name = person[0]
    wiki = person[1]
    twitterUserName = person[2]
    
    if twitterUserName!="NA":
        twitterData = getTweets(twitterUserName)
        sentiment=performSA(name,twitterData)
    else:
        twitterData = ["no twitter data"]
        sentiment={'type': 'NA', 'score': 'NA', 'mixed':'NA'}
    
    if (wiki!="NA"):
        piData = performPIURL(name, wiki,twitterData)
        eeData = performEE(wiki)
    else:
        piData = {"no data":"no data"}
        eeData = {"no data":"no data"}
    
    print(sentiment)
    spsScore=computeSPS(piData, sentiment)
    createPDF(name, piData, eeData, twitterData, sentiment, spsScore)
    #writeToFile(name, piData, eeData, twitterData)

def createPersonas(filename):
    f = open(filename, 'rt')
    try:
        persons = csv.reader(f)
        counter=0
        for person in persons:
            if (counter>0):
                processPersona(person)
            counter+=1
    finally:
        f.close()

def computeSPS(traits, sentiment):
    values = [int(float(value)*100) for name, value in traits.items()]
    ss=0
    if (sentiment['type']!='NA'):
        ss=int(float(sentiment['score'])*100)
    total=0
    for value in values:
        total+=value
    total+=ss
    print("Score ", total)
    return total
    
if __name__ == '__main__':
    createPersonas('person list.csv')
