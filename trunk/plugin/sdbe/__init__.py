import vim
import pyodbc
from collections import defaultdict
from decimal import Decimal
import time
from random import randint

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

def echoe(message):
	u"""
	Print an error message. This should only be used for serious errors!
	"""
	# probably some escaping is needed here
	for m in message.split(u'\n'):
		vim.command((u':echoerr "%s"' % m).encode(u'utf-8'))

def get_bufnumber(bufname):
	"""
	Return the number of the buffer for the given bufname if it exist;
	else None.
	"""
	for b in vim.buffers:
		if b.name == bufname:
			return int(b.number)


def get_bufname(bufnr):
	"""
	Return the name of the buffer for the given bufnr if it exist; else None.
	"""
	for b in vim.buffers:
		if b.number == bufnr:
			return b.name

def get_user_input(message):
	u"""Print the message and take input from the user.
	Return the input or None if there is no input.
	"""
	vim.command(u'call inputsave()'.encode(u'utf-8'))
	vim.command((u"let user_input = input('" + message + u": ')")
			.encode(u'utf-8'))
	vim.command(u'call inputrestore()'.encode(u'utf-8'))
	try:
		return vim.eval(u'user_input'.encode(u'utf-8')).decode(u'utf-8')
	except:
		return None

def insert_at_cursor(text, move=True, start_insertmode=False):
	u"""Insert text at the position of the cursor.

	If move==True move the cursor with the inserted text.
	"""
	d = ORGMODE.get_document(allow_dirty=True)
	line, col = vim.current.window.cursor
	_text = d._content[line - 1]
	d._content[line - 1] = _text[:col + 1] + text + _text[col + 1:]
	if move:
		vim.current.window.cursor = (line, col + len(text))
	if start_insertmode:
		vim.command(u'startinsert'.encode(u'utf-8'))

# -----------------------------------------
# sdbe code...
# -----------------------------------------

class Sdbe:
    def __init__(self):
        self.connections = {}
        self.workspace = Workspace(self)
        self.workspace.open()
        self.settings = Settings()
        echo("connection open")

    def newconnection(self, odbc_dsn_name):
        self.settings.load()
        password = self.settings.data['connections'][odbc_dsn_name]["password"]
        connection = self.opennewconnection(odbc_dsn_name, password, False)
        new_uniq_conn_name = '%s#%s' % (odbc_dsn_name, randint(0, 100))
        self.connections[new_uniq_conn_name] = Connection(odbc_dsn_name,
                password)

        #connection.openworkspace()
        print("Connection has been opened.")

    def executemany(self):
        pass 

        if vim.current.buffer.parent_script.is_enabled():
            self.conntabs.currentWidget().saveworkspace()
            self.conntabs.currentWidget().scripttabs.currentWidget().executemany()
            #self.showtooltip("Sql execute in %s seconds." % round(time.time() - startTime, 4))

    def stopexecute(self):
        self.conntabs.currentWidget().scripttabs.currentWidget().stopexecute()

    # ==== ==== ==== ==== ==== ==== ==== ====
    # SETTINGS
    # ==== ==== ==== ==== ==== ==== ==== ====
    def loadsettings(self):
        sett = Settings("settings.yaml")
        message = sett.load()

        if message[0] == "Error":
            warningMessage("Settings load ERROR.", message[1])
        return sett

    def openODBCmanager(self):
        try:
            Popen(["odbcad32.exe"])
        except:
            warningMessage("Error", "Could not open ODBC Manager.")

class Catalog:
    def reloadcatalog(self):
        if self.conntabs.currentWidget().isEnabled():
            self.conntabs.currentWidget().reloadcatalog()
            print("Catalog has been reloadet in %s seconds for %s tables."
                                % (round(time.time() - startTime, 4),
                                len(self.conntabs.currentWidget().catalog)))
    def showcatalog(self):
        self.conntabs.currentWidget().showcatalog()

class Workspace:
    def __init__(self, parent):
        self.sdbe = parent

    def save(self):
        print "saveworkspace"
        workspace = []
        for tabIndex in range(self.conntabs.count()):
            tab = self.conntabs.widget(tabIndex)
            tab.saveworkspace()
            workspace.append(tab.name)

        yaml.dump(workspace, open("files/workspace.yaml", "w"))

    def open(self):
        print "#openworkspace"
        if os.path.exists("files/workspace.yaml"):
            try:
                workspace = yaml.load(open("files/workspace.yaml"))
            except Exception as exc:
                warningMessage("Error at loading workspace!", unicode(exc.args))
                workspace = list()
                self.newconnection()

            if workspace != None:
                for connName in workspace:
                    print connName
                    try:
                        password = self.sett.settings['connections'].get(connName, {}).get("password", "")
                        connection = self.opennewconnection(connName, password,  False)
                        connection.openworkspace()
                        #QtCore.QTimer.singleShot(1, connection.openworkspace)

                    except Exception as exc:
                        warningMessage("Error loading workspace for conn: %s" % connName, unicode(exc.args))
                if len(workspace) == 0:
                    self.newconnection()

