#! /usr/bin/env python
# -*- coding: utf-8 -*-
#!flask/bin/python
import json 
import os
from flask import Flask, request,jsonify
import os.path
import sys
import apiai

# Flask app should start in global layout
app = Flask(__name__)

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai
    
CLIENT_ACCESS_TOKEN = '924dd071002644828261514050005a78'# old 21b2e61a9eb74524958b763be0393ffa

app = Flask(__name__)

def findWordinJsonFile(inputRequest,filename):
    file = open(filename,'r',encoding='utf-8')
    data = file.read()
    jsonData = json.loads(data)
    findword = "none"
    typeval = jsonData['name']
    #compare place name in json data
    for i in jsonData['entries']:
        if findword != "none":
            break
        for synonyms in i['synonyms']:
            if synonyms in inputRequest:
                findword = i['value']
                break
    file.close
    return findword,typeval

def findNextFileName(inputRequest,detail):
    print("inputRequest: ",inputRequest)
    print("detail: ",detail)
    while "*" in detail :
        #find type of Errand in filename
        detail = detail.split("*")
        print("detail[0] in while: ",detail[0])
        print("detail[1] in while: ",detail[1])
        if detail[0] == "":
            detail = detail[1] 
        else:
            detail = detail[0]+detail[1] 
        filename = detail  +".json"  
        print("filename in while: ",filename)
        value,typeval = findWordinJsonFile(inputRequest,filename)
        
        if value == "none":
            response,keyword,state = findInDialogflow(detail+value)
            
            #Build response to jason data
            olddetail = detail
            nextURL = "/askType/getDirection"
            jsData = {"Resp": response,"Keyword": keyword,"State": state,"Olddetail": olddetail,"nextURL": nextURL}
            
            #return response to application
            return jsonify(jsData)
        
        print("value: ",value)
        detail = detail + value
        print("new detail: ",detail)
    return detail

@app.route('/',methods=['GET'])
def index():
    resp = "สวัสดีจ้า! มีอะไรให้ iGuide ช่วยไหมเอ๋ย" 
    keyword = "First greetings"
    state = "AskTypeRequest"
    olddetail= "none"
    jsData = {"Resp": resp,"Keyword": keyword,"State": state,"Olddetail": olddetail}
    return jsonify(jsData)

@app.route('/userStart',methods=['POST','GET'])
def userStart():

    #extact json data to string
    jsondata = request.json
    print(jsondata)
    print("Request:",jsondata['Request'])
    
    inputRequest = jsondata['Request']
    
    #Go to findInDialogflow function to analysis message 
    response,keyword,state = findInDialogflow(inputRequest)
    
    olddetail= "none"
    jsData = {"Resp": response,"Keyword": keyword,"State": state,"Olddetail": olddetail}
    return jsonify(jsData)
  
@app.route('/askType/getDirection',methods=['POST','GET'])
def getDirection():
    
    #extact json data to string
    jsondata = request.json
    print(jsondata)
    print("Request:",jsondata['Request'])
    
    inputRequest = jsondata['Request']
    
    #set initial
    state = "none"
    olddetail = jsondata['Olddetail']
    keyword = "none"
    response = "none"
    nextURL = "/askType/getDirection"
    
    
    #find some words about directions
    filename = "askDirection.json"
    wordDirect,typeval = findWordinJsonFile(inputRequest,filename)
    
    
    #find place name in filename
    filename = "placeName.json"
    placeName,typeval = findWordinJsonFile(inputRequest,filename)
            
    
    #build new inputRequest (ถามทางไป + placeName)
    if wordDirect != "none" and placeName != "none" :
        print("wordDirect != none and placeName != none")
        inputRequest = wordDirect+placeName
        #Go to findInDialogflow function to analysis message 
        response,keyword,state = findInDialogflow(inputRequest)
        keyword = inputRequest
        
    #set olddetail keep to analyze next request sentence
    elif placeName == "none" and wordDirect != "none":
        olddetail = inputRequest
        
        #Go to findInDialogflow function to analysis message 
        response,keyword,state = findInDialogflow(inputRequest)
        print("wordDirect != none and placeName == none")
        
        if state == "input.unknown" :
            #find confused Words
            filename = "confusedPlaceName.json"
            confusedPlaceName,typeval = findWordinJsonFile(inputRequest,filename)
            keyword = wordDirect + confusedPlaceName #ถามทางไป none
            
            if confusedPlaceName != "none" :
                print("wordDirect != none and confusedPlaceName != none")
                inputRequest = wordDirect+confusedPlaceName #เช่น ถามทางไปหอ
                response,keyword,state = findInDialogflow(inputRequest)
                keyword = inputRequest
    
    elif placeName == "none" and wordDirect == "none" :
        
        typeOfErrand = "none"
        
        #find type of Errand in filename
        filename = "typeOfErrand.json"
        
        typeOfErrand,typeval = findWordinJsonFile(inputRequest,filename)
        
        if typeOfErrand != "none" :
            
            detail = findNextFileName(typeOfErrand,inputRequest)
            print("detail::::",detail)
            response,keyword,state = findInDialogflow(detail)
        
        else :
            
            response,keyword,state = findInDialogflow(inputRequest)
            
    elif olddetail != "":
        
        recentFile = jsondata['RecentFile']
        filename = recentFile +".json"  
        print("filename in while: ",filename)
        value,typeval = findWordinJsonFile(inputRequest+olddetail,filename)
        print("value: ",value)
        detail = filename + value
        print("new detail: ",detail)
        
        if "*" in detail :
            detail = findNextFileName(recentFile,inputRequest)
            
        olddetail = "none"
        response,keyword,state = findInDialogflow(detail)
        print("*test=response,keyword,state===",response,keyword,state)
        
    else :
        print("else")
        response,keyword,state = findInDialogflow(inputRequest)
        
    #Build response to jason data
    jsData = {"Resp": response,"Keyword": keyword,"State": state,"Olddetail": olddetail,"nextURL": nextURL}
    
    #return response to application
    return jsonify(jsData)

@app.route('/askType/inquiry',methods=['POST','GET'])
def getInformation():
    jsondata = request.json
    inputRequest = jsondata['Request']
    olddetail = inputRequest#เก็บคำถามก่อนหน้าเพื่อเชื่อมโยงหาคำตอบให้คำถามล่าสุด
    nextURL = ""
    
    #Go to findInDialogflow function to analysis message 
    response,keyword,state = findInDialogflow(inputRequest)
    
    #Build response to jason data
    jsData = {"Resp": response,"Keyword": keyword,"State": state,"Olddetail": olddetail,"nextURL": nextURL}
    
    #return response to application
    return jsonify(jsData)
    
def findInDialogflow(inputRequest):
    
    ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)

    request = ai.text_request()
    
    print("inputRequest: ",inputRequest)
    
    request.lang = 'th'  # optional, default value equal 'en'

    request.session_id = "<SESSION ID, UNIQUE FOR EACH USER>"

    request.query = inputRequest

    response = json.loads(request.getresponse().read().decode('utf-8'))

    response = response['result']
    
    #get intentName to keyword
    intentName = response['metadata']
    
    intentName = intentName['intentName'] 
    
    #get action
    action = response['action']
    
    #get speech to response
    speech = response['fulfillment']
    
    speech = speech['speech']
    
    print ("response, action: ",speech, action)
    
    return speech,intentName,action


    
if __name__ == '__main__':
    #main()
    print("RUNNNNNNNNN")
    app.run()