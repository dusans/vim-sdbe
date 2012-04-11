import vim
import pyodbc
from collections import defaultdict

def echo(message):
    for m in message.split(u'\n'):
        vim.command((u':echo "%s"' % m).encode(u'utf-8'))

def echom(message):
    u"""
    Print a regular message that will be visible to the user, even when
    multiple lines are printed
    """
    # probably some escaping is needed here
    for m in message.split(u'\n'):
        vim.command((u':echomsg "%s"' % m).encode(u'utf-8'))

class Connection:
    """
        Implement all the logic for one single connection
        - connect, reconnect
        - catalog load and save
        - workspace per connection...
        - managing scripts
    """
    def __init__(self, name='', password="", conn_settings=None):
        self.name = name
        self.password = password
        self.connSettings = conn_settings
        self.openconnection()

    def openconnection(self):
        try:
            self.conn = pyodbc.connect('DSN=%s;PWD=%s' % (self.name, self.password))
            #self.conn.autocommit = True
            self.cursor = self.conn.cursor()
        except Exception as exc:
            self.conn = None
            print("Error opening connection: %s" % self.name, unicode(exc.args))

    def executesql(self, sql):
        echo('indide executesql')
        query = self.cursor.execute(sql)

        for i in query.fetchall():
            echo("rss_id: %s" % i)

class Sdbe:
    def __init__(self):
        self._documents = {}
        # CHANGE: odbc_dsn_name, password
        self.connection = Connection(name='mynews', password='XXXXXX')
        echo("connection open")

#SDBE = Sdbe()