class Settings:
    def __init__(self, settingsFile='sdbe_settings.yml'):
        self.settingsFile = settingsFile
        self.data = {}
    # ==== LOAD SETTINGS ====
    def load(self):
        self.data = {}

        try:
            self.data = yaml.load(open(self.settingsFile))
        except IOError, e:
            open(self.settingsFile, "w").write(open("files/%s.%s" % (self.settingsFile, "example")).read())
            self.data = yaml.load(open(self.settingsFile))
            print("Info", "Settings file not found! I have created a settings.yml file in files directory. \nGo edit it or just click Settings button!")
        except ParserError, e:
            print("Error", "Settings load ERROR. YAML setting file is corrupt!\n %s" % str(e))

class Connection:
    """
        Implement all the logic for one single connection
        - connect, reconnect
        - catalog load and save
        - workspace per connection...
        - managing scripts
    """
    def __init__(self, odbc_dsn_name='', password=""):
        self.odbc_dsn_name = odbc_dsn_name
        self.password = password
        self.openconnection()
        
        # AUTO COMPLETE
        self.columnscatalog = defaultdict(list)
        self.catalog = []

    def openconnection(self):
        try:
            self.conn = pyodbc.connect('DSN=%s;PWD=%s' % (self.odbc_dsn_name, self.password))
            #self.conn.autocommit = True
            self.cursor = self.conn.cursor()
        except Exception as exc:
            self.conn = None
            echoe("Error opening connection: %s" % self.odbc_dsn_name, unicode(exc.args))

    def executesql(self, sql):
        #echo('indide executesql')
        query = self.cursor.execute(sql)
        time.sleep(5)
        vim.command(':vsp sdbe_result2.csv')
        #vim.command(u"let g:csv_delim='×'".encode('utf-8'))

        delimiter = u'×'
        
        # header
        header = delimiter.join(column[0] for column in query.description)
        vim.current.line = header.encode('utf-8')

        # data
        for i in query.fetchall():
            vim.current.buffer.append(delimiter.join(map(unicode, i)).encode(u'utf-8'))

        # tabularing
        tabular_align = u''
        tabular_space = 0
        for index, column in enumerate(query.description):
            print index, column
            if column[1] in (int, float, long, Decimal, ):
                tabular_align += 'r%s' % tabular_space
                print 'is num'
            else:
                tabular_align += 'l%s' % tabular_space
        comm = u':Tabular /%s/%s' % (delimiter, tabular_align)
        vim.command(comm.encode('utf-8'))

        #vim.command(':Header')
    def getcatalog(self):
        catalog = []

        print "START CATALOG LOAD: %s" % time.ctime()
        for i in self.cursor.tables(): #schema=self.connSettings.get('schema', '%')
            if i.table_name != None:
                #catalog[i.table_name.upper()] = dict([("TYPE", i.table_type), ("COLUMNS", dict())])
                catalog.append(map(str, [i.table_cat, i.table_schem, i.table_name, i.table_type, i.remarks]))
        print "END CATALOG LOAD: %s" % time.ctime()

        return catalog

    def reloadcatalog(self):
        self.catalog = self.getcatalog()
        self.savecatalog()
        # rebuild editor API for autocomplete
        for scriptIndex in range(0, self.scripttabs.count()):
            self.scripttabs.widget(scriptIndex).editor.setautocomplete(self.catalog)

    def savecatalog(self):
        pickle.dump(self.catalog, open("files/cache/%s.pickle" % self.name, "w"))

    def loadcatalog(self):
        if os.path.exists("files/cache/%s.pickle" % self.name):
            self.catalog = pickle.load(open("files/cache/%s.pickle" % self.name))
        else:
            self.reloadcatalog()

    def showcatalog(self):
        print "showcatalog"
        headers = ["DB Tree"]
        #catalog = self.cursor.tables(schema=self.connSettings.get('schema', '%'))

        #treeWidget = CatalogTree(catalog)
        #treeWidget.model().headers = headers

        script = self.scripttabs.currentWidget()
        #script.catalogtree.loadcatalog(catalog)
        #script.splitter.addWidget(self.treeWidget)
        #script.table = self.treeWidget
        columns = ["TABLE/COLUMN", "TYPE", "LENGTH"]
        printTable = [columns]

        for table in sorted(self.catalog):
            printTable.append([table[2], table[3], ""])
