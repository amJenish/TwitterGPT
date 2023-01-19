import math
import tweepy
import openai
import time
import csv
import re
import textwrap
from tweepy import OAuthHandler
from tokens import *

#Authenticating -----
auth = OAuthHandler(consumerKey, consumerSecret, accessToken,accessSecret)

client = tweepy.Client(consumer_key=consumerKey,
                       consumer_secret=consumerSecret,
                       access_token=accessToken,
                       access_token_secret=accessSecret,bearer_token=bearerToken)

api = tweepy.API(auth)
openai.api_key = openAI_API


#tweeting and controllings --------------------------------------------------------------
def tweetClean(tweet): #cleans  the tweet to send into chatGPT  -------

    tweet = re.sub(r'@[A-Za-z0-9]+', '', tweet) #removes @mentions
    tweet = re.sub(r'#[A-Za-z0-9]+', '', tweet) #removes all hashtags
    tweet = re.sub(r'RT[\s+]', '', tweet) #Removes RT
    tweet = re.sub(r'https?:\/\/\S+', '', tweet) #Removes links
    return tweet

Records = open('Record.csv', 'a',  newline='')
writer = csv.writer(Records)
RecordsRead = open('Record.csv', 'r', newline='')
startID =  1
tweetIDArray = [] #Stores  tweet IDs that have  already been replied to.

for line in RecordsRead: #Since csv files do not update  until closed, I will append all tweet ID values from  previous runs into tweetID.
    arr = line.split(',')
    ID = arr[0]
    tweetIDArray.append(ID)

while True: #inf loop to keep looking for tweets that mention me
    mentionData = api.mentions_timeline(since_id = startID) #gets every tweet that mentions me.
    if mentionData == None: #if mentionData is empty/ no more tweets left to  reply to.
        print("No more tweets left to reply to...")
        time.sleep(28) #pause search.
    else: #If mentionData is not empty/ tweets left to reply to.

        for tweet in mentionData: #iterate through tweets
            replied = tweetIDArray.count(tweet.id) #counts how many tweet id exist in tweetIDArray.
            if replied < 1: #check if a tweet has already been replied to.
                try:
                    tweetString = tweetClean(str(tweet.text))#clean tweet
                    completions = openai.Completion.create(engine="text-davinci-003",
                                                           prompt= str(tweetString), n=1, stop = None, temperature = 0.6, max_tokens = 1024) #put it  into chatGPT
                    answer = completions.choices[0].text #pick an answer
                    if len(answer) < 280: #280 is the max amount of  letter you can use on twitter.
                        response = client.create_tweet(in_reply_to_tweet_id=tweet.id, text=answer)
                    elif len(answer) >= 280:  #if it's not 280, it divides them into parts.
                        Lengthlimit = len(answer) / 289 #dividing by a bigger number than 280  just  to  make sure the  chunks are smaller than 280. Getting too close to 280 seem to cause problems..

                        tweet_chunk_length = len(answer) / math.ceil(Lengthlimit)

                        # chunk the tweet into individual pieces
                        tweet_chunks = textwrap.wrap(answer,  math.ceil(tweet_chunk_length), break_long_words=False)

                        # iterate over the chunks
                        for x, chunk in zip(range(len(tweet_chunks)), tweet_chunks):
                            if x == 0:
                                response = client.create_tweet(in_reply_to_tweet_id=tweet.id, text=f'1 of {len(tweet_chunks)}: {chunk}')#Response
                                time.sleep(3)
                            else:
                                response = client.create_tweet(in_reply_to_tweet_id=tweet.id, text=f'{x+1} of {len(tweet_chunks)}: {chunk}') #Response
                                time.sleep(3)

                    tweetIDArray.append(tweet.id)#Append the tweet's ID to tweetIDArray so that we don't create a  duplicate response.
                    writer.writerow([tweet.id, "Success"])  #Make a record of it in a file.
                    startID = tweet.id
                    print(tweet.id, end = '')
                    print("......success!")
                except Exception as e:
                    print(e)
                    tweetString = tweetClean(str(tweet.text))
                    print(tweet.id, end = '')
                    print("......fail")
                    time.sleep(10)
            else:
                pass
    time.sleep(30)