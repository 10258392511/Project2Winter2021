#################################
##### Name: Zhexin Wu
##### Uniqname: zhexinwu
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        """
        Provides a string representation of the object.

        Parameters
        ----------
        None

        Returns
        -------
        str
            <name> (<category>): <address> <zip>
        """
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    out_dict = {}
    base_url = "https://www.nps.gov"
    main_url = "/index.htm"
    unique_key = base_url + main_url
    if unique_key in CACHE_DICT:
        print("Using cache")
        return CACHE_DICT[unique_key]

    print("Fetching")
    resp = requests.get(base_url + main_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    li_tags = soup.find("ul", class_="dropdown-menu SearchBar-keywordSearch").find_all("li")
    for li_tag in li_tags:
        anchor = li_tag.find("a")
        ref = base_url + anchor["href"]
        out_dict[anchor.text.lower()] = ref

    CACHE_DICT[unique_key] = out_dict
    save_cache(CACHE_DICT, CACHE_FILENAME)

    return out_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    if site_url in CACHE_DICT:
        print("Using cache")
        json_dict = CACHE_DICT[site_url]
        return NationalSite(**json_dict)

    print("Fetching")
    resp = requests.get(site_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    # print(soup)
    try:
        name = soup.find("a", class_="Hero-title").text.strip()
    except Exception:
        name = "No Name"
    try:
        cate = soup.find("span", class_="Hero-designation").text.strip()
    except Exception:
        cate = "No Category"
    try:
        zip_code = soup.find("span", attrs={"itemprop": "postalCode", "class": "postal-code"}).text.strip()
    except Exception:
        zip_code = "No Zipcode"
    try:
        phone = soup.find("span", attrs={"itemprop": "telephone", "class": "tel"}).text.strip()
    except Exception:
        phone = "No Phone"
    try:
        city = soup.find("span", attrs={"itemprop": "addressLocality"}).text.strip()
        state = soup.find("span", attrs={"itemprop": "addressRegion", "class": "region"}).text.strip()
        address = f"{city}, {state}"
    except Exception:
        address = "No Address"

    CACHE_DICT[site_url] = {"category": cate, "name": name, "address": address, "zipcode": zip_code, "phone": phone}
    save_cache(CACHE_DICT, CACHE_FILENAME)

    return NationalSite(cate, name, address, zip_code, phone)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    sites = []
    if state_url in CACHE_DICT:
        print("Using cache")
        links = CACHE_DICT[state_url]

    else:
        print("Fetching")
        base_url = "https://www.nps.gov"
        resp = requests.get(state_url)
        state_soup = BeautifulSoup(resp.text, "html.parser")
        anchors = state_soup.select("ul li h3 a")
        links = []
        for anchor in anchors:
            park_url = base_url + anchor["href"]
            links.append(park_url)
        CACHE_DICT[state_url] = links

    for park_url in links:
        sites.append(get_site_instance(park_url))

    return sites


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    endpoint = "http://www.mapquestapi.com/search/v2/radius"
    params = {"key": secrets.API_KEY,
              "origin": site_object.zipcode,
              "radius": 10,
              "maxMatches": 10,
              "ambiguities": "ignore",
              "outFormat": "json"}
    unique_key = construct_unique_key(endpoint, params)
    if unique_key in CACHE_DICT:
        print("Using cache")
        out_dict = CACHE_DICT[unique_key]
        # print(out_dict)
        return out_dict
    else:
        print("Fetching")
        resp = requests.get(endpoint, params=params)
        if resp.status_code != 200:
            raise Exception("Access Failed!")
        CACHE_DICT[unique_key] = resp.json()
        save_cache(CACHE_DICT, CACHE_FILENAME)
        # print(CACHE_DICT[unique_key])
        return CACHE_DICT[unique_key]


def construct_unique_key(base_url, params, connector="_"):
    """
    Create a unique key for a query.

    Parameters
    ----------
    base_url: str
        API endpoint.
    params: dict
        Query parameters.
    connector: str
        Connecting symbol to string "base_url" and "params".

    Returns
    -------
    str
        The unique key as a str.
    """
    out_key = base_url
    for key in params:
        out_key += connector + f"{key}{connector}{params[key]}"

    return out_key


def open_cache(filename):
    """
    Open or create a cache.json file.

    Parameters
    ----------
    filename: str
        Path to the cache.json file.

    Returns
    -------
    dict
        Loaded or created cache as a dictionary.
    """
    try:
        with open(filename, "r") as rf:
            cache_dict = json.loads(rf.read())
        # print("Using cache")
        return cache_dict
    except FileNotFoundError:
        with open(filename, "w") as wf:
            pass
        # print("Fetching")
        return {}


def save_cache(cache_dict, filename):
    """
    Save the current cache dict to "filename".

    Parameters
    ----------
    cache_dict: dict
        The current cache dict.
    filename: str
        Cache file path.

    Returns
    -------
    None
    """
    with open(filename, "w") as wf:
        wf.write(json.dumps(cache_dict))


def process_part_4(result_dict):
    """
    Helper function for part 4. Extract relevant info and print it.

    Parameters
    ----------
    result_dict: dict
        The raw search result as a json dict.

    Returns
    -------
    None
    """
    json_dicts = result_dict["searchResults"]
    # extracted_dicts = []
    for json_dict in json_dicts:
        extracted_dict = dict()
        extracted_dict["name"] = json_dict.get("name", "no name")
        if "group_sic_code_name" in json_dict["fields"]:
            extracted_dict["category"] = json_dict["fields"]["group_sic_code_name"]
        elif "group_sic_code_name_ext" in json_dict["fields"]:
            extracted_dict["category"] = json_dict["fields"]["group_sic_code_name_ext"]
        else:
            extracted_dict["category"] = "no category"
        extracted_dict["address"] = json_dict.get("address", "no address")
        extracted_dict["city"] = json_dict["fields"].get("city", "no city")

        for key in extracted_dict:
            if extracted_dict[key] == "":
                extracted_dict[key] = f"no {key}"

        print(f"- {extracted_dict['name']} ({extracted_dict['category']}): {extracted_dict['address']}, " +
              f"{extracted_dict['city']}")


CACHE_FILENAME = "cache.json"
CACHE_DICT = open_cache(CACHE_FILENAME)


if __name__ == "__main__":
    # # a test for missing info
    # park_url = "https://www.nps.gov/yose/index.htm"
    # site = get_site_instance(park_url)
    # print(site.info())

    # # part 3
    # # CACHE_FILENAME = "cache.json"
    # # CACHE_DICT = open_cache(CACHE_FILENAME)
    # state_url_dict = build_state_url_dict()
    #
    # while True:
    #     user_input = input("Enter a state name (e.g. Michigan, michigan) or \"exit\": ")
    #     if user_input == "exit":
    #         break
    #
    #     state_url = state_url_dict[user_input.lower()]
    #     title = f"List of national sites in {user_input}"
    #     sites = get_sites_for_state(state_url)
    #     print("-" * len(title))
    #     print(title)
    #     print("-" * len(title))
    #     for i, site in enumerate(sites):
    #         print(f"[{i + 1}] {site.info()}")

    # # part 4: a test
    # site_mi = get_site_instance('https://www.nps.gov/slbe/index.htm')
    # nearby_mi = get_nearby_places(site_mi)
    # process_part_4(nearby_mi)

    # part 5: the main control logic
    state_url_dict = build_state_url_dict()

    while True:
        user_input = input("Enter a state name (e.g. Michigan, michigan) or \"exit\": ")
        if user_input == "exit":
            break

        # step 1 & 2
        state_key = user_input.lower()
        if state_key not in state_url_dict:
            print("[Error] Enter a proper state name")
            print()
            continue

        state_url = state_url_dict[state_key]
        title = f"List of national sites in {user_input}"
        sites = get_sites_for_state(state_url)
        print("-" * len(title))
        print(title)
        print("-" * len(title))
        for i, site in enumerate(sites):
            print(f"[{i + 1}] {site.info()}")

        # step 3 & 4
        while True:
            user_input = input("Choose the number for detail search or \"exit\" or \"back\": ")
            if user_input in ["exit", "back"]:
                break

            if not user_input.isnumeric():
                print("[Error] Invalid input")
                print("-" * 40)
                continue

            number = int(user_input)
            if number > len(sites) or number <= 0:
                print("[Error] Invalid input")
                print("-" * 40)
                continue

            index = number - 1
            nearby_places = get_nearby_places(sites[index])
            title = f"Places near {sites[index].name}"
            print("-" * len(title))
            print(title)
            print("-" * len(title))
            process_part_4(nearby_places)

        if user_input == "back":
            continue

        if user_input == "exit":
            break

    print()
    print("Bye!")
