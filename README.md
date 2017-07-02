Unpack the Online Documentation
-------------------------------

  	cd SEN2THREE/distributions/v1.1.0
  	unzip sen2three-1.0.0.htmldoc.zip
  	cd sen2three-1.0.0.htmldoc/html
  open index.html with a web browser
    
Install Sen2Three Runtime
-------------------------

  read the file installation.md 

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

Recent Issue with Anaconda
--------------------------
There is currently a bug in the libxml2 library version 2.9.4 installed by Anaconda
2.4.0 which is used in the SentThree's L3_XmlParser.py module for reading
and validating XML config L3_GIPP.xml. Even though the XML files are
correct, they are not properly validated as such by the XML parser due to
this bug. Details are described here:
https://bugzilla.gnome.org/show_bug.cgi?id=766834

If yiu are confronted with an error like:
	Syntax error in metadata, see report file for details.
	Parsing error:
	Schema file: L3_GIPP.xsd
	Details: Element 'PSD_Scheme', attribute 'PSD_Version': [facet 'length'] The value '' has a length of '0'; this 	differs from the allowed length of '2'.
	
The solution is to downgrade the libxml2 library to the version 2.9.2
which is not affected by the bug. This is done by the following command:

	conda install libxml2=2.9.2
