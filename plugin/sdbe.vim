" sdbe.vim -- Simple database explorer for vim
" @Author       : Dusan Smitran (dusan.smitran [at] gmail.com)
" @License      : AGPL3 (see http://www.gnu.org/licenses/agpl.txt)
" @Created      : 2012-04-10
" @Last Modified: 2012-04-11
" @Revision     : 0.0.1

if ! has('python') || v:version < 703
	echoerr "Unable to start sdbe. Sdbe depends on Vim >= 7.3 with Python support complied in."
	finish
endif

" load plugin just once
if &cp || exists("g:sdbe_loaded")
    finish
endif
let g:sdbe_loaded= 1

" Public interface. {{{
fun! s:SdbeStart()
    let g:csv_delim='×'
python << EOF
import vim, os, sys

for p in vim.eval("&runtimepath").split(','):
	dname = os.path.join(p, "plugin")
	if os.path.exists(os.path.join(dname, "sdbe")):
		if dname not in sys.path:
			sys.path.append(dname)
			break

from sdbe import Sdbe
SDBE = Sdbe()
EOF

    let g:sdbe_started = 1
endfun

fun! s:ExecuteSql()
    if !exists("g:sdbe_started")
        call s:SdbeStart()
    endif
    "echo("SdbeExecuteSql started.")
    python SDBE.connection.executesql('SELECT RSS_ID, LINK, DATE_CREATED FROM RSS')
    "echo("SdbeExecuteSql executed.")
endfun

" Expose the functions publicly.
command! -nargs=0 SdbeStart call s:SdbeStart()
command! -nargs=0 SdbeExecuteSql call s:ExecuteSql()
