#!/usr/bin/env python3
"""
DirBuster Mini - Incremental Directory Brute-forcer
Author: Githu836
License: MIT
"""

import argparse
import requests
import sys
import time
import threading
from queue import Queue
from urllib.parse import urljoin
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class DirBusterMini:
    def __init__(self, target, wordlist, threads=10, delay=0, output=None, verbose=False):
        self.target = target if target.startswith('http') else f'http://{target}'
        self.wordlist = wordlist
        self.threads = threads
        self.delay = delay
        self.output = output
        self.verbose = verbose
        self.found_paths = []
        self.queue = Queue()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DirBusterMini/1.0'
        })
        
    def load_wordlist(self):
        """Load wordlist from file"""
        try:
            with open(self.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                words = [line.strip() for line in f if line.strip()]
            return words
        except FileNotFoundError:
            print(f"{Fore.RED}[ERROR] Wordlist file not found: {self.wordlist}")
            sys.exit(1)
    
    def check_url(self, url):
        """Check if a URL exists"""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=False)
            return response.status_code
        except requests.RequestException:
            return None
    
    def worker(self):
        """Worker thread to process URLs"""
        while not self.queue.empty():
            path = self.queue.get()
            url = urljoin(self.target, path)
            
            status = self.check_url(url)
            if status:
                if status == 200:
                    color = Fore.GREEN
                elif status in [301, 302, 307, 308]:
                    color = Fore.BLUE
                elif status == 403:
                    color = Fore.YELLOW
                elif status == 401:
                    color = Fore.MAGENTA
                else:
                    color = Fore.CYAN
                
                message = f"{color}[{status}] {url}{Style.RESET_ALL}"
                print(message)
                
                if self.output:
                    self.found_paths.append(f"[{status}] {url}")
            
            if self.delay > 0:
                time.sleep(self.delay)
            
            self.queue.task_done()
    
    def generate_incremental_paths(self, base_path, depth=2):
        """Generate incremental paths by combining words from wordlist"""
        words = self.load_wordlist()
        incremental_paths = []
        
        # Add single words
        incremental_paths.extend(words)
        
        # Generate combinations for deeper levels
        if depth > 1:
            for word1 in words:
                for word2 in words:
                    incremental_paths.append(f"{word1}/{word2}")
        
        if depth > 2:
            for word1 in words:
                for word2 in words:
                    for word3 in words:
                        incremental_paths.append(f"{word1}/{word2}/{word3}")
        
        return incremental_paths
    
    def run(self):
        """Run the directory brute-force attack"""
        print(f"{Fore.YELLOW}[INFO] Starting DirBuster Mini against {self.target}")
        print(f"{Fore.YELLOW}[INFO] Using wordlist: {self.wordlist}")
        print(f"{Fore.YELLOW}[INFO] Threads: {self.threads}, Delay: {self.delay}s")
        print(f"{Fore.YELLOW}[INFO] Generating incremental paths...")
        
        # Generate incremental paths
        paths = self.generate_incremental_paths("", depth=2)
        
        # Add paths to queue
        for path in paths:
            self.queue.put(path)
        
        print(f"{Fore.YELLOW}[INFO] Generated {len(paths)} paths to test")
        print(f"{Fore.YELLOW}[INFO] Starting attack... Press Ctrl+C to stop\n")
        
        # Start worker threads
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
        
        try:
            self.queue.join()
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}[INFO] Interrupted by user. Stopping...")
        
        # Save results if output file specified
        if self.output and self.found_paths:
            with open(self.output, 'w') as f:
                f.write("\n".join(self.found_paths))
            print(f"{Fore.YELLOW}[INFO] Results saved to: {self.output}")
        
        print(f"{Fore.YELLOW}[INFO] Scan completed. Found {len(self.found_paths)} paths.")

def main():
    parser = argparse.ArgumentParser(description="DirBuster Mini - Incremental Directory Brute-forcer")
    parser.add_argument("target", help="Target URL (e.g., http://example.com)")
    parser.add_argument("-w", "--wordlist", default="wordlists/common.txt", 
                        help="Path to wordlist file (default: wordlists/common.txt)")
    parser.add_argument("-t", "--threads", type=int, default=10,
                        help="Number of threads (default: 10)")
    parser.add_argument("-d", "--delay", type=float, default=0,
                        help="Delay between requests in seconds (default: 0)")
    parser.add_argument("-o", "--output", help="Output file to save results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Create dirbuster instance and run
    dirbuster = DirBusterMini(
        target=args.target,
        wordlist=args.wordlist,
        threads=args.threads,
        delay=args.delay,
        output=args.output,
        verbose=args.verbose
    )
    
    dirbuster.run()

if __name__ == "__main__":
    main()
