This is a website with intentional security flaws for the cybersecurity course. 

https://owasp.org/Top10/A01_2021-Broken_Access_Control/



You might want to set up a virtual environment

Depending on your python installation, you might have to use 
"python3" instead of "python" in the commands
In the root directory:
$ python -m venv venv
$ source venv/bin/activate

Once you're done with everything, just run
$ deactivate

Installing the requirements

$ pip install -r requirements.txt

Running the main app. For some of the flaws, you'll have to change this as specified in the instructions.

$ uvicorn main:app --reload