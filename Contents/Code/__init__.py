import sys,re

GL_PLUGIN_PREFIX   = "/photos/Google-LIFE"
GL_URL             = "http://images.google.com/hosted/life"
GL_SEARCHURL       = "http://images.google.com/images?client=safari&rls=en-us&q="

GL_SEARCH_DEPTH    = 3 # number of search result pages to parse

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(GL_PLUGIN_PREFIX, MainMenu, "Google LIFE Archive", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("ImageStream", viewMode="Pictures", mediaType="photos")
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')
  DirectoryItem.thumb = R('icon-default.png')
  HTTP.CacheTime = 3600
  HTTP.Headers["User-agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"  

####################################################################################################
def MainMenu():
  dir = MediaContainer(title1="Google LIFE Archive")
  dir.Append(Function(DirectoryItem(DecadesMenu, title = L("Decades"))))
  i=0
  for item in HTML.ElementFromURL(GL_URL).xpath("//h2"):
    i+=1
    if item.text != "Search tip":
      dir.Append(Function(DirectoryItem(SectionsMenu, title = L(item.text)),sectionIndex = i))
  dir.Append(Function(InputDirectoryItem(Search, L("Search Google:LIFE"), L("Search Google:LIFE"), thumb=R("icon-search.png"))))
 
  return dir
  
def GetImage(sender, path):
  return DataObject(HTTP.Request(path).content,'image/jpeg')

def searchResults(sender=None, url=''):
  url = url+'&biw=1024&bih=768'
  searchResults = HTML.ElementFromURL(url)
  if (HTML.StringFromElement(searchResults).find("did not match any documents") > 0) or (searchResults == None):
    return 0
    
  approxResults = searchResults.xpath("//div[@id='resultStats']")[0].text_content().replace(",","").replace('About ','')
  approxResults = approxResults[:approxResults.find(" ")]
  totalResultsPages = (int(approxResults) / 21) + 1 #imperfect need to see if this is exactly divisible by 20 or not 
  if totalResultsPages > GL_SEARCH_DEPTH: totalResultsPages = GL_SEARCH_DEPTH
  for x in range(totalResultsPages): #loop through search result pages
    if x > 0: # not the first time through, so skip and pass in the already retrieved searchResults html
      tmpSpot = url.find("&start=")+7
      if tmpSpot > 7:
        tmpSpotEnd = url.find("&",tmpSpot)
        if tmpSpotEnd == -1: tmpSpotEnd = len(url)
        lastSearchStart = url[tmpSpot:tmpSpotEnd]
        newSearchStart = str(int(lastSearchStart) + 20)
        url = url.replace("=" + lastSearchStart,"=" + newSearchStart)
      else: #first start results increment
        url = url + "&start=21"
      searchResults = HTML.ElementFromURL(url)      
 
    dir = MediaContainer(viewGroup="ImageStream")

    searchResults = XML.StringFromElement(searchResults.xpath("//div[@id='hd_1']")[0])
    for s in searchResults.split(':['):
      s=s.replace("(","").replace(");","").replace('"',"")
      if s.find('id=hd_1') == -1: 
        tmpS = s.split(",")
        id = tmpS[3]
        thumb = id.replace("large","thumb")
        desc = tmpS[6].replace("\\x3cb\\x3e","").replace("\\x3c/b\\x3e","").replace("\\x26#39;","'")
        dir.Append(Function(PhotoItem(GetImage, desc, subtitle=desc,summary=desc, thumb=thumb,ext='jpg'),path=id))
  return dir

def DecadesMenu(sender):    
  dir = MediaContainer(title2="Decades")

  for item in HTML.ElementFromURL(GL_URL).xpath("//a[@class='tmb']//following-sibling::a"): #decades
    dir.Append(Function(DirectoryItem(searchResults, item.text, ""),url = item.get("href")))

  return dir
   
def SectionsMenu(sender, sectionIndex = 0):
  dir = MediaContainer(title2="Sections")

  for item in HTML.ElementFromURL(GL_URL).xpath("//table/tr["+ str(sectionIndex*2) +"]/td/ul/li/a"): 
    dir.Append(Function(DirectoryItem(searchResults, item.text),url=item.get("href")))

  return dir

def Search(sender,query = None):
  response = searchResults(url = (GL_SEARCHURL + query + "+source:life&biw=1024&bih=768"))
  if response == 0:
    return MessageContainer("Error","This search query did not return any document.")
  else:
    return response