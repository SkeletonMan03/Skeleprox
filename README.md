# Skeleprox
This is a simple HTTP, HTTPS, and SOCKS5 proxy checker that should just work.  
It just runs through a list of proxies you provide of a specified type and checks its IP address, if it gets a response with the correct IP address, it's valid.  

## How to use:
0) `git clone https://github.com/SkeletonMan03/Skeleprox.git`
1) `cd Skeleprox` 
2) `python3 -m venv venv`
3) `source venv/bin/activate`
4) `pip3 install -r requirements.txt`
5) `python3 main.py -p <infile.txt> -t <Proxy type (http or socks5)> -o <outfile.txt> -n <number of workers>`

`-n` controls bounded worker threads. The checker reuses one HTTP session per
worker and writes the output once after all checks finish. Use `--timeout` to
override the five-second per-request timeout.

## Known issues
The checker uses threads rather than one process per chunk, which avoids the
old multiprocessing hang and reduces process and connection setup overhead.
