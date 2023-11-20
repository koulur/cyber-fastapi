This is a website with intentional security flaws for the cybersecurity course. 

https://owasp.org/Top10/A01_2021-Broken_Access_Control/



You might want to set up a virtual environment

Slight warning. You might have problems, particularly installing the cryptography package. In case you're on a Mac and using the system python, it probably has to do with openssl. You can either 
1. Use homebrew to install python and use that python - problem most likely solved
2. Google it - sorry :(
3. Comment out the package from requirements.txt. There's not much going on in this flaw, so you don't really have to run it. Here's a link to known security vulnerabilities: https://osv.dev/list?ecosystem=PyPI&q=cryptography

Depending on your python installation, you might have to use 
"python3" instead of "python" in the commands
In the root directory:
$ python -m venv venv
$ source venv/bin/activate

Once you're done with everything, just run
$ deactivate

Installing the requirements

$ pip install -r requirements.txt
or
$ python -m pip install -r requirements.txt
or
$ python3 -m pip install -r requirements.txt

Running the main app. For some of the flaws, you'll have to change this as specified in the instructions.

$ uvicorn main:app --reload
or
$ python -m uvicorn main:app --reload
or
$ python3 -m uvicorn main:app --reload