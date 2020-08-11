
import socket, thread, select
from urlparse import urlparse
import pycurl
import StringIO
from urlparse import urlparse 
import certifi

__version__ = '0.1.0 Draft 1'
BUFLEN =8192
VERSION = 'Python Proxy/'+__version__
HTTPVER = 'HTTP/1.1'

class ConnectionHandler:
    def __init__(self, connection, address, timeout):
        self.client = connection
        self.client_buffer = ''
        self.timeout = timeout
        self.method, self.path, self.protocol = self.get_base_header()
        if self.method=='CONNECT':
            self.method_CONNECT()
        elif self.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT',
                             'DELETE', 'TRACE'):
            self.method_others()
        self.client.close()
        self.target.close()

    def get_base_header(self):
        while 1:
            self.client_buffer += self.client.recv(BUFLEN)
            end = self.client_buffer.find('\n')
            if end!=-1:
                break
        print
        print '%s'%self.client_buffer[:end]#debug
        data = (self.client_buffer[:end+1]).split()
        self.client_buffer = self.client_buffer[end+1:]
        return data

    def method_CONNECT(self):
        self._connect_target(self.path)
        self.client.send(HTTPVER+' 200 Connection established\n'+
                         'Proxy-agent: %s\n\n'%VERSION)
        self.client_buffer = ''
        self._read_write()        

    def method_others(self):
    	self._parser()

        self.path = self.path[7:]
        i = self.path.find('/')
        host = self.path[:i]        
        path = self.path[i:]
        self._connect_target(host)
        self.target.send('%s %s %s\n'%(self.method, path, self.protocol)+
                         self.client_buffer)
        self.client_buffer = ''
        self._read_write()

    def _parser(self):
         #dung curl lay noi dung web
    	response = StringIO.StringIO()
    	c = pycurl.Curl()
    	c.setopt(pycurl.CAINFO, certifi.where())
    	c.setopt(c.URL, self.path)
    	c.setopt(c.WRITEFUNCTION, response.write)
    	c.setopt(c.HTTPHEADER, ['Content-Type: application/json', 'Accept-Charset: UTF-8'])
    	c.setopt(c.POSTFIELDS, '@request.json')
    	c.perform()
    	c.close()
    	body = response.getvalue()
    	response.close()
    	 #trich xuat url 
    	arrbody = body.splitlines()
    	list_url = []
    	file = open('url.txt', 'w')
    	for line in arrbody:
    		start = line.find('href="http')
    		if (start != -1):
    			end = line.find('"', start + 7)
    			url = line[start + 6:end]
    			list_url.append(url)
    			file.writelines(url + '\n')
    			urlpar = urlparse(url)
    			strparse = '(Protocol:' + urlpar.scheme + ', Domain:' + urlpar.netloc + ', Path:' + urlpar.path + ', Params:' + urlpar.params + ', Query:' + urlpar.query + ", Fragment:" + urlpar.fragment + ')'
    			file.writelines(strparse + '\n')
    		    

    	http=https=ftp=0
        #phan loai  theo giao thuc http
    	file.writelines('\n\n'+'Protocol http'+'\n')
    	for item in list_url:
    		parse=urlparse(item)
    		if(parse.scheme=='http'):
    			http+=1
    			file.writelines(item+'\n')
    	file.writelines(str(http))

         #phan loai  theo giao thuc https
    	file.writelines('\n\n'+'Protocol https'+'\n')
    	for item in list_url:
    		parse=urlparse(item)
    		if(parse.scheme=='https'):
    			https+=1
    			file.writelines(item+'\n')
    	file.writelines(str(https))

        #phan loai  theo giao thuc ftp
    	file.writelines('\n\n'+'Protocol ftp'+'\n')
    	for item in list_url:
    		parse=urlparse(item)
    		if(parse.scheme=='ftp'):
    			ftp+=1
    			file.writelines(item+'\n')
    	file.writelines(str(ftp)+'\n')

         #loc domain name trung nhau
    	listDomain={''}
    	for item in list_url:
    		abc=urlparse(item)
    		listDomain.add(abc.netloc)
         #phan loai  theo domain name
    	for domain in listDomain:
    		file.writelines('\n''DomainName '+domain+'\n')
    		count=0
    		for line in list_url:
    			parse=urlparse(line)
    			if(parse.netloc==domain):
    				count+=1
    				file.writelines(line+'\n')
    		file.writelines(str(count)+'\n')

    	file.close()
    	print 'done'

    def _connect_target(self, host):
        i = host.find(':')
        if i!=-1:
            port = int(host[i+1:])
            host = host[:i]
        else:
            port = 80
        (soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
        self.target = socket.socket(soc_family)
        self.target.connect(address)

    def _read_write(self):
        time_out_max = self.timeout/3
        socs = [self.client, self.target]
        count = 0
        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 3)
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(BUFLEN)
                    if in_ is self.client:
                        out = self.target
                    else:
                        out = self.client
                    if data:
                        out.send(data)
                        count = 0
            if count == time_out_max:
                break

def start_server(host='localhost', port=8080, IPv6=False, timeout=60,
                  handler=ConnectionHandler):
    if IPv6==True:
        soc_type=socket.AF_INET6
    else:
        soc_type=socket.AF_INET
    soc = socket.socket(soc_type)
    soc.bind((host, port))
    print "Serving on %s:%d."%(host, port)#debug
    soc.listen(0)
    while 1:
        thread.start_new_thread(handler, soc.accept()+(timeout,))

if __name__ == '__main__':
    start_server()
