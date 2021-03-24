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
    pass


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
        out_key =+ connector + f"{key}{connector}{params[key]}"

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


if __name__ == "__main__":
    # # a test for missing info
    # park_url = "https://www.nps.gov/yose/index.htm"
    # site = get_site_instance(park_url)
    # print(site.info())

    # part 3
    CACHE_FILENAME = "cache.json"
    CACHE_DICT = open_cache(CACHE_FILENAME)
    state_url_dict = build_state_url_dict()

    while True:
        user_input = input("Enter a state name (e.g. Michigan, michigan) or \"exit\": ")
        if user_input == "exit":
            break

        state_url = state_url_dict[user_input.lower()]
        title = f"List of national sites in {user_input}"
        sites = get_sites_for_state(state_url)
        print("-" * len(title))
        print(title)
        print("-" * len(title))
        for i, site in enumerate(sites):
            print(f"[{i + 1}] {site.info()}")
