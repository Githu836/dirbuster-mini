#!/usr/bin/env python3
"""
DirBuster Mini v1.0 - Advanced Incremental Directory Brute-forcer
Author: Faqih
License: MIT
"""

import argparse
import requests
import sys
import time
import threading
import json
import random
import os
from queue import Queue
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style, init
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# ASCII Banner
BANNER = f"""{Fore.CYAN}
  ____  _ _____   ____        _             __  __ _           _ 
 |  _ \(_) __\ \ / / |_ _   _| |_ ___  _ __|  \/  (_)_ __   __| |
 | | | | |__ \\ V /| __| | | | __/ _ \| '__| |\/| | | '_ \ / _` |
 | |_| | |__) | | | |_| |_| | || (_) | |  | |  | | | | | | (_| |
 |____/|_|___/ |_|  \__|\__,_|\__\___/|_|  |_|  |_|_|_| |_|\__,_|
 {Fore.YELLOW}Mini Directory Brute-forcer v2.0
 {Fore.GREEN}By: Faqih
{Style.RESET_ALL}
"""

class DirBusterMini:
    def __init__(self, target, wordlist, threads=10, delay=0, output=None, 
                 verbose=False, extensions=None, status_codes=None, 
                 user_agents=None, timeout=10, resume=False, no_color=False):
        self.target = target if target.startswith('http') else f'http://{target}'
        self.wordlist = wordlist
        self.threads = threads
        self.delay = delay
        self.output = output
        self.verbose = verbose
        self.extensions = extensions or []
        self.status_codes = status_codes or [200, 301, 302, 307, 308, 403, 401]
        self.user_agents = user_agents or [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'DirBusterMini/2.0'
        ]
        self.timeout = timeout
        self.resume = resume
        self.no_color = no_color
        
        self.found_paths = []
        self.queue = Queue()
        self.session = requests.Session()
        self.scan_start_time = None
        self.scan_end_time = None
        self.tested_paths = 0
        self.progress_file = "scan_progress.json"
        
        # Load templates if available
        self.templates = self.load_templates()
        
    def print_banner(self):
        """Print the ASCII banner"""
        print(BANNER)
        
    def load_templates(self):
        """Load detection templates from templates directory"""
        templates = {}
        templates_dir = "templates"
        
        if os.path.exists(templates_dir) and os.path.isdir(templates_dir):
            for filename in os.listdir(templates_dir):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(templates_dir, filename), 'r') as f:
                            template = json.load(f)
                            templates[template['id']] = template
                    except (json.JSONDecodeError, KeyError):
                        pass
        return templates
    
    def load_wordlist(self):
        """Load wordlist from file"""
        try:
            with open(self.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                words = [line.strip() for line in f if line.strip()]
            return words
        except FileNotFoundError:
            self.print_error(f"Wordlist file not found: {self.wordlist}")
            sys.exit(1)
    
    def load_progress(self):
        """Load progress from previous scan if resume is enabled"""
        if self.resume and os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    return progress.get('tested_paths', [])
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []
    
    def save_progress(self, tested_paths):
        """Save progress to file"""
        if self.resume:
            progress = {
                'target': self.target,
                'tested_paths': tested_paths,
                'timestamp': datetime.now().isoformat()
            }
            try:
                with open(self.progress_file, 'w') as f:
                    json.dump(progress, f)
            except IOError:
                self.print_error("Could not save progress file")
    
    def print_error(self, message):
        """Print error message"""
        if self.no_color:
            print(f"[ERROR] {message}")
        else:
            print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")
    
    def print_warning(self, message):
        """Print warning message"""
        if self.no_color:
            print(f"[WARN] {message}")
        else:
            print(f"{Fore.YELLOW}[WARN] {message}{Style.RESET_ALL}")
    
    def print_success(self, message):
        """Print success message"""
        if self.no_color:
            print(f"[SUCCESS] {message}")
        else:
            print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")
    
    def print_info(self, message):
        """Print info message"""
        if self.no_color:
            print(f"[INFO] {message}")
        else:
            print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")
    
    def check_url(self, url):
        """Check if a URL exists with random User-Agent"""
        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        
        try:
            response = self.session.get(
                url, 
                timeout=self.timeout, 
                allow_redirects=False,
                headers=headers
            )
            return response.status_code, response.headers, len(response.content)
        except requests.RequestException as e:
            if self.verbose:
                self.print_error(f"Request failed for {url}: {str(e)}")
            return None, None, None
    
    def match_template(self, url, status_code, headers, content_length):
        """Check if response matches any template"""
        for template_id, template in self.templates.items():
            # Check status code match
            if status_code in template.get('status_codes', []):
                return template
            
            # Check header matches
            for header_name, header_value in template.get('headers', {}).items():
                if header_name in headers and header_value in headers[header_name]:
                    return template
            
            # Check content length
            if 'content_length' in template and content_length == template['content_length']:
                return template
        
        return None
    
    def worker(self):
        """Worker thread to process URLs"""
        tested_paths = []
        
        while not self.queue.empty():
            path = self.queue.get()
            full_url = urljoin(self.target, path)
            
            status_code, headers, content_length = self.check_url(full_url)
            self.tested_paths += 1
            
            if status_code and status_code in self.status_codes:
                # Check if it matches any template
                template = self.match_template(full_url, status_code, headers, content_length)
                
                if status_code == 200:
                    color = Fore.GREEN
                    status_label = "FOUND"
                elif status_code in [301, 302, 307, 308]:
                    color = Fore.BLUE
                    status_label = "REDIRECT"
                elif status_code == 403:
                    color = Fore.YELLOW
                    status_label = "FORBIDDEN"
                elif status_code == 401:
                    color = Fore.MAGENTA
                    status_label = "UNAUTHORIZED"
                else:
                    color = Fore.CYAN
                    status_label = "OTHER"
                
                # Add template info if matched
                template_info = ""
                if template:
                    template_info = f" [{Fore.WHITE}{template['name']}{color}]"
                    status_label = "TEMPLATE"
                
                message = f"{color}[{status_label}] {status_code} {full_url}{template_info}{Style.RESET_ALL}"
                print(message)
                
                result = {
                    'url': full_url,
                    'status': status_code,
                    'content_length': content_length,
                    'template': template['id'] if template else None
                }
                
                self.found_paths.append(result)
                tested_paths.append(path)
            
            # Save progress periodically
            if self.tested_paths % 100 == 0:
                self.save_progress(tested_paths)
            
            if self.delay > 0:
                time.sleep(self.delay)
            
            self.queue.task_done()
        
        # Final progress save
        self.save_progress(tested_paths)
    
    def generate_incremental_paths(self, base_path, depth=2):
        """Generate incremental paths by combining words from wordlist"""
        words = self.load_wordlist()
        incremental_paths = []
        previously_tested = self.load_progress() if self.resume else []
        
        # Add single words
        for word in words:
            path = word
            if path not in previously_tested:
                incremental_paths.append(path)
            
            # Add with extensions
            for ext in self.extensions:
                path_with_ext = f"{word}.{ext}"
                if path_with_ext not in previously_tested:
                    incremental_paths.append(path_with_ext)
        
        # Generate combinations for deeper levels
        if depth > 1:
            for word1 in words:
                for word2 in words:
                    path = f"{word1}/{word2}"
                    if path not in previously_tested:
                        incremental_paths.append(path)
                    
                    # Add with extensions
                    for ext in self.extensions:
                        path_with_ext = f"{word1}/{word2}.{ext}"
                        if path_with_ext not in previously_tested:
                            incremental_paths.append(path_with_ext)
        
        if depth > 2:
            for word1 in words:
                for word2 in words:
                    for word3 in words:
                        path = f"{word1}/{word2}/{word3}"
                        if path not in previously_tested:
                            incremental_paths.append(path)
                        
                        # Add with extensions
                        for ext in self.extensions:
                            path_with_ext = f"{word1}/{word2}/{word3}.{ext}"
                            if path_with_ext not in previously_tested:
                                incremental_paths.append(path_with_ext)
        
        return incremental_paths
    
    def save_results(self):
        """Save results to output file"""
        if not self.output:
            return
        
        output_format = os.path.splitext(self.output)[1].lower()
        
        try:
            if output_format == '.json':
                with open(self.output, 'w') as f:
                    json.dump({
                        'target': self.target,
                        'start_time': self.scan_start_time.isoformat(),
                        'end_time': self.scan_end_time.isoformat(),
                        'duration_seconds': (self.scan_end_time - self.scan_start_time).total_seconds(),
                        'total_tested': self.tested_paths,
                        'total_found': len(self.found_paths),
                        'results': self.found_paths
                    }, f, indent=2)
            
            elif output_format == '.html':
                with open(self.output, 'w') as f:
                    f.write(self.generate_html_report())
            
            else:  # Default to text
                with open(self.output, 'w') as f:
                    f.write(f"DirBuster Mini Scan Report\n")
                    f.write(f"Target: {self.target}\n")
                    f.write(f"Start Time: {self.scan_start_time}\n")
                    f.write(f"End Time: {self.scan_end_time}\n")
                    f.write(f"Duration: {(self.scan_end_time - self.scan_start_time).total_seconds():.2f} seconds\n")
                    f.write(f"Total Tested: {self.tested_paths}\n")
                    f.write(f"Total Found: {len(self.found_paths)}\n\n")
                    
                    for result in self.found_paths:
                        f.write(f"[{result['status']}] {result['url']}\n")
            
            self.print_success(f"Results saved to: {self.output}")
        except IOError:
            self.print_error(f"Could not save results to: {self.output}")
    
    def generate_html_report(self):
        """Generate HTML report"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DirBuster Mini Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; }}
        .summary {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .result {{ padding: 10px; border-bottom: 1px solid #eee; }}
        .found {{ background-color: #d4edda; }}
        .redirect {{ background-color: #cce5ff; }}
        .forbidden {{ background-color: #fff3cd; }}
        .unauthorized {{ background-color: #f8d7da; }}
        .status {{ font-weight: bold; padding: 3px 8px; border-radius: 3px; display: inline-block; margin-right: 10px; }}
        .code-200 {{ background: #28a745; color: white; }}
        .code-30x {{ background: #007bff; color: white; }}
        .code-401 {{ background: #6f42c1; color: white; }}
        .code-403 {{ background: #ffc107; color: black; }}
        .code-other {{ background: #17a2b8; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>DirBuster Mini Scan Report</h1>
        
        <div class="summary">
            <h2>Scan Summary</h2>
            <p><strong>Target:</strong> {self.target}</p>
            <p><strong>Start Time:</strong> {self.scan_start_time}</p>
            <p><strong>End Time:</strong> {self.scan_end_time}</p>
            <p><strong>Duration:</strong> {(self.scan_end_time - self.scan_start_time).total_seconds():.2f} seconds</p>
            <p><strong>Total Tested:</strong> {self.tested_paths}</p>
            <p><strong>Total Found:</strong> {len(self.found_paths)}</p>
        </div>
        
        <h2>Results</h2>
        <div class="results">
            {"".join([self._generate_result_html(result) for result in self.found_paths])}
        </div>
    </div>
</body>
</html>"""
    
    def _generate_result_html(self, result):
        """Generate HTML for a single result"""
        status_class = ""
        if result['status'] == 200:
            status_class = "code-200"
        elif result['status'] in [301, 302, 307, 308]:
            status_class = "code-30x"
        elif result['status'] == 401:
            status_class = "code-401"
        elif result['status'] == 403:
            status_class = "code-403"
        else:
            status_class = "code-other"
        
        return f"""
        <div class="result">
            <span class="status {status_class}">{result['status']}</span>
            <a href="{result['url']}" target="_blank">{result['url']}</a>
            {f'<br><small>Template: {result["template"]}</small>' if result['template'] else ''}
        </div>
        """
    
    def run(self):
        """Run the directory brute-force attack"""
        self.print_banner()
        self.print_info(f"Starting DirBuster Mini v2.0 against {self.target}")
        self.print_info(f"Using wordlist: {self.wordlist}")
        self.print_info(f"Threads: {self.threads}, Delay: {self.delay}s")
        
        if self.extensions:
            self.print_info(f"Extensions: {', '.join(self.extensions)}")
        
        self.print_info("Generating incremental paths...")
        
        # Generate incremental paths
        paths = self.generate_incremental_paths("", depth=2)
        
        # Add paths to queue
        for path in paths:
            self.queue.put(path)
        
        self.print_info(f"Generated {len(paths)} paths to test")
        
        if self.resume and self.load_progress():
            self.print_info("Resuming from previous scan")
        
        self.print_info("Starting attack... Press Ctrl+C to stop\n")
        
        # Record start time
        self.scan_start_time = datetime.now()
        
        # Start worker threads
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        try:
            # Monitor progress
            while any(t.is_alive() for t in threads):
                time.sleep(1)
                if self.verbose:
                    print(f"\rTested: {self.tested_paths} | Found: {len(self.found_paths)} | Queue: {self.queue.qsize()}", end='')
            
            self.queue.join()
            
        except KeyboardInterrupt:
            self.print_info("\nInterrupted by user. Stopping...")
        
        # Record end time
        self.scan_end_time = datetime.now()
        
        # Print summary
        duration = (self.scan_end_time - self.scan_start_time).total_seconds()
        self.print_info(f"Scan completed in {duration:.2f} seconds")
        self.print_info(f"Tested {self.tested_paths} paths, found {len(self.found_paths)} accessible resources")
        
        # Save results if output file specified
        if self.output:
            self.save_results()
        
        # Clean up progress file if scan completed
        if self.resume and os.path.exists(self.progress_file):
            os.remove(self.progress_file)

def main():
    parser = argparse.ArgumentParser(description="DirBuster Mini v2.0 - Advanced Incremental Directory Brute-forcer")
    parser.add_argument("target", help="Target URL (e.g., http://example.com)")
    parser.add_argument("-w", "--wordlist", default="wordlists/common.txt", 
                        help="Path to wordlist file (default: wordlists/common.txt)")
    parser.add_argument("-t", "--threads", type=int, default=10,
                        help="Number of threads (default: 10)")
    parser.add_argument("-d", "--delay", type=float, default=0,
                        help="Delay between requests in seconds (default: 0)")
    parser.add_argument("-o", "--output", help="Output file to save results (supports .txt, .json, .html)")
    parser.add_argument("-e", "--extensions", nargs="+", help="File extensions to test (e.g., php txt html)")
    parser.add_argument("-s", "--status-codes", nargs="+", type=int, 
                        help="Status codes to report (default: 200 301 302 307 308 403 401)")
    parser.add_argument("-T", "--timeout", type=int, default=10,
                        help="Request timeout in seconds (default: 10)")
    parser.add_argument("-r", "--resume", action="store_true",
                        help="Resume previous scan")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable colored output")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Create dirbuster instance and run
    dirbuster = DirBusterMini(
        target=args.target,
        wordlist=args.wordlist,
        threads=args.threads,
        delay=args.delay,
        output=args.output,
        verbose=args.verbose,
        extensions=args.extensions,
        status_codes=args.status_codes,
        timeout=args.timeout,
        resume=args.resume,
        no_color=args.no_color
    )
    
    dirbuster.run()

if __name__ == "__main__":
    main()