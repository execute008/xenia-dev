# -*- coding: utf-8 -*-
import json
from io import StringIO
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from random import randint

PORT = 1870
SEARCH_API_KEY = ""
COSTUM_SEARCH_CX = ""
MAP_API_KEY = ""



class Xenia:
    def __init__(self):
        self.brain = open("memory/xenia.brain", 'r').readlines()
        self.answers = open("memory/answer.brain", 'r').readlines()
        self.answer = ""
        self.classify = []
        self.keywords = []
        self.winner = ""
        self.query = ""
        
    
    def handleInput(self, instream):
        instream = instream.strip("?\n").split(" ")
        key_count = 0
        search = False
        sf = False
        for word in instream:
            found = False
            for line in self.brain:
                thought = line.strip("\n").split(":")
                if thought[0].lower() == word.lower():
                    
                    if search and sf and thought[1] != "a":
                        sf = False
                        found = False
                        break
                    elif thought[1] == "s" or thought[1] == "m" and search == False:
                        self.classify.append(thought[1])
                        found = True
                        search = True
                        sf = True
                        break
                    elif thought[0].lower() == "i" and len(word) != 1:
                        break
                    else:                            
                        self.classify.append(thought[1])
                        found = True
            if found != True:
                self.keywords.append(word)
                key_count+=1
        if len(self.classify) == 0 and key_count > 0 or "s" in self.classify or "m" in self.classify:
           self.classify.append("k")

        self.evalClassify()
                             
    
    def evalClassify(self):
        
        #FIND BEST ANSWER
        score = 0
        highscore = [ 0 , ""]
        for line in self.answers:
            line = line.strip("\n").split(":")
            for cl in self.classify:
                for i in range(1, len(line)):
                    if line[i] in cl:
                        score += 1
            if score > highscore[0]:
                highscore[0] = score
                highscore[1] = line[0]
            score = 0
        self.winner = highscore[1]

        #ADD MISSING KEYWORDS
        for line in self.answers:
            line = line.strip("\n").split(":")
            if self.winner in line[0]:
                self.classify = []
                for i in range(1, len(line)):
                    self.classify.append(line[i])
        if len(self.keywords) > 0:
            self.classify.append("k")
        print(str(self.classify) + "+ keys:" + str(self.keywords))
                            
                        
            

        ctk, ending = self.check_to_add_keywords()
        if ctk:
            for keyword in self.keywords:
                self.winner += " "+keyword
                self.query += keyword + " "
            self.winner += ending
        elif ("name" in self.classify or "k" in self.classify) and ("m" in self.classify or "name" in self.classify):
            for keyword in self.keywords:
                self.query += keyword.title() + " "
            if "name" in self.classify:
                self.query = self.query[:-1]
            self.winner = self.query + self.winner

    def check_to_add_keywords(self):
        if "k" in self.classify and ("s" in self.classify or len(self.classify) == 1):
            return (True, "...")
        return (False, None)

    def answerRequest(self):
        answer = self.winner
        io = StringIO()

        #Search for ... in Google
        if "s" in self.classify or ("k" in self.classify and len(self.classify) == 1 and len(self.keywords) != None):
            url = "https://www.googleapis.com/customsearch/v1?q="+self.query.replace(" ", "%20") +"&cx="+COSTUM_SEARCH_CX+"&num=5&key="+SEARCH_API_KEY 
            json.dump({"answer": answer, "classify": "s", "url": url, "position": "left"}, io)
            return io.getvalue()
        
        #Use Maps
        elif "m" in self.classify:
            url = "https://www.google.com/maps/embed/v1/place?key="+MAP_API_KEY+"&q="+self.query.replace(" ", "%20")
            json.dump({"answer": answer, "classify": "m", "url": url,  "position": "left"},io)
            return io.getvalue()

        #Throw a Coin 
        elif 'tac' in self.classify:
            result = self.throwCoin()
            json.dump({"answer": result, "position": "left"},io)
            return io.getvalue()
            
        #All other Answers
        else:
            json.dump({"answer": answer, "position": "left"},io)
            return io.getvalue()

    def clean(self):
        self.brain = open("memory/xenia.brain", 'r').readlines()
        self.answers = open("memory/answer.brain", 'r').readlines()
        self.answer = ""
        self.classify = []
        self.keywords = []
        self.winner = ""
        self.query = ""
    
    def throwCoin(self):
        rn = randint(0,1)
        ret = "Head"
        if rn:
            ret = "Tails"
        return ret
        


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
            
        request_path = unquote(self.path, encoding="utf-8")
 
        print("\n" + request_path)
        if("favicon.ico" in request_path):
            try:
                self.send_response(0)
            except:
                pass
        else:
            try:
                request_path = request_path.strip("/").replace("%20", " ")
                xenia = Xenia()
                xenia.handleInput(request_path)
                answer = xenia.answerRequest()
                print(answer)
                response = bytes(answer, 'utf-8')
                xenia.clean()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=UTF-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response)
            except:
                pass
        





def main():
    print('Listening on localhost:%s' % PORT)
    server = HTTPServer(('', PORT), RequestHandler)
    server.timeout = 1
    server.serve_forever()

        
if __name__ == "__main__":
    main()
