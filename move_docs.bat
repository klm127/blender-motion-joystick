rmdir docs
cd sphinx-documentation
call make.bat html
cd ..
Xcopy /E /I sphinx-documentation\build\html .\docs /y
rmdir /Q /S sphinx-documentation\build