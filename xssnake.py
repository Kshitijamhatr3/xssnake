import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode
from colorama import Fore, Style, init
import time

# Initialize colorama
init(autoreset=True)

# Function to print the custom banner
def print_custom_banner():
    banner = f"""
{Fore.BLUE}@@@  @@@   @@@@@@    @@@@@@   @@@  @@@   @@@@@@   @@@  @@@  @@@@@@@@  {Fore.RESET}
{Fore.BLUE}@@@  @@@  @@@@@@@   @@@@@@@   @@@@ @@@  @@@@@@@@  @@@  @@@  @@@@@@@@  {Fore.RESET}
{Fore.CYAN}@@!  !@@  !@@       !@@       @@!@!@@@  @@!  @@@  @@!  !@@  @@!       {Fore.RESET}
{Fore.CYAN}!@!  @!!  !@!       !@!       !@!!@!@!  !@!  @!@  !@!  @!!  !@!       {Fore.RESET}
{Fore.BLUE} !@@!@!   !!@@!!    !!@@!!    @!@ !!@!  @!@!@!@!  @!@@!@!   @!!!:!    {Fore.RESET}
{Fore.BLUE}  @!!!     !!@!!!    !!@!!!   !@!  !!!  !!!@!!!!  !!@!!!    !!!!!:    {Fore.RESET}
{Fore.CYAN} !: :!!        !:!       !:!  !!:  !!!  !!:  !!!  !!: :!!   !!:       {Fore.RESET}
{Fore.CYAN}:!:  !:!      !:!       !:!   :!:  !:!  :!:  !:!  :!:  !:!  :!:       {Fore.RESET}
{Fore.BLUE} ::  :::  :::: ::   :::: ::    ::   ::  ::   :::   ::  :::   :: ::::  {Fore.RESET}
{Fore.BLUE} :   ::   :: : :    :: : :    ::    :    :   : :   :   :::  : :: ::   {Fore.RESET}
                                                                      
{Fore.CYAN}Powered by Sukshield{Style.RESET_ALL}
{Fore.CYAN}Website: https://sukshield.com/{Style.RESET_ALL}\n
"""
    print(banner)

# Function to read payloads from a file
def read_payloads(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

# Function to scan for XSS vulnerabilities on given parameters
def scan_xss(url, params, target_params, payloads):
    success_color = Fore.GREEN
    failure_color = Fore.RED

    success_count = 0
    failure_count = 0
    error_count = 0
    results = []

    for payload in payloads:
        for target_param in target_params:
            # Inject the payload into the parameters
            injected_params = {k: (payload if k == target_param else v) for k, v in params.items()}
            # Encode the parameters into a query string
            query_string = urlencode(injected_params)
            target_url = f"{url}?{query_string}"
            print(f"Testing payload: {payload} on parameter: {target_param} - {target_url}")

            try:
                response = requests.get(target_url)

                # Check for reflected XSS
                if payload in response.text:
                    result = f"{success_color}Success:{Style.RESET_ALL} Possible reflected XSS vulnerability found with payload: {payload} in parameter: {target_param}"
                    success_count += 1
                else:
                    result = f"{failure_color}Failure:{Style.RESET_ALL} No reflected XSS found with payload: {payload} in parameter: {target_param}"
                    failure_count += 1
                results.append(result)

                # Check for stored XSS by submitting the form
                form_response = requests.post(url, data=injected_params)
                if payload in form_response.text:
                    result = f"{success_color}Success:{Style.RESET_ALL} Possible stored XSS vulnerability found with payload: {payload} in parameter: {target_param}"
                    success_count += 1
                else:
                    result = f"{failure_color}Failure:{Style.RESET_ALL} No stored XSS found with payload: {payload} in parameter: {target_param}"
                    failure_count += 1
                results.append(result)

            except requests.RequestException as e:
                error_message = f"{Fore.YELLOW}Error:{Style.RESET_ALL} Request error occurred: {e}"
                results.append(error_message)
                error_count += 1

    return results, success_count, failure_count, error_count

if __name__ == "__main__":
    # Display custom banner with footer
    print_custom_banner()

    try:
        # Prompt user for target URL
        target_url = input("Enter the target URL: ").strip()

        # Prompt user for payload file path
        payload_file_path = input("Enter the full path to the payload file (including the file name): ").strip()

        # Read payloads from the text file
        xss_payloads = read_payloads(payload_file_path)

        # Fetch the page content
        response = requests.get(target_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all forms and their parameters
        forms = soup.find_all('form')
        if not forms:
            print("No forms found on the page.")
        else:
            for form_index, form in enumerate(forms, start=1):
                action = form.get('action')
                full_url = urljoin(target_url, action)
                inputs = form.find_all('input')
                params = {input_element.get('name'): input_element.get('value') or '' for input_element in inputs if input_element.get('name')}
                if params:
                    print(f"\nForm {form_index} at {full_url} with parameters:")
                    for param_index, param_name in enumerate(params.keys(), start=1):
                        print(f"  {param_index}. {param_name}")

                    # Prompt user to select parameters to test
                    selected_params = []
                    while True:
                        try:
                            param_input = input("Enter parameter number(s) to test (comma-separated): ")
                            param_indices = map(int, param_input.split(','))
                            selected_params = [list(params.keys())[idx - 1] for idx in param_indices]
                            break
                        except (ValueError, IndexError) as e:
                            print(f"Error: Invalid input. Please try again.")

                    # Scan XSS on selected parameters
                    results, success_count, failure_count, error_count = scan_xss(full_url, params, selected_params, xss_payloads)
                    print(f"\nResults for Form {form_index} at {full_url}, Parameters: {', '.join(selected_params)}:")
                    for result in results:
                        print(result)

                    # Print summary below the results
                    print("\nScan Results Summary:")
                    print(f"{Fore.GREEN}Successes:{Style.RESET_ALL} {success_count}")
                    print(f"{Fore.RED}Failures:{Style.RESET_ALL} {failure_count}")
                    print(f"{Fore.YELLOW}Errors:{Style.RESET_ALL} {error_count}")

    except requests.RequestException as e:
        print(f"{Fore.YELLOW}Error:{Style.RESET_ALL} Failed to fetch {target_url}: {e}")
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}\nScan stopped by user{Style.RESET_ALL}")
