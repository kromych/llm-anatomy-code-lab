import sys
from sdk_server import app
app.run(transport="streamable-http", host="127.0.0.1", port=int(sys.argv[2]))
