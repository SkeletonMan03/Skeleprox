# Skeleprox
This is a simple HTTP, HTTPS, and SOCKS5 proxy checker that should just work.  
It just runs through a list of proxies you provide of a specified type and checks its IP address, if it gets a response with the correct IP address, it's valid.  

## How to use:
0) `git clone https://github.com/SkeletonMan03/Skeleprox.git`
1) `python3 -m venv venv`
2) `source venv/bin/activate`
3) `pip3 install -r requirements.txt`
4) `python3 main.py -p <infile.txt> -t <Proxy type (http or socks5)> -o <outfile.txt> -n <number of processes>`

## Known issues
I'm not entirely sure why, probably because I chose to try multiprocessing instead of threading, sometimes it never finishes running through the list of proxies.  
