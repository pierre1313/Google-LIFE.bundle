import re

GL_PLUGIN_PREFIX   = "/photos/Google-LIFE"
GL_URL             = "http://images.google.com/hosted/life"
GL_API_URL         = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=%s&rsz=8'

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(GL_PLUGIN_PREFIX, MainMenu, "Google LIFE Archive", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="photos")
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

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def searchResults(sender=None, url=''):
  dir = MediaContainer(viewGroup="ImageStream")
  
  for page in range(0,8):
    jsonObject = JSON.ObjectFromURL(url+"&start="+str(8*page))
  
    if int(jsonObject['responseData']['cursor']['estimatedResultCount']) < (8*page):
      break;
    
    for image in jsonObject['responseData']['results']:
      dir.Append(Function(PhotoItem(GetImage, remove_html_tags(image['contentNoFormatting']), subtitle=image['contentNoFormatting'],summary=image['contentNoFormatting'], thumb=image['tbUrl'],ext='jpg'),path=image['unescapedUrl']))

  return dir

def DecadesMenu(sender):    
  dir = MediaContainer(title2="Decades")

  for item in HTML.ElementFromURL(GL_URL).xpath("//a[@class='tmb']//following-sibling::a"): #decades
    href = item.get("href")
    url = GL_API_URL % href[href.find('q=')+2:]
    dir.Append(Function(DirectoryItem(searchResults, item.text, ""),url = url))

  return dir
   
def SectionsMenu(sender, sectionIndex = 0):
  dir = MediaContainer(title2="Sections")

  for item in HTML.ElementFromURL(GL_URL).xpath("//table/tr["+ str(sectionIndex*2) +"]/td/ul/li/a"): 
    href = item.get("href")
    url = GL_API_URL % href[href.find('q=')+2:]
    dir.Append(Function(DirectoryItem(searchResults, item.text),url=url))

  return dir

def Search(sender,query = None):
  response = searchResults(url = (GL_API_URL % (String.Quote(query) + "+source:life")))
  if response == 0:
    return MessageContainer("Error","This search query did not return any document.")
  else:
    return response