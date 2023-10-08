
# Overview
This is a lightweight script based OSINT tool that searches for a username across a list of websites. It supports threading
to help reduce the runtime of requests significantly. This is my first real open source project. I have made 
an effort to make this script easy to understand and easily extendable. Additions to the siteList.json file are 
very appreciated. Please, feel free to submit MRs and help me create a more robust tool. Obviously, I don't assume any
responsibility for the misuse of this tool.

# Installation
Installs the requirements for the script.

    git clone https://github.com/devinogle/behold.git && cd behold/ && sudo pip3 install -r requirements.txt && cd src && python3 behold.py -- h  

# Options
```
  --username USERNAME   (str): The username to search for.
  --nsfw NSFW           (true/false): Include NSFW websites in search.
  --output_filepath OUTPUT_FILEPATH
                        (str): The filepath to save the results of the search as csv.
  --threads THREADS     (int): Number of threads to run for threading. Defaults to 1.
```

# Tested OS:
<table>
    <tr>
        <th>Operative system</th>
        <th> Version </th>
    </tr>
    <tr>
        <td>MacOS</td>
        <td> Sonoma 14.0 </td>
    </tr>
</table>