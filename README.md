Unpack the Online Documentation
-------------------------------

  	cd SEN2THREE/distributions/v1.1.0
  	unzip sen2three-1.0.0.htmldoc.zip
  	cd sen2three-1.0.0.htmldoc/html
  open index.html with a web browser
    
Install Sen2Three Runtime
-------------------------

  open index.html and read Section 1.3 Installation and Setup
  of the Software Installation and Users Manual

Building Sen2Three Distribution Package
----------------------------------------

	cd SEN2THREE/sources
  	python setup.py sdist --formats=gztar,zip
  creates the distribution packages under sources/dist

Building Sen2Three HTML Help
----------------------------

	cd SEN2THREE/documentation
  	make html
  creates HTML pages under build/html