##            columns = self.catalog[table]["COLUMNS"]
##            for column in columns:
##                printTable.append(["\t%s" % column, 0, 0])

            printTable.append(["", "", ""])
        script.printmessage(printTable)




class Script(QtGui.QWidget):
    def __init__(self, parent=None, conn=None):
        self.connection = parent
        self.saveTo = None
        self.query = []
        self.fetchedall = True
        self.fetchednum = 0
        self.fetchto = 0


        # sql editor
        self.editor = Editor(self)
        self.editor.setautocomplete(self.connection.catalog)
        self.findDialog = FindDialog(self)
        QtCore.QObject.connect(self.editor, QtCore.SIGNAL("userListActivated(int,QString)"), self.userlistselected)

        # table
        self.table = Table(self)
        QtCore.QObject.connect(self.table.verticalScrollBar(), QtCore.SIGNAL("valueChanged(int)"), self.maybefetchmore)


    def executemany(self):
        sqlparsed = self.editor.getparsedsql()

        if not self.connection.conn:
            self.connection.openconnection()

        if len(sqlparsed) > 0:
            header = ["S", "ROWS", "START", "TIME", "ERROR", "SQL"]

            self.fetchedall = True
            self.locktab()
            self.executemanythread = ExecuteManyThread(self)
            self.connect(self.executemanythread, QtCore.SIGNAL('executed'), self.executed)
            self.connect(self.executemanythread, QtCore.SIGNAL('finished()'), self.postexecutemany)

            # define model
            self.fetchednum = 0
            self.executemanymodel = ExecuteManyModel(0, len(header), self)
            for i, name in enumerate(header):
                self.executemanymodel.setHeaderData(i, QtCore.Qt.Horizontal, name)

            self.table.setModel(self.executemanymodel)
            self.table.setWordWrap(True)
            self.table.resizeColumnsToContents()

            self.executemanythread.start()

    def executed(self):
        result = self.executemanythread.results[self.fetchednum].toarray()
        self.executemanymodel.insertRow(self.fetchednum, QtCore.QModelIndex())

        for j, column in enumerate(result):
            self.executemanymodel.setData(self.executemanymodel.index(self.fetchednum, j, QtCore.QModelIndex()), column, role=0)

        # scrool table
        vertical = self.table.verticalScrollBar()
        vertical.setFocus()
        vertical.setValue(vertical.value() + 5)

        #print self.fetchednum, type(self.fetchednum), math.log(self.fetchednum + 1, 2)
        if math.log(self.fetchednum + 1, 2).is_integer():
            self.table.resizeColumnsToContents()

        self.fetchednum += 1

    def stopexecute(self):
        print "stopexecute"
        self.executemanythread.stop()

    def is_singleselect(self):
        try:
            sqlparsed = self.executemanythread.sqlparsed
            if len(sqlparsed) == 1 and sqlparsed[0].upper().strip().startswith('SELECT'):
                if self.executemanythread.results[0].status == "OK":
                    return True
        except:
            return False

    def postexecutemany(self):
        print "postexecutemany"
        self.unlocktab()
        self.table.resizeColumnsToContents()

        if self.is_singleselect():
            self.postexecute()


    def executetofile(self, path):
        try:
            self.query = self.connection.cursor.execute(self.editor.getsql())
            o = open(path, "w", 5000)

            if self.query:
                # HEADER
                bazz = u";".join([i[0] for i in self.query.description])
                o.write(bazz.encode('UTF-8') + u";\n")

                for row in self.query:
                    #print row
                    line = u"%s;\n" % u";".join(map(unicode, row))
                    o.write(line.encode('UTF-8'))
            o.close()
        except Exception as exc:
                warningMessage("Error executing to file!", unicode(exc.args))

    def locktab(self):
        self.connection.setDisabled(True)
        palette = QtGui.QPalette()


        brush = QtGui.QBrush(QtGui.QColor("#E3F6CE"))
        brush.setStyle(QtCore.Qt.SolidPattern)

        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        self.table.setPalette(palette)
        #self.connTab.seticon("files/icons/DeletedIcon.ico")


    def postexecute(self):
        self.query = self.executemanythread.results[0].query
        self.columnsLen = len(self.query.description)
        # print types
        for i in self.query.description:
            print "%s: '%s'" % (i[0], i[1])
        # New model
        self.model = QtGui.QStandardItemModel(0, self.columnsLen)
        # Header
        for index, column in enumerate(self.query.description):
            self.model.setHeaderData(index, QtCore.Qt.Horizontal, column[0], role=0)

        self.fetchednum = 0
        self.fetchto = 0
        self.fetchedall = False

        self.table.setModel(self.model)
        self.fetchMore()

    def unlocktab(self):

        self.connection.setDisabled(False)
        self.editor.setFocus()


    def maybefetchmore(self, value):
        if self.fetchedall == False:
            vertical = self.table.verticalScrollBar()
            if vertical.value() +  vertical.pageStep() > vertical.maximum() and vertical.maximum() != 0:
                self.fetchMore()

    def fetchMore(self):
        self.fetchto += 256
        self.model.insertRows(self.fetchednum, 256, QtCore.QModelIndex())

        # PYODBC
        for row in self.query:
            for j in xrange(self.columnsLen):
                self.model.setData(self.model.index(self.fetchednum, j, QtCore.QModelIndex()), convertforQt(row[j]), role=0)
                if isnumber(row[j]):
                    self.model.setData(self.model.index(self.fetchednum, j, QtCore.QModelIndex()), QtCore.QVariant(QtCore.Qt.AlignRight + QtCore.Qt.AlignVCenter) , QtCore.Qt.TextAlignmentRole)

            self.fetchednum += 1

            if self.fetchednum >= self.fetchto:
                break
        else:
            self.fetchedall = True

        self.model.removeRows(self.fetchednum, self.model.rowCount() - (self.fetchednum), QtCore.QModelIndex())
        self.table.resizeColumnsToContents()

        self.connection.showtooltip("Rows: %s" % self.model.rowCount())

