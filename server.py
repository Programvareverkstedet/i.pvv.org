from twisted.web import server, resource, static#, util
from twisted.internet import reactor#, ssl
from twisted.web.util import redirectTo as TwistedRedirectTo
import os, sys, glob, __builtin__, ConfigParser

class Settings:
	def __init__(self, config="config.ini"):
		self.conf = ConfigParser.ConfigParser()
		f = open("config.ini", "r")
		self.conf.readfp(f)
		f.close()
Settings = Settings()
class Template():
	def __init__(self):
		f = open("template/base.html", "rb")
		self.template = f.read().replace("\r\n", "\n").replace("\r", "\n")
		f.close()
		
		f = open("template/404.html", "rb")
		self.not_found = f.read().replace("\r\n", "\n").replace("\r", "\n")
		f.close()
		
		self.domain = Settings.conf.get("server", "domain")
		self.default_title = Settings.conf.get("server", "default_title")
	def MakePage(self, request, body, title=None):
		#Session = request.getSession()
		t = title if title else self.default_title
		return self.template.replace("<!--BODY-->", body).replace("<!--TITLE-->", t)
Template = Template()

class NotFound(resource.Resource):#404 page
	isLeaf = True
	def render(self, request):
		request.setResponseCode(404)
		print "%s got 404 when requesting \"%s\"" % (request.getClientIP(), request.uri)
		
		return Template.MakePage(request, Template.not_found, "404 - Not Found")
NotFound = NotFound()

class Root(resource.Resource):
	isLeaf = False
	NotFound = NotFound
	def getChild(self, name, request):
		if name == "":
			return self
		if name == "favicon.ico":
			return self.getChildWithDefault("template", request).getChildWithDefault("favicon.ico", request)
			pass
		return self.NotFound
	def render(self, request):
		request.redirect("/home")
		return Template.MakePage(request, "")
class pageBase(resource.Resource):#to be used by plugins
	Template = Template
	isLeaf = False
	NotFound = NotFound
	def getChild(self, name, request):#usually don't get called if a child exists
		if name == "":
			return self
		return self.NotFound

def LoadPlugins():
	global PageBase, Services
	#print "Loading services..."
	__builtin__.PageBase = pageBase#ugly...
	#__builtin__.Template = Template#ugly...
	__builtin__.Services = Services#ugly...
	__builtin__.Settings = Settings#ugly...
	
	#Backup and change sys.path:
	old = sys.path[:]
	sys.path[0] = os.path.join(os.getcwd(), "services")
	
	#Load plugins:
	for i in glob.glob("services/*.py"):
		name = ".".join(os.path.split(i)[-1].split(".")[:-1])
		if name == "template": continue
		print "Loading services/%s.py..." % name
		module = __import__(name)
		Services[name] = module
		Root.putChild(name, module.Page())
	
	#Restore old sys.path:
	sys.path = old
	#print "Done!"
#/home is a service
#/template is hardcoded as a filedirectory


Root = Root()
#Root.putChild('user', User())
#Root.putChild('blog', Blog())
Root.putChild('template',  static.File(os.path.join("template" ,""), "text/plain"))

#is this needed?
Services = {}#"filename" : module
LoadPlugins()

print "Server start!"
print
#reactor.listenTCP( 80, server.Site(Root))
#reactor.listenTCP( 80, server.Site(util.Redirect("https://192.168.0.10")))
#reactor.listenTCP(443, server.Site(Root), ssl.DefaultOpenSSLContextFactory("server.key", "server.crt"))
reactor.listenTCP(80, server.Site(Root), interface='::')

reactor.run()