import sys
from PMS import Plugin, Log, DB, Thread, XML, HTTP, Utils
from PMS.MediaXML import *
from PMS.Shorthand import _L, _R, _E, _D

GL_PLUGIN_PREFIX   = "/photos/Google-LIFE"
GL_URL             = "http://images.google.com/hosted/life"
GL_SEARCHURL       = "http://images.google.com/images?q="

GL_SEARCH_DEPTH    = 3 # number of search result pages to parse

####################################################################################################
def Start():
  Plugin.AddRequestHandler(GL_PLUGIN_PREFIX, HandlePhotosRequest, "Google LIFE Archive", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("ImageStream", viewMode="Pictures", contentType="photos")
  HTTP.__headers["User-agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"  

####################################################################################################

def searchLoop(searchResults, dir):
  #Log.Add(XML.ElementToString(searchResults))
  searchResults = XML.ElementToString(searchResults)
  #Log.Add(searchResults) 
  searchResults = searchResults[searchResults.find("dyn.setResults")+17:]
  searchResults = searchResults.split("],[")
  for s in searchResults[1:]:
    tmpS = s.replace("(","").replace(");","").replace('"',"")
    #Log.Add(tmpS)
    tmpS = tmpS.split(",")
    id = HTTP.Unquote(tmpS[3])
    #Log.Add(id)
    thumb = id.replace("large","landing")
    desc = tmpS[6].replace("\\x3cb\\x3e","").replace("\\x3c/b\\x3e","").replace("\\x26#39;","'")
    dir.AppendItem(PhotoItem(id, desc, desc, thumb))
  return dir
  
def searchResults(url, dir):
  searchResults = XML.ElementFromString(HTTP.GetCached(url),True)
  if searchResults.find("did not match any documents") > 0:
    return None
  #pull out the number of result pages
  #Log.Add(HTTP.GetCached(url))
  #Log.Add(url)
  approxResults = searchResults.xpath("//div[@id='resultStats']")[0].text_content().replace(",","").replace('About ','')
  approxResults = approxResults[:approxResults.find(" ")]
  totalResultsPages = (int(approxResults) / 21) + 1 #imperfect need to see if this is exactly divisible by 20 or not 
  if totalResultsPages > GL_SEARCH_DEPTH: totalResultsPages = GL_SEARCH_DEPTH
  for x in range(totalResultsPages): #loop through search result pages
    #Log.Add(x)
    if x > 0: # not the first time through, so skip and pass in the already retrieved searchResults html
      tmpSpot = url.find("&start=")+7
      #Log.Add("tmpSpot: " + str(tmpSpot))
      if tmpSpot > 7:
        tmpSpotEnd = url.find("&",tmpSpot)
        if tmpSpotEnd == -1: tmpSpotEnd = len(url)
        lastSearchStart = url[tmpSpot:tmpSpotEnd]
        #Log.Add("ls: " + lastSearchStart + " *** " + url)
        newSearchStart = str(int(lastSearchStart) + 20)
        url = url.replace("=" + lastSearchStart,"=" + newSearchStart)
      else: #first start results increment
        url = url + "&start=21"
      searchResults = XML.ElementFromURL(url,True)  
    dir = searchLoop(searchResults=searchResults, dir=dir)
    
  dir.SetViewGroup("ImageStream")
  return dir
  
def HandlePhotosRequest(pathNouns, count):
  GL_HOMEPAGE        = XML.ElementFromString(HTTP.GetCached(GL_URL), True)
  #Log.Add(GL_HOMEPAGE)
  try:
    title2 = pathNouns[count-1].split("||")[1]
    pathNouns[count-1] = pathNouns[count-1].split("||")[0]
  except:
    title2 = ""
    
  dir = MediaContainer("art-default.jpg", None, title1="Google LIFE Archive", title2=title2)
  if count == 0:
    dir.AppendItem(DirectoryItem("decades||" + _L("Decades"), _L("Decades"), ""))
    i=0
    for item in GL_HOMEPAGE.xpath("//h2"):
      i+=1
      if item.text != "Search tip":
        dir.AppendItem(DirectoryItem("section_" + str(i) + "_" + item.text + "||" + _L(item.text), _L(item.text), ""))
    dir.AppendItem(SearchDirectoryItem("search", _L("Search Google:LIFE"), _L("Search Google:LIFE"), _R("search.png")))
    return dir.ToXML()
  
  if pathNouns[0][:7] == "decades":
    if count == 1:
      for item in GL_HOMEPAGE.xpath("//a[@class='tmb']//following-sibling::a"): #decades
        dir.AppendItem(DirectoryItem(_E(item.get("href"))+"||"+item.text, item.text, ""))
    if count == 2:
      dir = searchResults(_D(pathNouns[1]),dir)

  elif pathNouns[0][:8] == "section_":
    if count == 1:
      for item in GL_HOMEPAGE.xpath("//table/tr["+ str(int(pathNouns[0][8:9])*2) +"]/td/ul/li/a"): 
        dir.AppendItem(DirectoryItem(_E(item.get("href")), item.text, ""))
    if count == 2:
      dir = searchResults(_D(pathNouns[1]),dir)
  
  elif pathNouns[0] == "search":
   if count > 1:
    query = pathNouns[1]
    if count > 2:
      for i in range(2, len(pathNouns)): query += "/%s" % pathNouns[i]
    dir = searchResults(GL_SEARCHURL + query + "+source:life",dir) # example query=http://images.google.com/images?q=country+doctor+source:life
    if dir.ChildCount() == 0:
      dir.AppendItem(DirectoryItem("%s/search" % GL_PLUGIN_PREFIX, "(No Results)", ""))
      
  return dir.ToXML()