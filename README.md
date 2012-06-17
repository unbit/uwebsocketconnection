uwebsocketconnection
====================

an attempt to run websockets over uwsgi http router using gevent or uGreen

run it with

uwsgi --http :8080 --http-raw-body --wsgi-file your_app.wsgi --loop gevent --async 1000 --master --enable-threads

```python
# this is your_app.wsgi
import uwsgi
from uwebsocketconnection import uGeventWebSocketConnection

class EchoerWS(uGeventWebSocketConnection):
    def onmessage(self, message):
        print message
        self.send(message)

def application(env, sr):

    if env['PATH_INFO'] == '/':
        sr('200 OK', [('Content-Type','text/html')])
        return """
	<html>
  	  <head>
    	  <script language="Javascript">
      	    var s = new WebSocket("ws://localhost:8080/foobar/");
            s.onopen = function() {
              alert("connesso !!!");
              s.send("ciao");
            };
            s.onmessage = function(e) {
              alert(e.data);
            };

            function invia() {
              var value = document.getElementById('testo').value;
              s.send(value);
            }
    	  </script>
 	 </head>
  	<body>
    	<h1>WebSocket</h1>
    	<input type="text" id="testo"/>
    	<input type="button" value="invia" onClick="invia();"/>
  	</body>
	</html>
        """
        

    if env.get('HTTP_UPGRADE', '').lower() == 'websocket':
        EchoerWS(env, uwsgi.connection_fd())
        return
```