class Editor(Qsci.QsciScintilla):
    """
        Class thats add extra functions to the Qt Scintilla implementation.
         - some extra fuctions to make editing easier
         - some user friendly functionalyt: comment, join split lines, ctrl+whell mouse zoom
         - we set autocomplete from templates and tables names
    """
    def __init__(self, parent=None):
        pass

    def getselection(self, linefrom, indexfrom, lineto, indexto):
        cursorPosition = self.getCursorPosition()

        self.setSelection(linefrom, indexfrom, lineto, indexto)
        text = unicode(self.selectedText())

        self.setCursorPosition(*cursorPosition)

        return text

    def formatsql(self):
        if self.hasSelectedText():
            sql = sqlparse.format(self.findselection(), reindent=True, keyword_case='upper')
            self.replace(sql)


    def getsql(self):
        if self.hasSelectedText():
            sql = self.selectedText()
        else:
            sql = self.text()

        return unicode(sql).strip()

    def getparsedsql(self):
        return [i.strip() for i in sqlparse.split(self.getsql()) if i != '']

    def setautocomplete(self, tables=[]):
        for i in tables:
            self.api.add(i[2])

class Table:
    """  QTableView with default settings and copytoclipbord function """
    def __init__(self, parent=None):
        pass

    def convertstring(self, s):
        return s.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")

    def copytoclipbord(self):
        pass

class QueryResult:
    """
        This class saves one query result, status, sql, time and possible errors
    """
    def __init__(self, query, status, sql="", rows=-1, starttime=datetime.now(), endtime=datetime.now(), error=""):
        self.query = query
        self.status = status
        self.rows = rows

        self.starttime = starttime
        self.endtime = endtime
        self.error = error
        self.sql = sql

    def gettime(self):
        self.executiontime = self.endtime - self.starttime
        return "%s.%s" % (self.executiontime.seconds, int(self.executiontime.microseconds / 100))

    def toarray(self):
        """ function to print the query result in the gui table with printMessage """
        return (self.status, self.rows, self.starttime.strftime('%H:%M:%S'), self.gettime(), self.error, self.sql)

class ExecuteManyThread(QtCore.QThread):
    """ runs a thread with multiple sql statements and stores the results in
        a list of QueryResults.
        - each time a sql is executed it emits a 'executed' signal that
          print the currently executed statements.
        - when all the sql statements are executed a 'finished' signal tells
          the gui to unlock the gui.

        We dont call the printMessage directly cuz of Qt limitation of
        creating childs in another thread.
        Signals are the adviced approch to work around this limitation.
    """
    def __init__(self, parent=None):
       QtCore.QThread.__init__(self, parent)
       self.script = parent
       self.results = []
       self.alive = 1

    def run(self):
        self.sqlparsed = self.script.editor.getparsedsql()

        for sql in self.sqlparsed:
            if self.alive == 1:
                try:
                    startime = datetime.now()
                    query = self.script.connection.cursor.execute(sql)
                    result = QueryResult(query, "OK", sql, query.rowcount, startime, datetime.now())
                    self.results.append(result)

                except Exception as exc:
                    result = QueryResult(None, "ERROR", sql, -1, startime, datetime.now(), str(exc))
                    self.results.append(result)
                finally:
                    self.emit(QtCore.SIGNAL('executed'))
            else:
                break

        self.emit(QtCore.SIGNAL('finished'))

    def stop(self):
       self.alive = 0
#SDBE = Sdbe()
